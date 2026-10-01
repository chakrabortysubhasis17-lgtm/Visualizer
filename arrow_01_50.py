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
START_CHAPTER = 1
END_CHAPTER = 50
START_CHAPTER_URL = "https://mtl-novel.com/novel/one-evolution-point-per-second-i-slay-gods-with-a-single-arrow/chapter-1-professional-awakening/"

NOVEL_SLUG = "one-evolution-point-per-second-i-slay-gods-with-a-single-arrow"

NOVEL_TITLE_DISPLAY = [
    "1 FREE POINT PER SECOND",
    "F-RANK ARCHER SLAYS GODS",
    "Chapters 01 – 50 [Full Marathon]"
]

# ==================== 12-ROLE ACOUSTIC ROSTER ====================
# Format: (VoiceName, PitchModifier, RateModifier)
VOICE_MAP = {
    # 1. Progression Exposition & Divine Notifications
    "narrator":              ("en-US-ChristopherNeural", "-4Hz",  "+11%"),
    "system":                ("en-US-SteffanNeural",     "-20Hz", "-6%"),

    # 2. Protagonist & Allies
    "ye_chen":               ("en-US-AndrewNeural",      "+0Hz",  "+12%"),
    "fang_xue":              ("en-US-JennyNeural",       "+2Hz",  "+9%"),
    "support_girl":          ("en-US-EmmaNeural",        "+4Hz",  "+10%"),
    "female_officer":        ("en-US-AriaNeural",        "+0Hz",  "+11%"),

    # 3. Antagonists & Clan Forces
    "arrogant_scion":        ("en-US-EricNeural",        "+6Hz",  "+14%"),
    "capital_young_master":  ("en-US-TonyNeural",        "+4Hz",  "+12%"),
    "old_patriarch":         ("en-US-DavisNeural",       "-12Hz", "-2%"),
    "shadow_assassin":       ("en-US-BrianNeural",       "-10Hz", "+2%"),

    # 4. Military & World Bosses
    "military_general":      ("en-US-RogerNeural",       "-6Hz",  "+4%"),
    "abyssal_boss":          ("en-US-DavisNeural",       "-25Hz", "-10%")
}

# ==================== OUTPUT PATHS & PERFORMANCE ====================
BUILD_DIR = "build_arrow_01_50"
FINAL_AUDIO = "output_arrow_01_50.mp3"
TIMESTAMPS_FILE = "youtube_timestamps_arrow_01_50.txt"
SUBTITLES_FILE = "subtitles_arrow_01_50.srt"
FINAL_VIDEO = "final_arrow_01_50.mp4"
COVER_IMAGE = "cover_arrow_01_50.jpg"

MAX_CONCURRENT_TTS = 12  # Optimal parallel WebSocket connections
TARGET_CHUNK_WORDS = 65  # Pacing threshold for subtitles & TTS stability

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# ==================== COMPILED REGEX PATTERNS ====================
RE_SYSTEM = re.compile(
    r"\[(Ding!|System Prompt|Evolution Point|Acquired|Unlocked|Upgraded|Host|Congratulations|Skill).*?\]",
    re.IGNORECASE
)

SPEAKER_PATTERNS = [
    (re.compile(r"\b(Ye Chen said|Ye Chen replied|Ye Chen smiled|Ye Chen asked|thought Ye Chen|Ye Chen thought)\b", re.I), "ye_chen"),
    (re.compile(r"\b(Fang Xue|Miss Fang|Xue'er)\b", re.I), "fang_xue"),
    (re.compile(r"\b(nurse|healer|medic|junior sister|girl whimpered|she cried)\b", re.I), "support_girl"),
    (re.compile(r"\b(senior sister|female officer|Captain Lin|instructor|Dean Tang)\b", re.I), "female_officer"),
    (re.compile(r"\b(Wang Teng|Chu Tian|young master Wang|sneered Wang|barked Chu)\b", re.I), "arrogant_scion"),
    (re.compile(r"\b(young master|Holy Son|Nangong|prodigy scoffed|imperial student)\b", re.I), "capital_young_master"),
    (re.compile(r"\b(Patriarch|Elder Wang|Wang Zhen|Old Ancestor|Grandmaster)\b", re.I), "old_patriarch"),
    (re.compile(r"\b(Commander|General Zhou|Fortress Lord|Adjutant|Chief Examiner)\b", re.I), "military_general"),
    (re.compile(r"\b(assassin|Shadow Pavilion|man in black|cultist|traitor whispered)\b", re.I), "shadow_assassin"),
    (re.compile(r"\b(Demon General|Abyssal King|Beast Monarch|Demigod|Overlord roared)\b", re.I), "abyssal_boss")
]

