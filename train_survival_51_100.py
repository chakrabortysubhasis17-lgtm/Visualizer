import os
import re
import json
import asyncio
import subprocess
import urllib.parse
import requests
from bs4 import BeautifulSoup
import edge_tts
from PIL import Image, ImageDraw, ImageFont

# ==================== CONFIGURATION ====================
START_CHAPTER = 51
END_CHAPTER = 100
START_CHAPTER_URL = "https://mtl-novel.com/novel/the-class-is-trying-to-survive-on-a-train-im-the-only-boy-in-the-whole-class/chapter-51-level-3-zombie/"

NOVEL_TITLE_DISPLAY = [
    "THE CLASS IS TRYING TO SURVIVE ON A TRAIN",
    "I'M THE ONLY BOY IN THE WHOLE CLASS",
    "Chapters 51 – 100"
]

# ==================== 28-CHARACTER UNIFIED CAST ====================
# Format: (VoiceName, PitchModifier, RateModifier)
VOICE_MAP = {
    # 1. Lead Male & Homeroom Teacher
    "hero_narrator":      ("en-US-AndrewNeural",      "+0Hz",  "+14%"),
    "female_teacher":     ("en-US-MichelleNeural",    "+0Hz",  "+6%"),

    # 2. Automated Train Broadcast & Train Characters
    "train_system":       ("en-US-SteffanNeural",     "-20Hz", "-5%"),   # Cold PA broadcast / intercom
    "train_conductor":    ("en-US-BrianNeural",       "+0Hz",  "+0%"),   # Official train conductor
    "train_guard":        ("en-US-ChristopherNeural", "-10Hz", "+5%"),   # Gruff security guard
    "train_passenger":    ("en-US-GuyNeural",         "+0Hz",  "+8%"),   # Panicking older passenger

    # 3. The 22 Distinct American High School Girls
    "girl_01_strong":     ("en-US-AriaNeural",        "+0Hz",  "+12%"),  # Class rep / assertive
    "girl_02_gentle":     ("en-US-JennyNeural",       "+0Hz",  "+12%"),  # Natural girl-next-door
    "girl_03_bright":     ("en-US-AvaNeural",         "+0Hz",  "+12%"),  # High energy / panicked
    "girl_04_cool":       ("en-US-SaraNeural",        "+0Hz",  "+12%"),  # Calm / analytical / kuudere
    "girl_05_sweet":      ("en-US-EmmaNeural",        "+0Hz",  "+12%"),  # Soft / caring peacemaker
    "girl_06_petite":     ("en-US-AnaNeural",         "+0Hz",  "+12%"),  # Cute / youthful / younger
    "girl_07_feisty":     ("en-US-AmberNeural",       "+0Hz",  "+12%"),  # Sarcastic / sharp-tongued
    "girl_08_timid":      ("en-US-AshleyNeural",      "+0Hz",  "+12%"),  # Soft-spoken / fragile
    "girl_09_stoic":      ("en-US-CoraNeural",        "+0Hz",  "+12%"),  # Formal / bookish
    "girl_10_refined":    ("en-US-ElizabethNeural",   "+0Hz",  "+12%"),  # Poised ojou-sama
    "girl_11_tough":      ("en-US-MonicaNeural",      "+0Hz",  "+12%"),  # Athletic / tomboy
    "girl_12_talkative":  ("en-US-AmandaNeural",      "+0Hz",  "+14%"),  # Fast gossiper
    "girl_13_calm":       ("en-US-JaneNeural",        "+0Hz",  "+10%"),  # Mature / observant
    "girl_14_leader2":    ("en-US-AriaNeural",        "+15Hz", "+14%"),  # Sporty club vice-captain
    "girl_15_shy2":       ("en-US-JennyNeural",       "+20Hz", "+12%"),  # Squeaky / anxious whisperer
    "girl_16_dramatic":   ("en-US-AvaNeural",         "+15Hz", "+14%"),  # Overdramatic / screaming
    "girl_17_intellect":  ("en-US-SaraNeural",        "-12Hz", "+10%"),  # Deeper / deadpan tactician
    "girl_18_nurse":      ("en-US-EmmaNeural",        "+12Hz", "+10%"),  # First-aid caregiver
    "girl_19_rebel":      ("en-US-AmberNeural",       "-12Hz", "+12%"),  # Cynical delinquent
    "girl_20_crying":     ("en-US-AshleyNeural",      "+15Hz", "+10%"),  # Trembling / tearful
    "girl_21_proper":     ("en-US-CoraNeural",        "+12Hz", "+12%"),  # Student council secretary
    "girl_22_casual":     ("en-US-AmandaNeural",      "-15Hz", "+12%")   # Sarcastic back-row student
}

