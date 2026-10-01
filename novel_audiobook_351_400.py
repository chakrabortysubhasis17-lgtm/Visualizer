import os
import re
import json
import asyncio
import subprocess
import urllib.parse
import requests
from bs4 import BeautifulSoup
from groq import Groq
import edge_tts

# ==================== CONFIGURATION ====================
GROQ_API_KEY = "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"

START_CHAPTER = 351
END_CHAPTER = 400
NOVEL_TOC_URL = "https://mtl-novel.com/novel/all-gods-starting-with-sss-level-talent/"

VOICE_MAP = {
    "hero_narrator": "en-US-ChristopherNeural",  # Yang Fan + Narration
    "male_young":    "en-US-GuyNeural",          # Peers, disciples (Li Tianheng)
    "male_elder":    "en-US-EricNeural",         # Elders, clan masters, veteran gods
    "female_young":  "en-US-JennyNeural",        # Young maidens, junior sisters
    "female_elder":  "en-US-MichelleNeural"      # Mothers, matriarchs, senior aunts
}

BUILD_DIR = "build_351_400"
NAME_MAP_FILE = "name_map.json"
FINAL_AUDIO = "output_chapters_351_400.mp3"
TIMESTAMPS_FILE = "youtube_timestamps_351_400.txt"
FINAL_VIDEO = "final_video_351_400.mp4"
COVER_IMAGE = "cover.jpg"

MAX_CONCURRENT_TTS = 8   # Optimal parallel connections
TARGET_CHUNK_WORDS = 80  # Keeps all parallel workers evenly loaded

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

os.makedirs(BUILD_DIR, exist_ok=True)
groq_client = Groq(api_key=GROQ_API_KEY)


# ==================== ROSTER & REGISTRY ====================
def load_name_map() -> dict:
    if os.path.exists(NAME_MAP_FILE):
        with open(NAME_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "narrator": "hero_narrator",
        "yang fan": "hero_narrator",
        "li tianheng": "male_young"
    }