WATERMARK_PATTERNS = [
    re.compile(r"\(End of this chapter\)", re.I),
    re.compile(r"Please visit mtl-novel\.com.*", re.I),
    re.compile(r"Check out our latest novel.*", re.I),
    re.compile(r"\[TL Note:.*?\]", re.I),
    re.compile(r"https?://\S+", re.I),
]

FULLWIDTH_TO_ASCII = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'", '「': '"', '」': '"', '『': '"', '』': '"',
    '，': ', ', '。': '. ', '！': '! ', '？': '? ', '：': ': ', '；': '; ', '（': '(', '）': ')'
})

RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')
RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

os.makedirs(BUILD_DIR, exist_ok=True)


# ==================== TEXT NORMALIZATION ====================
def clean_and_normalize_text(text: str) -> str:
    cleaned = text.translate(FULLWIDTH_TO_ASCII)
    for pat in WATERMARK_PATTERNS:
        cleaned = pat.sub("", cleaned)

    # Phonetic expansion for LitRPG stat displays
    cleaned = re.sub(r"\bLv\.?\s*(\d+)", r"Level \1", cleaned, flags=re.I)
    cleaned = re.sub(r"\bHP\b", "Health Points", cleaned)
    cleaned = re.sub(r"\bMP\b", "Mana Points", cleaned)
    cleaned = re.sub(r"\bF-rank\b", "F rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSSS-rank\b", "Triple S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSS-rank\b", "Double S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bS-rank\b", "S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSTR\b", "Strength", cleaned)
    cleaned = re.sub(r"\bAGI\b", "Agility", cleaned)
    cleaned = re.sub(r"\bINT\b", "Intelligence", cleaned)
    
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


# ==================== CELESTIAL GOLD & OBSIDIAN COVER ====================
def generate_cover_image(lines: list, output_path: str = COVER_IMAGE):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return

    width, height = 1920, 1080
    base = Image.new("RGBA", (width, height), (10, 8, 14, 255))

    # Radiant Solar Core Glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cx, cy = width // 2, int(height * 0.48)
    for r in range(650, 0, -25):
        alpha = int(40 * (1 - (r / 650)))
        glow_draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(180, 130, 30, alpha))
    base = Image.alpha_composite(base, glow)

    # 45-Degree Glass Lustre Beam
    sheen = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen)
    sheen_draw.polygon([
        (int(width * 0.32), 0),
        (int(width * 0.50), 0),
        (int(width * 0.18), height),
        (int(width * 0.00), height)
    ], fill=(255, 255, 255, 14))
    base = Image.alpha_composite(base, sheen)

    draw = ImageDraw.Draw(base)

    # Double Border
    draw.rectangle([(50, 50), (width - 50, height - 50)], outline=(45, 35, 20, 255), width=2)
    draw.rectangle([(64, 64), (width - 64, height - 64)], outline=(140, 105, 40, 180), width=1)

    # Tactical HUD Corner Brackets
    c = 36
    corners = [
        ((64, 64), (64 + c, 64), (64, 64 + c)),
        ((width - 64, 64), (width - 64 - c, 64), (width - 64, 64 + c)),
        ((64, height - 64), (64 + c, height - 64), (64, height - 64 - c)),
        ((width - 64, height - 64), (width - 64 - c, height - 64), (width - 64, height - 64 - c))
    ]
    for orig, h_pt, v_pt in corners:
        draw.line([orig, h_pt], fill=(240, 195, 75, 255), width=3)
        draw.line([orig, v_pt], fill=(240, 195, 75, 255), width=3)

    # Typography
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
                font = ImageFont.truetype(fp, 56)
                sub_font = ImageFont.truetype(fp, 40)
                break
            except Exception:
                pass

    if not font:
        font = ImageFont.load_default()
        sub_font = font

    line_spacing = 95
    total_text_height = (len(lines) - 1) * line_spacing + 50
    start_y = (height - total_text_height) // 2

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else font
        bbox = draw.textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)

        # 4px Drop Shadow
        draw.text((x + 4, y + 4), line, fill=(0, 0, 0, 220), font=active_font)
        fill_color = (230, 210, 160) if i == len(lines) - 1 else (255, 250, 240)
        draw.text((x, y), line, fill=fill_color, font=active_font)

    base.convert("RGB").save(output_path, "JPEG", quality=98)
    print(f"[Cover Generator] Created 1080p Celestial Gold Cover: '{output_path}'")