GIRL_ROTATION = [k for k in VOICE_MAP if k.startswith("girl_")]

LEGACY_ROLE_MIGRATION = {
    "female_teen_strong": "girl_01_strong",
    "female_teen_soft":   "girl_02_gentle",
    "female_teen_bright": "girl_03_bright",
    "female_teen_cool":   "girl_04_cool"
}

# ==================== OUTPUT ARTIFACTS ====================
BUILD_DIR = "build_train_survival_51_100"
NAME_MAP_FILE = "name_map_train_survival.json"  # Shared across all batches for voice continuity
FINAL_AUDIO = "output_train_survival_51_100.mp3"
TIMESTAMPS_FILE = "youtube_timestamps_train_51_100.txt"
FINAL_VIDEO = "final_video_train_51_100.mp4"
COVER_IMAGE = "cover_train_51_100.jpg"

MAX_CONCURRENT_TTS = 12  # Optimal parallel WebSocket downloads
TARGET_CHUNK_WORDS = 80  # Narration slicing threshold

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# ==================== PRE-COMPILED OPTIMIZATIONS ====================
QUOTE_TRANSLATION_TABLE = str.maketrans('“”「」『』', '""""""')
RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')
RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

os.makedirs(BUILD_DIR, exist_ok=True)


# ==================== AUTOMATIC COVER GENERATOR ====================
def generate_cover_image(lines: list, output_path: str = COVER_IMAGE):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return

    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), color=(8, 8, 12))
    draw = ImageDraw.Draw(img)

    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 52)
                sub_font = ImageFont.truetype(fp, 38)
                break
            except Exception:
                pass

    if not font:
        font = ImageFont.load_default()
        sub_font = font

    line_spacing = 90
    total_text_height = (len(lines) - 1) * line_spacing + 50
    start_y = (height - total_text_height) // 2

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else font
        bbox = draw.textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)

        fill_color = (180, 195, 215) if i == len(lines) - 1 else (255, 255, 255)
        draw.text((x, y), line, fill=fill_color, font=active_font)

    draw.rectangle([(60, 60), (width - 60, height - 60)], outline=(50, 55, 70), width=3)
    img.save(output_path, "JPEG", quality=95)
    print(f"[Cover Generator] Created 1080p cover: '{output_path}'")