def save_name_map(mapping: dict):
    with open(NAME_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


# ==================== SCRAPING ====================
def find_chapter_url(chapter_num: int) -> str:
    print(f"Scanning Table of Contents for Chapter {chapter_num}...")
    resp = requests.get(NOVEL_TOC_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    target_pattern = re.compile(rf"/chapter-{chapter_num}[-/]", re.IGNORECASE)
    for a in soup.find_all("a", href=True):
        if target_pattern.search(a["href"]):
            return urllib.parse.urljoin(NOVEL_TOC_URL, a["href"])

    raise ValueError(f"Could not locate URL for Chapter {chapter_num} in Table of Contents.")


def scrape_chapter_content(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=20)
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
    for a in soup.select("nav a"):
        text = a.get_text(strip=True).lower()
        if "next" in text or "»" in text:
            next_url = urllib.parse.urljoin(url, a["href"])
            break

    return title, full_text, next_url


# ==================== BALANCED CHUNKING & CLASSIFICATION ====================
def balance_segments_for_parallelism(segments: list, max_words: int = TARGET_CHUNK_WORDS) -> list:
    balanced = []
    for seg in segments:
        text = seg["text"].strip()
        words = text.split()

        if len(words) <= max_words:
            balanced.append(seg)
            continue

        sentences = re.split(r'(?<=[.!?])\s+', text)
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


def heuristic_classify_segments(chapter_text: str, current_map: dict) -> list:
    segments = []
    lines = [l.strip() for l in chapter_text.split("\n") if l.strip()]
    last_speaker_role = "male_young"

    for line in lines:
        parts = re.split(r'["“]([^"”]+)["”]', line)
        for i, chunk in enumerate(parts):
            chunk = chunk.strip()
            if not re.search(r'[a-zA-Z0-9]', chunk):
                continue

            if i % 2 == 0:
                segments.append({"speaker": "narrator", "role": "hero_narrator", "text": chunk})
            else:
                lower_chunk = chunk.lower()
                context = line.lower()
                assigned_role = None

                for name, role in current_map.items():
                    if name in context:
                        assigned_role = role
                        break

                if not assigned_role:
                    if any(w in lower_chunk for w in ["brother yang", "bro", "adoptive father"]):
                        assigned_role = "male_young"
                    elif any(w in context for w in ["yang fan said", "yang fan smiled", "yang fan replied"]):
                        assigned_role = "hero_narrator"
                    elif any(w in context for w in ["elder", "ancestor", "father", "patriarch", "old man", "general"]):
                        assigned_role = "male_elder"
                    elif any(w in context for w in ["fairy", "sister", "maiden", "girl", "princess", "miss"]):
                        assigned_role = "female_young"
                    elif any(w in context for w in ["mother", "matriarch", "grandmother", "aunt"]):
                        assigned_role = "female_elder"
                    else:
                        assigned_role = "hero_narrator" if last_speaker_role != "hero_narrator" else "male_young"

                last_speaker_role = assigned_role
                segments.append({"speaker": "character", "role": assigned_role, "text": chunk})

    return balance_segments_for_parallelism(segments)


def classify_chapter_segments(chapter_text: str, current_map: dict) -> list:
    prompt = f"""
You are preparing a web novel chapter for a 5-role audiobook.
Protagonist / Lead: "Yang Fan"

KNOWN ROSTER:
{json.dumps(current_map, indent=2)}

Available Archetypes:
- "hero_narrator": Third-person narrative description, thoughts, or direct dialogue by Yang Fan.
- "male_young": Dialogue spoken by young men, peers, classmates, brothers, young disciples.
- "male_elder": Dialogue spoken by older men, fathers, grandfathers, elders, sect masters, ancient gods.
- "female_young": Dialogue spoken by young women, daughters, sisters, fairies, young goddesses.
- "female_elder": Dialogue spoken by mothers, grandmothers, matriarchs, elderly women, senior aunts.

Rules:
1. Break down the text chronologically into narration and dialogue chunks.
2. Identify the speaker name for each line.
3. If the character is already in KNOWN ROSTER, assign their established archetype.
4. If NEW, infer age and gender from context, titles (e.g. 'Elder', 'Fairy', 'Bro'), and honorifics.
5. In machine-translated text, pronouns are frequently mistranslated (e.g., calling female characters 'he'). Rely on contextual titles over pronouns.

Return strictly a valid JSON object matching:
{{
  "new_characters": {{ "character_name_lowercase": "assigned_archetype" }},
  "segments": [
    {{"speaker": "narrator", "role": "hero_narrator", "text": "Li Tianheng glanced at the sky."}},
    {{"speaker": "li tianheng", "role": "male_young", "text": "Brother Yang, what should we do?"}},
    {{"speaker": "yang fan", "role": "hero_narrator", "text": "Prepare the fortress."}}
  ]
}}

Chapter Text:
{chapter_text}
"""
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        content = completion.choices[0].message.content
        data = json.loads(content)

        new_chars = data.get("new_characters", {})
        if new_chars:
            for name, role in new_chars.items():
                clean = name.strip().lower()
                if clean not in current_map:
                    current_map[clean] = role
                    print(f"  [Roster Update] '{clean}' -> {role}")
            save_name_map(current_map)

        valid_segments = []
        for seg in data.get("segments", []):
            if re.search(r'[a-zA-Z0-9]', seg.get("text", "")):
                valid_segments.append(seg)

        return balance_segments_for_parallelism(valid_segments)

    except Exception as e:
        print(f"  [Groq Fallback] ({e}). Switching to Smart Local Engine...")
        return heuristic_classify_segments(chapter_text, current_map)


# ==================== PARALLEL AUDIO SYNTHESIS ====================
async def synthesize_chunk(text: str, voice: str, output_path: str, sem: asyncio.Semaphore, max_retries: int = 3):
    clean_text = text.strip()
    if not re.search(r'[a-zA-Z0-9]', clean_text):
        return

    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                comm = edge_tts.Communicate(clean_text, voice, rate="+15%")
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
                await asyncio.sleep(attempt * 0.4)


async def build_chapter_audio(segments: list, output_mp3: str):
    temp_dir = os.path.join(BUILD_DIR, "temp_chunks")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files = []
    tasks = []

    sem = asyncio.Semaphore(MAX_CONCURRENT_TTS)

    for i, seg in enumerate(segments):
        role = seg.get("role", "hero_narrator")
        voice = VOICE_MAP.get(role, VOICE_MAP["hero_narrator"])
        chunk_path = os.path.join(temp_dir, f"seg_{i:04d}.mp3")
        chunk_files.append(chunk_path)
        tasks.append(synthesize_chunk(seg["text"], voice, chunk_path, sem))

    await asyncio.gather(*tasks)

    valid_chunks = [f for f in chunk_files if os.path.exists(f) and os.path.getsize(f) > 0]

    manifest_path = os.path.join(temp_dir, "manifest.txt")
    with open(manifest_path, "w", encoding="utf-8") as f:
        for cf in valid_chunks:
            safe_path = os.path.abspath(cf).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", manifest_path, "-c", "copy", output_mp3
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    os.remove(manifest_path)


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
    print(f"=== Running Audiobook Pipeline: Chapters {START_CHAPTER} to {END_CHAPTER} ===")
    name_map = load_name_map()

    try:
        current_url = find_chapter_url(START_CHAPTER)
    except Exception as e:
        print(f"Auto-discovery note: {e}")
        current_url = input(f"Please paste the exact URL for Chapter {START_CHAPTER}: ").strip()

    chapter_files = []
    timestamps = []
    current_time_offset = 0.0

    for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
        if not current_url:
            print("No next chapter URL found. Ending loop.")
            break

        print(f"\n[Chapter {ch_num}/{END_CHAPTER}] Fetching: {current_url}")
        title, text, next_url = scrape_chapter_content(current_url)

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

        print(f"  -> Segmenting and balancing chunks across 8 workers...")
        segments = classify_chapter_segments(text, name_map)
        print(f"  -> Synthesizing {len(segments)} audio blocks in parallel...")
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

    # Lossless Merge
    master_manifest = os.path.join(BUILD_DIR, "master_list.txt")
    with open(master_manifest, "w", encoding="utf-8") as f:
        for cf in chapter_files:
            safe = os.path.abspath(cf).replace("\\", "/")
            f.write(f"file '{safe}'\n")

    print(f"\nMerging all chapters into: {FINAL_AUDIO}...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", master_manifest, "-c", "copy", FINAL_AUDIO
    ], check=True)

    print(f"Audiobook ready: {FINAL_AUDIO} (Total runtime: {format_timestamp(current_time_offset)})")

    # Render MP4 (Guaranteed MP4 Output)
    print(f"\nRendering YouTube-ready MP4: {FINAL_VIDEO}...")
    if os.path.exists(COVER_IMAGE):
        print(f"  -> Using cover artwork: '{COVER_IMAGE}'")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1",
            "-i", COVER_IMAGE, "-i", FINAL_AUDIO,
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            "-c:a", "copy", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-shortest", FINAL_VIDEO
        ], check=True)
    else:
        print(f"  -> No 'cover.jpg' found. Generating 1080p slate background automatically...")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x0f172a:s=1920x1080:r=1",
            "-i", FINAL_AUDIO,
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            "-c:a", "copy", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-shortest", FINAL_VIDEO
        ], check=True)

    print(f"\n[Done] Final Video Ready for YouTube: {FINAL_VIDEO}")


if __name__ == "__main__":
    asyncio.run(main())