# ==================== SCRAPING PIPELINE ====================
def scrape_chapter_content(session: requests.Session, url: str):
    resp = session.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "Untitled Chapter"

    article = soup.find("article")
    if not article:
        raise ValueError(f"Could not locate <article> element at: {url}")

    paragraphs = [clean_and_normalize_text(p.get_text(strip=True)) for p in article.find_all("p")]
    paragraphs = [p for p in paragraphs if p and RE_ALPHANUM.search(p)]
    full_text = f"{title}.\n\n" + "\n\n".join(paragraphs)

    next_url = None
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True).lower()
        if "next" in t or "»" in t or "next chapter" in t:
            if NOVEL_SLUG in a["href"]:
                next_url = urllib.parse.urljoin(url, a["href"])
                break

    return title, full_text, next_url


# ==================== SCRIPT & DIALOGUE PARSER ====================
def parse_chapter_to_segments(text: str) -> list:
    parts = text.split('"')
    raw_segments = []

    for i, raw_chunk in enumerate(parts):
        chunk = raw_chunk.strip()
        if not chunk or not RE_ALPHANUM.search(chunk):
            continue

        if i % 2 == 0:
            # Narrative segment or System Announcement
            if RE_SYSTEM.search(chunk):
                role = "system"
            else:
                role = "narrator"
            raw_segments.append({"role": role, "text": chunk})
        else:
            # Spoken Dialogue Segment
            prev_context = parts[i - 1][-120:].lower() if i > 0 else ""
            next_context = parts[i + 1][:120].lower() if i + 1 < len(parts) else ""
            surrounding = prev_context + " " + next_context

            assigned_role = None
            for pattern, r in SPEAKER_PATTERNS:
                if pattern.search(surrounding):
                    assigned_role = r
                    break

            if not assigned_role:
                if any(w in surrounding for w in ["i said", "i replied", "ye chen", "i muttered"]):
                    assigned_role = "ye_chen"
                elif any(w in surrounding for w in ["she said", "she whispered", "miss fang"]):
                    assigned_role = "fang_xue"
                elif any(w in surrounding for w in ["roared", "shouted", "bastard", "courting death"]):
                    assigned_role = "arrogant_scion"
                else:
                    assigned_role = "ye_chen"

            raw_segments.append({"role": assigned_role, "text": chunk})

    # Balance into optimal chunks for Edge-TTS and Soft Subtitles
    balanced_segments = []
    for seg in raw_segments:
        words = seg["text"].split()
        if len(words) <= TARGET_CHUNK_WORDS:
            balanced_segments.append(seg)
            continue

        sentences = RE_SENTENCE_SPLIT.split(seg["text"])
        curr_words = []
        for s in sentences:
            s_words = s.split()
            if len(curr_words) + len(s_words) > TARGET_CHUNK_WORDS and curr_words:
                balanced_segments.append({"role": seg["role"], "text": " ".join(curr_words)})
                curr_words = s_words
            else:
                curr_words.extend(s_words)

        if curr_words:
            balanced_segments.append({"role": seg["role"], "text": " ".join(curr_words)})

    return balanced_segments


# ==================== PARALLEL AUDIO SYNTHESIS ====================
async def synthesize_chunk(text: str, role: str, output_path: str, sem: asyncio.Semaphore, max_retries: int = 3):
    voice_name, pitch_mod, rate_mod = VOICE_MAP.get(role, VOICE_MAP["narrator"])

    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                comm = edge_tts.Communicate(text, voice_name, pitch=pitch_mod, rate=rate_mod)
                await comm.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return
            except Exception:
                if attempt == max_retries:
                    # Fallback silent snippet to prevent FFmpeg pipeline crashes
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                        "-t", "0.2", "-q:a", "9", "-acodec", "libmp3lame", output_path
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                await asyncio.sleep(attempt * 0.4)