# ==================== ROSTER & REGISTRY ====================
def load_name_map() -> dict:
    base_map = {
        "narrator": "hero_narrator",
        "protagonist": "hero_narrator",
        "teacher": "female_teacher",
        "sensei": "female_teacher"
    }
    if os.path.exists(NAME_MAP_FILE):
        try:
            with open(NAME_MAP_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            migrated = {}
            for k, v in saved.items():
                new_v = LEGACY_ROLE_MIGRATION.get(v, v)
                migrated[k] = new_v if new_v in VOICE_MAP else "girl_02_gentle"
            return {**base_map, **migrated}
        except Exception:
            pass
    return base_map


def save_name_map(mapping: dict):
    with open(NAME_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


# ==================== SCRAPING WITH CONNECTION POOLING ====================
def scrape_chapter_content(session: requests.Session, url: str):
    resp = session.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "Untitled Chapter"

    article = soup.find("article")
    if not article:
        raise ValueError(f"Could not find <article> content block at {url}")

    paragraphs = [p.get_text(strip=True) for p in article.find_all("p") if p.get_text(strip=True)]
    full_text = f"{title}.\n\n" + "\n\n".join(paragraphs)

    next_url = None
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True).lower()
        if "next" in t or "»" in t or "next chapter" in t:
            if "the-class-is-trying-to-survive-on-a-train" in a["href"]:
                next_url = urllib.parse.urljoin(url, a["href"])
                break

    return title, full_text, next_url


# ==================== CHUNK BALANCING ====================
def balance_segments_for_parallelism(segments: list, max_words: int = TARGET_CHUNK_WORDS) -> list:
    balanced = []
    for seg in segments:
        text = seg["text"].strip()
        words = text.split()

        if len(words) <= max_words or seg["role"] != "hero_narrator":
            balanced.append(seg)
            continue

        sentences = RE_SENTENCE_SPLIT.split(text)
        current_chunk = []
        current_count = 0

        for s in sentences:
            s_words = s.split()
            if current_count + len(s_words) > max_words and current_chunk:
                balanced.append({
                    "speaker": seg.get("speaker", "narrator"),
                    "role": seg["role"],
                    "text": " ".join(current_chunk)
                })
                current_chunk = [s]
                current_count = len(s_words)
            else:
                current_chunk.append(s)
                current_count += len(s_words)

        if current_chunk:
            balanced.append({
                "speaker": seg.get("speaker", "narrator"),
                "role": seg["role"],
                "text": " ".join(current_chunk)
            })

    return balanced


# ==================== UNIVERSAL DIALOGUE PARSER ====================
def classify_chapter_segments(chapter_text: str, current_map: dict) -> list:
    normalized = chapter_text.translate(QUOTE_TRANSLATION_TABLE)
    parts = normalized.split('"')
    segments = []
    rot_idx = 0
    stats = {k: 0 for k in VOICE_MAP}

    for i, raw_chunk in enumerate(parts):
        chunk = raw_chunk.strip()
        if not chunk or not RE_ALPHANUM.search(chunk):
            continue

        if i % 2 == 0:
            lower_chunk = chunk.lower()
            if any(w in lower_chunk for w in ["[announcement", "[broadcast", "[train system", "chime rings", "the speaker crackled"]):
                role = "train_system"
            else:
                role = "hero_narrator"

            stats[role] += 1
            segments.append({"speaker": "narrator", "role": role, "text": chunk})
        else:
            prev_context = parts[i - 1][-120:].lower() if i > 0 else ""
            next_context = parts[i + 1][:120].lower() if i + 1 < len(parts) else ""
            surrounding = prev_context + " " + next_context

            assigned_role = None

            # 1. Match known roster names
            for name, role in current_map.items():
                if name in surrounding:
                    assigned_role = role
                    break

            # 2. Match train entities and specific character tags
            if not assigned_role:
                if any(w in surrounding for w in ["speaker", "intercom", "broadcast", "pa system", "automated voice", "electronic chime"]):
                    assigned_role = "train_system"
                elif any(w in surrounding for w in ["conductor", "train master", "driver"]):
                    assigned_role = "train_conductor"
                elif any(w in surrounding for w in ["guard", "security", "officer"]):
                    assigned_role = "train_guard"
                elif any(w in surrounding for w in ["passenger", "old man", "stranger"]):
                    assigned_role = "train_passenger"
                elif any(w in surrounding for w in ["teacher", "sensei", "chaperone", "homeroom"]):
                    assigned_role = "female_teacher"
                elif any(w in surrounding for w in ["i said", "i replied", "i asked", "i muttered", "i shouted", "i thought"]):
                    assigned_role = "hero_narrator"
                elif any(w in surrounding for w in ["shouted", "yelled", "snapped", "demanded", "class rep", "president", "glared"]):
                    assigned_role = "girl_01_strong"
                elif any(w in surrounding for w in ["whimpered", "sobbed", "whispered", "nervous", "trembling", "crying"]):
                    assigned_role = "girl_20_crying"
                elif any(w in surrounding for w in ["calmly", "analyzed", "coolly", "quietly", "sighed"]):
                    assigned_role = "girl_04_cool"
                elif any(w in surrounding for w in ["scoffed", "sneered", "sarcastically", "barked"]):
                    assigned_role = "girl_07_feisty"

            # 3. Fallback: cycle across the 22-girl classroom rotation
            if not assigned_role:
                assigned_role = GIRL_ROTATION[rot_idx % len(GIRL_ROTATION)]
                rot_idx += 1

            assigned_role = LEGACY_ROLE_MIGRATION.get(assigned_role, assigned_role)
            if assigned_role not in VOICE_MAP:
                assigned_role = "girl_02_gentle"

            stats[assigned_role] += 1
            segments.append({"speaker": "character", "role": assigned_role, "text": chunk})

    active_cast = [f"{k}: {v}" for k, v in stats.items() if v > 0]
    print(f"  [Active Cast Breakdown] {' | '.join(active_cast[:8])}...")

    return balance_segments_for_parallelism(segments)


# ==================== PARALLEL SYNTHESIS WITH PITCH MOD ====================
async def synthesize_chunk(text: str, role: str, output_path: str, sem: asyncio.Semaphore, max_retries: int = 3):
    clean_text = text.strip()
    if not RE_ALPHANUM.search(clean_text):
        return

    safe_role = LEGACY_ROLE_MIGRATION.get(role, role)
    voice_name, pitch_mod, rate_mod = VOICE_MAP.get(safe_role, VOICE_MAP["hero_narrator"])

    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                comm = edge_tts.Communicate(clean_text, voice_name, pitch=pitch_mod, rate=rate_mod)
                await comm.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return
            except Exception:
                if attempt == max_retries:
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                        "-t", "0.2", "-q:a", "9", "-acodec", "libmp3lame", output_path
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                await asyncio.sleep(attempt * 0.3)


async def build_chapter_audio(segments: list, output_mp3: str):
    temp_dir = os.path.join(BUILD_DIR, "temp_chunks")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files = []
    tasks = []

    sem = asyncio.Semaphore(MAX_CONCURRENT_TTS)

    for i, seg in enumerate(segments):
        role = seg.get("role", "hero_narrator")
        chunk_path = os.path.join(temp_dir, f"seg_{i:04d}.mp3")
        chunk_files.append(chunk_path)
        tasks.append(synthesize_chunk(seg["text"], role, chunk_path, sem))

    await asyncio.gather(*tasks)

    valid_chunks = [f for f in chunk_files if os.path.exists(f) and os.path.getsize(f) > 0]

    manifest_path = os.path.join(temp_dir, "manifest.txt")
    manifest_lines = "".join(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n" for cf in valid_chunks)
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_lines)

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", manifest_path, "-c", "copy", output_mp3
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    try: os.remove(manifest_path)
    except OSError: pass


def get_audio_duration(file_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(res.stdout.strip())


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ==================== MAIN PIPELINE ====================
async def main():
    print(f"=== Starting Train Survival Audiobook: Chapters {START_CHAPTER} to {END_CHAPTER} ===")
    print("[*] Engine: High-Performance 28-Character Unified Cast (12 Parallel TTS Workers)")
    generate_cover_image(NOVEL_TITLE_DISPLAY, COVER_IMAGE)
    name_map = load_name_map()

    chapter_files = []
    timestamps = []
    current_time_offset = 0.0

    with requests.Session() as session:
        current_url = START_CHAPTER_URL

        for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
            if not current_url:
                print("No next chapter URL found. Ending loop.")
                break

            print(f"\n[Chapter {ch_num}/{END_CHAPTER}] Fetching: {current_url}")
            title, text, next_url = scrape_chapter_content(session, current_url)

            chapter_mp3 = os.path.join(BUILD_DIR, f"ch_{ch_num}.mp3")

            # Resume support: skip already synthesized chapters
            if os.path.exists(chapter_mp3) and os.path.getsize(chapter_mp3) > 1000:
                duration = get_audio_duration(chapter_mp3)
                ts = format_timestamp(current_time_offset)
                timestamps.append(f"{ts} - {title}")
                current_time_offset += duration
                chapter_files.append(chapter_mp3)
                print(f"  [Found Cached] Reusing {chapter_mp3} ({format_timestamp(duration)})")
                current_url = next_url
                continue

            print(f"  -> Parsing dialogue across 28 distinct character profiles...")
            segments = classify_chapter_segments(text, name_map)
            print(f"  -> Synthesizing {len(segments)} audio blocks in parallel (12 workers)...")
            await build_chapter_audio(segments, chapter_mp3)
            chapter_files.append(chapter_mp3)

            ts = format_timestamp(current_time_offset)
            timestamps.append(f"{ts} - {title}")
            duration = get_audio_duration(chapter_mp3)
            current_time_offset += duration
            print(f"  -> Completed: '{title}' ({format_timestamp(duration)})")

            current_url = next_url

    # Save Timestamps
    with open(TIMESTAMPS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(timestamps))
    print(f"\n[Saved] YouTube timestamps written to: {TIMESTAMPS_FILE}")

    # Lossless Audio Merge
    master_manifest = os.path.join(BUILD_DIR, "master_list.txt")
    with open(master_manifest, "w", encoding="utf-8") as f:
        for cf in chapter_files:
            safe = os.path.abspath(cf).replace(os.sep, "/")
            f.write(f"file '{safe}'\n")

    print(f"\nMerging all chapters ({START_CHAPTER}–{END_CHAPTER}) into: {FINAL_AUDIO}...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", master_manifest, "-c", "copy", FINAL_AUDIO
    ], check=True)

    print(f"Audio ready: {FINAL_AUDIO} (Runtime: {format_timestamp(current_time_offset)})")

    # Render YouTube MP4
    print(f"\nRendering YouTube MP4 using generated black title card: {FINAL_VIDEO}...")
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "1",
        "-i", COVER_IMAGE, "-i", FINAL_AUDIO,
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
        "-c:a", "copy", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-shortest", FINAL_VIDEO
    ], check=True)

    print(f"\n[Done] Video Ready for YouTube: {FINAL_VIDEO}")


if __name__ == "__main__":
    asyncio.run(main())