def get_audio_duration(file_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 0.2


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


async def build_chapter_audio(segments: list, output_mp3: str, chapter_start_offset: float):
    temp_dir = os.path.join(BUILD_DIR, "temp_chunks")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files = []
    tasks = []

    sem = asyncio.Semaphore(MAX_CONCURRENT_TTS)

    for i, seg in enumerate(segments):
        chunk_path = os.path.join(temp_dir, f"seg_{i:04d}.mp3")
        chunk_files.append(chunk_path)
        tasks.append(synthesize_chunk(seg["text"], seg["role"], chunk_path, sem))

    await asyncio.gather(*tasks)

    # Stitch chapter audio & compute accurate millisecond subtitle entries
    manifest_path = os.path.join(temp_dir, "manifest.txt")
    valid_chunks = [cf for cf in chunk_files if os.path.exists(cf) and os.path.getsize(cf) > 0]
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        for cf in valid_chunks:
            safe = os.path.abspath(cf).replace(os.sep, "/")
            f.write(f"file '{safe}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", manifest_path, "-c", "copy", output_mp3
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    srt_entries = []
    curr_time = chapter_start_offset
    for cf, seg in zip(valid_chunks, segments):
        dur = get_audio_duration(cf)
        start_srt = format_srt_time(curr_time)
        end_srt = format_srt_time(curr_time + dur)
        srt_entries.append((start_srt, end_srt, seg["text"]))
        curr_time += dur

    # Cleanup temp segments
    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    try: os.remove(manifest_path)
    except OSError: pass

    chapter_duration = curr_time - chapter_start_offset
    return chapter_duration, srt_entries


# ==================== MAIN COMPILATION ENGINE ====================
async def main():
    print(f"=== Starting Production: One Evolution Point Per Second (Ch. {START_CHAPTER} to {END_CHAPTER}) ===")
    print("[*] Engine: 12-Role Acoustic Matrix (12 Parallel Workers) | Approach B (Soft Subtitles)")
    
    generate_cover_image(NOVEL_TITLE_DISPLAY, COVER_IMAGE)

    chapter_files = []
    timestamps = []
    all_subtitles = []
    current_time_offset = 0.0

    with requests.Session() as session:
        current_url = START_CHAPTER_URL

        for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
            if not current_url:
                print(f"[Warning] No URL found for chapter {ch_num}. Halting scrape.")
                break

            print(f"\n[Chapter {ch_num:02d}/{END_CHAPTER}] Crawling: {current_url}")
            title, text, next_url = scrape_chapter_content(session, current_url)

            chapter_mp3 = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}.mp3")
            chapter_meta = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}_meta.json")

            # Resuming check
            if os.path.exists(chapter_mp3) and os.path.exists(chapter_meta):
                with open(chapter_meta, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                dur = meta["duration"]
                timestamps.append(f"{format_timestamp(current_time_offset)} - {title}")
                for s, e, txt in meta["subtitles"]:
                    all_subtitles.append((s, e, txt))
                current_time_offset += dur
                chapter_files.append(chapter_mp3)
                print(f"  [Cached] Reusing Chapter {ch_num:02d} ({format_timestamp(dur)})")
                current_url = next_url
                continue

            segments = parse_chapter_to_segments(text)
            print(f"  -> Synthesizing {len(segments)} segments in parallel...")
            dur, srt_entries = await build_chapter_audio(segments, chapter_mp3, current_time_offset)

            # Cache chapter metadata
            with open(chapter_meta, "w", encoding="utf-8") as f:
                json.dump({"title": title, "duration": dur, "subtitles": srt_entries}, f)

            timestamps.append(f"{format_timestamp(current_time_offset)} - {title}")
            for entry in srt_entries:
                all_subtitles.append(entry)

            current_time_offset += dur
            chapter_files.append(chapter_mp3)
            print(f"  -> Generated '{title}' ({format_timestamp(dur)})")

            current_url = next_url

    # Export Timestamps
    with open(TIMESTAMPS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(timestamps))
    print(f"\n[Saved] YouTube timestamps written to: {TIMESTAMPS_FILE}")

    # Export Master Subtitles (.srt)
    with open(SUBTITLES_FILE, "w", encoding="utf-8") as f:
        for idx, (s_time, e_time, text) in enumerate(all_subtitles, 1):
            f.write(f"{idx}\n{s_time} --> {e_time}\n{text}\n\n")
    print(f"[Saved] Soft subtitles exported to: {SUBTITLES_FILE}")

    # Lossless Audio Concatenation
    master_manifest = os.path.join(BUILD_DIR, "master_list.txt")
    with open(master_manifest, "w", encoding="utf-8") as f:
        for cf in chapter_files:
            safe = os.path.abspath(cf).replace(os.sep, "/")
            f.write(f"file '{safe}'\n")

    print(f"\nMerging all chapters into: {FINAL_AUDIO}...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", master_manifest, "-c", "copy", FINAL_AUDIO
    ], check=True)

    print(f"Audio Complete: {FINAL_AUDIO} (Runtime: {format_timestamp(current_time_offset)})")

    # Ultra-Fast MP4 Video Export (Sub-30 seconds)
    print(f"\nRendering YouTube MP4 via 1-frame loop: {FINAL_VIDEO}...")
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "1",
        "-i", COVER_IMAGE, "-i", FINAL_AUDIO,
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
        "-c:a", "copy", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-shortest", FINAL_VIDEO
    ], check=True)

    print(f"\n[Done] Master Video Generated: {FINAL_VIDEO}")
    print(f"[Done] Soft Subtitles Ready for Upload: {SUBTITLES_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
