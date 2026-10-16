import os
import re
import sys
import glob
import shutil
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import edge_tts

# High-speed I/O with standard fallbacks
try:
    import orjson as json_mod
    def json_dumps(obj): return json_mod.dumps(obj, option=json_mod.OPT_INDENT_2).decode("utf-8")
    def json_loads(s): return json_mod.loads(s)
except ImportError:
    import json as json_mod
    def json_dumps(obj): return json_mod.dumps(obj, indent=2, ensure_ascii=False)
    def json_loads(s): return json_mod.loads(s)

try:
    import httpx
except ImportError:
    httpx = None

try:
    from rich.console import Console
    console = Console()
    def log(msg): console.log(msg)
except ImportError:
    def log(msg): print(msg, flush=True)

# ---------------------------------------------------------------------------
# PATHS & FOLDER RESOLUTION
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

EXTRACTED_CHAPTERS_DIR = SCRIPT_DIR / "extracted_chapters"
BUILD_DIR = SCRIPT_DIR / "build_durga_puja_01_11"
OUTPUT_DIR = SCRIPT_DIR / "output"
BUILD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CREDENTIALS_FILE = PROJECT_ROOT / "api_credentials.json"
REGISTRY_FILE = PROJECT_ROOT / "novel_entities_registry.json"
THUMBNAIL_SOURCE = SCRIPT_DIR / "thumbnail.png"

# ---------------------------------------------------------------------------
# CREDENTIALS LOADER
# ---------------------------------------------------------------------------
def load_credentials() -> dict:
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                return json_loads(f.read())
        except Exception as e:
            log(f"[Warning] Failed to read credentials: {e}")
    return {}

CREDS = load_credentials()
GEMINI_API_KEY = CREDS.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")

# ---------------------------------------------------------------------------
# NOVEL METADATA & ROMANTIC VOICE CASTING (NEERJA RESTORED / NO PRABHAT)
# ---------------------------------------------------------------------------
NOVEL_KEY = "when-durga-puja-brought-you-to-me"
NOVEL_TITLE = "When Durga Puja Brought You To Me"
ORIGINAL_AUTHOR = "Michi_0204"

CHARACTER_VOICES = {
    "Narrator": {"voice": "en-US-ChristopherNeural", "rate": "-9%",  "pitch": "+0Hz"},
    "Arijit":   {"voice": "en-US-RyanNeural",        "rate": "-2%",  "pitch": "+0Hz"},
    "Tara":     {"voice": "en-IN-NeerjaNeural",      "rate": "-1%",  "pitch": "+2Hz"},
    "Ananya":   {"voice": "en-IN-NeerjaNeural",      "rate": "-1%",  "pitch": "-1Hz"},
    "Rahul":    {"voice": "en-GB-RyanNeural",        "rate": "-3%",  "pitch": "-2Hz"},
    "Mother":   {"voice": "en-IN-NeerjaNeural",      "rate": "-10%", "pitch": "-5Hz"},
    "Rohan":    {"voice": "en-US-RyanNeural",        "rate": "+2%",  "pitch": "+3Hz"},
    "Kabir":    {"voice": "en-GB-RyanNeural",        "rate": "-3%",  "pitch": "-3Hz"},
    "Sneha":    {"voice": "en-IN-NeerjaNeural",      "rate": "+1%",  "pitch": "+1Hz"},
    "Priya":    {"voice": "en-IN-NeerjaNeural",      "rate": "+1%",  "pitch": "+2Hz"},
    "Manoj":    {"voice": "en-GB-RyanNeural",        "rate": "-4%",  "pitch": "-4Hz"},
    "Priest":   {"voice": "en-IN-NeerjaNeural",      "rate": "-12%", "pitch": "-6Hz"},
}

EMOTION_DELTAS = {
    "neutral":     {"rate_delta": 0, "pitch_delta": 0},
    "cheerful":    {"rate_delta": 2, "pitch_delta": 2},
    "teasing":     {"rate_delta": 2, "pitch_delta": 2},
    "tender":      {"rate_delta": -4, "pitch_delta": -1},
    "surprised":   {"rate_delta": 3, "pitch_delta": 3},
    "excited":     {"rate_delta": 4, "pitch_delta": 3},
    "shy":         {"rate_delta": -4, "pitch_delta": -1},
    "solemn":      {"rate_delta": -5, "pitch_delta": -2},
    "warm":        {"rate_delta": -2, "pitch_delta": -1},
    "embarrassed": {"rate_delta": 1, "pitch_delta": 2},
    "annoyed":     {"rate_delta": 2, "pitch_delta": 2},
}

# ---------------------------------------------------------------------------
# PHONETICS & PACING ENGINE
# ---------------------------------------------------------------------------
def strip_emojis_and_symbols(text: str) -> str:
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2600-\u27bf]'
        r'|[\u2300-\u23ff]'
        r'|[\ufe00-\ufe0f]'
        r'|[\u200d]'
    )
    cleaned = emoji_pattern.sub('', text)
    cleaned = re.sub(r'\b(cherry\s*blossom|flower)\b', '', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', cleaned).strip()

NARRATOR_PHONETICS = [
    (r"\bDurga\s+Puja\b", "Door-gaa Poo-jaa"),
    (r"\bDurga\b", "Door-gaa"),
    (r"\bPuja\b", "Poo-jaa"),
    (r"\bAshtami\b", "Ush-tomee"),
    (r"\bShashthi\b", "Shosh-thee"),
    (r"\bSaptami\b", "Shop-tomee"),
    (r"\bSaptamis\b", "Shop-tomees"),
    (r"\bAnjali\b", "On-joli"),
    (r"\bpandals?\b", lambda m: "pun-daals" if m.group(0).endswith('s') else "pun-daal"),
    (r"\bdhaak\b", "dhaak"),
    (r"\bdhunuchi\b", "dhoo-noo-chee"),
    (r"\bsandesh\b", "shon-desh"),
    (r"\broshogullas?\b", lambda m: "rosho-goollahs" if m.group(0).endswith('s') else "rosho-goollah"),
    (r"\brasgullas?\b", lambda m: "rosho-goollahs" if m.group(0).endswith('s') else "rosho-goollah"),
    (r"\bmishti\s+doi\b", "meesh-tee doy"),
    (r"\bbhog\b", "bhoag"),
    (r"\bGuwahati\b", "Goo-wah-hah-tee"),
    (r"\bTezpur\b", "Tayz-poor"),
    (r"\bThakurmoshai\b", "Thaa-koor-moshai"),
    (r"\bMount\s+Fuji\b", "Mount Foo-jee"),
]

DIALOGUE_PHONETICS = [
    (r"\bBhaiya\b", "Bhai-yaa"),
    (r"\bbhaiya\b", "bhai-yaa"),
    (r"\bBhai\s*sahab\b", "Bhai-saahab"),
    (r"\bArijit\b", "Uh-ri-jeet"),
    (r"\bTara\b", "Taaraa"),
    (r"\bAnanya\b", "Uh-naan-yaa"),
    (r"\bRahul\b", "Raahul"),
    (r"\bbeta\b", "bay-tah"),
    (r"\bBeta\b", "Bay-tah"),
    (r"\bThakurmoshai\b", "Thaa-koor-mo-shai"),
    (r"\bbaka\b", "baa-kaa"),
    (r"\bjiju\b", "jee-joo"),
    (r"\bArrey\b", "Uh-rey"),
    (r"\bWah\b", "Waah"),
    (r"\broshogullas?\b", lambda m: "rosho-goollahs" if m.group(0).endswith('s') else "rosho-goollah"),
    (r"\brasgullas?\b", lambda m: "rosho-goollahs" if m.group(0).endswith('s') else "rosho-goollah"),
    (r"\bsandesh\b", "shon-desh"),
    (r"\bdoi\b", "doy"),
    (r"\bAshtami\b", "Ush-tomee"),
    (r"\bDurga\s+Puja\b", "Door-gaa Poo-jaa"),
    (r"\bPuja\b", "Poo-jaa"),
    (r"\bpandals?\b", lambda m: "pun-daals" if m.group(0).endswith('s') else "pun-daal"),
    (r"\bMount\s+Fuji\b", "Mount Foo-jee"),
]

def apply_phonetic_fixes(text: str, speaker: str, emotion: str = "neutral") -> str:
    cleaned = strip_emojis_and_symbols(text)
    for pattern, replacement in DIALOGUE_PHONETICS:
        cleaned = re.sub(pattern, replacement, cleaned)
    if speaker == "Narrator":
        for pattern, replacement in NARRATOR_PHONETICS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
            
    # Expressive pacing: soften abrupt dialogue starts with micro-breaths
    if emotion in ["tender", "shy"] and not cleaned.startswith("..."):
        cleaned = f"... {cleaned}"
    return cleaned

# ---------------------------------------------------------------------------
# 1. NON-DESTRUCTIVE REGISTRY MERGE
# ---------------------------------------------------------------------------
def merge_novel_entities_registry():
    log("[1/5] Synchronizing novel_entities_registry.json with high-performance voice mapping...")
    registry_data = {}
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                registry_data = json_loads(f.read())
        except Exception as e:
            log(f"[Warning] Registry read issue: {e}")

    if NOVEL_KEY not in registry_data:
        registry_data[NOVEL_KEY] = {
            "title": NOVEL_TITLE,
            "author": ORIGINAL_AUTHOR,
            "genre": "Slice of Life / Festive Romance",
            "characters": {}
        }

    for char_name, vinfo in CHARACTER_VOICES.items():
        registry_data[NOVEL_KEY]["characters"][char_name] = {
            "voice": vinfo["voice"],
            "rate": vinfo["rate"],
            "pitch": vinfo["pitch"],
            "role": "Narrator" if char_name == "Narrator" else "Character"
        }

    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            f.write(json_dumps(registry_data))
        log(f"Synced {len(CHARACTER_VOICES)} entities into '{REGISTRY_FILE.name}'.")
    except Exception as e:
        log(f"[Warning] Failed to update registry file: {e}")

# ---------------------------------------------------------------------------
# 2. GEMINI AI NARRATIVE DIRECTOR & STAGING
# ---------------------------------------------------------------------------
async def stage_chapter_with_gemini(ch_num: int, raw_text: str) -> list:
    staged_cache = BUILD_DIR / f"ch_{ch_num:02d}_staged.json"
    if staged_cache.exists():
        try:
            with open(staged_cache, "r", encoding="utf-8") as f:
                data = json_loads(f.read())
                if isinstance(data, list) and len(data) > 0:
                    log(f"Loaded staged dialogue for Chapter {ch_num:02d} from cache.")
                    return data
        except Exception:
            pass

    if not GEMINI_API_KEY:
        log(f"[Warning] No GEMINI_API_KEY. Using heuristic staging for Chapter {ch_num:02d}.")
        return fallback_dialogue_parser(raw_text)

    log(f"Directing Chapter {ch_num:02d} with Gemini (Romantic Emotional Staging)...")

    prompt = f"""You are directing the audio performance for the romantic festive novel '{NOVEL_TITLE}' by {ORIGINAL_AUTHOR}.
This is a tender story of blossoming young love between 17-year-old Arijit and 16-year-old Tara against the backdrop of Durga Puja.

Analyze the chapter text and split it into sequential performance lines.
Rules:
1. "speaker": Choose strictly from ["Narrator", "Arijit", "Tara", "Ananya", "Rahul", "Mother", "Rohan", "Kabir", "Sneha", "Priya", "Priest", "Manoj"].
   - Arijit: 17yo earnest student, quiet, romantic, polite.
   - Tara: 16yo expressive Bengali girl, sweet, playful, thoughtful, blushing.
   - Rahul: 30s caring doctor brother.
   - Ananya: 30s lively, teasing doctor sister.
   - Mother: 60s warm, affectionate Indian mother.
2. "text": Spoken prose. Remove emojis or flower symbols. Keep narrative descriptions and dialogues authentic.
3. "emotion": Choose strictly from:
   ["neutral", "cheerful", "teasing", "tender", "surprised", "excited", "shy", "solemn", "warm", "embarrassed", "annoyed"].

Return STRICT JSON ARRAY OF OBJECTS ONLY.

CHAPTER TEXT:
{raw_text}
"""

    models_to_try = ["gemini-2.5-flash-lite", "gemini-flash-lite-latest", "gemini-1.5-flash"]
    url_base = "https://generativelanguage.googleapis.com/v1beta/models"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }

    staged_lines = None
    for model_name in models_to_try:
        url = f"{url_base}/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            if httpx:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        raw_json_str = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                        staged_lines = json_loads(raw_json_str)
                        break
        except Exception as e:
            log(f"Gemini staging notice ({model_name}): {e}")

    if not staged_lines or not isinstance(staged_lines, list):
        staged_lines = fallback_dialogue_parser(raw_text)

    with open(staged_cache, "w", encoding="utf-8") as f:
        f.write(json_dumps(staged_lines))

    return staged_lines

def fallback_dialogue_parser(text: str) -> list:
    lines = []
    pattern = re.compile(r'["“](.*?)["”]')
    for p in text.split("\n"):
        p = p.strip()
        if not p or p.startswith("=") or p.startswith("Chapter"):
            continue
        matches = list(pattern.finditer(p))
        if not matches:
            lines.append({"speaker": "Narrator", "text": p, "emotion": "neutral"})
            continue
        pos = 0
        for m in matches:
            pre = p[pos:m.start()].strip()
            if pre:
                lines.append({"speaker": "Narrator", "text": pre, "emotion": "neutral"})
            quote = m.group(1).strip()
            surr = (p[max(0, m.start()-40):m.start()] + " " + p[m.end():min(len(p), m.end()+40)]).lower()
            
            speaker, emotion = "Arijit", "neutral"
            if any(k in surr for k in ["tara", "she smiled", "she asked", "she giggled"]):
                speaker, emotion = "Tara", "tender" if "soft" in surr or "quiet" in surr else "cheerful"
            elif any(k in surr for k in ["ananya", "didi"]):
                speaker, emotion = "Ananya", "teasing"
            elif any(k in surr for k in ["rahul", "doctor"]):
                speaker, emotion = "Rahul", "cheerful"
            elif any(k in surr for k in ["rohan", "papa"]):
                speaker, emotion = "Rohan", "excited"
            elif any(k in surr for k in ["mother", "aunty", "ma!"]):
                speaker, emotion = "Mother", "warm"
            elif any(k in surr for k in ["priest", "thakurmoshai"]):
                speaker, emotion = "Priest", "solemn"
            elif any(k in surr for k in ["sneha", "priya"]):
                speaker, emotion = "Sneha", "teasing"

            if quote:
                lines.append({"speaker": speaker, "text": quote, "emotion": emotion})
            pos = m.end()
        post = p[pos:].strip()
        if post:
            lines.append({"speaker": "Narrator", "text": post, "emotion": "neutral"})
    return lines

# ---------------------------------------------------------------------------
# 3. DIRECT ASYNC IN-PROCESS SYNTHESIS ENGINE (HIGH PERFORMANCE)
# ---------------------------------------------------------------------------
def compute_voice_parameters(speaker: str, emotion: str) -> tuple:
    base = CHARACTER_VOICES.get(speaker, CHARACTER_VOICES["Narrator"])
    voice = base["voice"]
    
    base_rate = int(base["rate"].replace("%", "").replace("+", ""))
    base_pitch = int(base["pitch"].replace("Hz", "").replace("+", ""))

    delta = EMOTION_DELTAS.get(emotion.lower(), {"rate_delta": 0, "pitch_delta": 0})
    final_rate = f"{base_rate + delta['rate_delta']:+d}%"
    final_pitch = f"{base_pitch + delta['pitch_delta']:+d}Hz"
    return voice, final_rate, final_pitch

async def synthesize_line_direct(text: str, voice: str, rate: str, pitch: str, out_path: Path, sem: asyncio.Semaphore) -> bool:
    if out_path.exists() and out_path.stat().st_size > 2500:
        return True

    async with sem:
        for attempt in range(1, 5):
            try:
                comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await asyncio.wait_for(comm.save(str(out_path)), timeout=25.0)
                if out_path.exists() and out_path.stat().st_size > 1000:
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.3 * attempt)

    return False

async def build_chapter_audio(ch_num: int, lines: list, sem: asyncio.Semaphore) -> Path:
    ch_build = BUILD_DIR / f"ch_{ch_num:02d}"
    ch_build.mkdir(parents=True, exist_ok=True)
    ch_mp3 = BUILD_DIR / f"chapter_{ch_num:02d}.mp3"

    if ch_mp3.exists() and ch_mp3.stat().st_size > 15000:
        log(f"Chapter {ch_num:02d} audio already built.")
        return ch_mp3

    tasks = []
    line_files = []

    for i, line in enumerate(lines):
        speaker = line["speaker"]
        emotion = line.get("emotion", "neutral")
        raw_text = line["text"]
        
        spoken_text = apply_phonetic_fixes(raw_text, speaker, emotion)
        v, r, p = compute_voice_parameters(speaker, emotion)
        seg_file = ch_build / f"seg_{i:04d}.mp3"
        line_files.append(seg_file)

        tasks.append(synthesize_line_direct(spoken_text, v, r, p, seg_file, sem))

    await asyncio.gather(*tasks)

    valid_files = [f for f in line_files if f.exists() and f.stat().st_size > 1000]
    concat_txt = ch_build / "concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for vf in valid_files:
            f.write(f"file '{vf.resolve().as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy", str(ch_mp3)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return ch_mp3

# ---------------------------------------------------------------------------
# 4. CHANNEL INTRO
# ---------------------------------------------------------------------------
async def build_intro_audio(sem: asyncio.Semaphore) -> Path:
    intro_mp3 = BUILD_DIR / "chapter_00_intro.mp3"
    if intro_mp3.exists() and intro_mp3.stat().st_size > 15000:
        return intro_mp3

    intro_script = (
        "Welcome to Being A Bong! If you love our audiobooks and romantic stories, "
        "please take a moment to like this video, share it with your friends, "
        "and subscribe to Being A Bong with the notification bell turned on so you never miss a release. "
        "A heartfelt thank you to the author, Michi zero two zero four, for writing this charming and nostalgic festive romance, "
        "'When Durga Puja Brought You To Me'. "
        "And now, let us begin the story with chapters one to eleven."
    )

    spoken_intro = apply_phonetic_fixes(intro_script, "Narrator")
    base = CHARACTER_VOICES["Narrator"]

    await synthesize_line_direct(spoken_intro, base["voice"], base["rate"], base["pitch"], intro_mp3, sem)
    log("Generated Being A Bong channel intro & author acknowledgment.")
    return intro_mp3

# ---------------------------------------------------------------------------
# 5. DYNAMIC RED & GOLD WATERMARK GENERATOR (X=1320, Y=220)
# ---------------------------------------------------------------------------
def generate_watermarked_thumbnail(ch_num: int, raw_chapter_text: str) -> Path:
    dest_thumb = BUILD_DIR / f"thumbnail_chapter_{ch_num:02d}.jpg"
    if dest_thumb.exists() and dest_thumb.stat().st_size >= 30000:
        return dest_thumb

    src_thumb = THUMBNAIL_SOURCE
    if not src_thumb.exists():
        src_thumb = Path(r"D:\Projects\visualer\copyproj\thumbnail.png")
    
    if not src_thumb.exists():
        raise FileNotFoundError(f"Base thumbnail not found at '{src_thumb}'. Please place thumbnail.png in copyproj.")

    lines = [l.strip() for l in raw_chapter_text.splitlines() if l.strip()]
    chapter_heading = f"Chapter {ch_num:02d}"
    for l in lines[:3]:
        if "chapter" in l.lower() or len(l) < 60:
            chapter_heading = l.replace("#", "").strip()
            break

    chapter_heading = re.sub(r'^(?:chapter|chaper)\s*\d+[:\-–—]*\s*', '', chapter_heading, flags=re.I).strip()
    caption = f"Chapter {ch_num:02d}: {chapter_heading}" if chapter_heading else f"Chapter {ch_num:02d}"

    log(f"Watermarking thumbnail dynamically for Chapter {ch_num:02d} ('{caption}') at X=1320, Y=220...")

    base_img = Image.open(src_thumb).convert("RGBA")

    font_paths = [
        "C:\\Windows\\Fonts\\seguiembl.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    
    selected_font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                selected_font = ImageFont.truetype(fp, size=48)
                break
            except Exception:
                continue
    
    if not selected_font:
        selected_font = ImageFont.load_default()

    img_copy = base_img.copy()
    draw = ImageDraw.Draw(img_copy)

    x, y = 1320, 220
    bbox = draw.textbbox((x, y), caption, font=selected_font)
    padding = 18
    box_rect = [bbox[0] - padding, bbox[1] - (padding - 2), bbox[2] + padding, bbox[3] + (padding - 2)]
    
    draw.rounded_rectangle(box_rect, radius=14, fill=(139, 0, 0, 230), outline=(255, 215, 0, 255), width=3)

    border_width = 3
    for ox in range(-border_width, border_width + 1):
        for oy in range(-border_width, border_width + 1):
            if ox != 0 or oy != 0:
                draw.text((x + ox, y + oy), caption, font=selected_font, fill=(0, 0, 0, 255))

    draw.text((x, y), caption, font=selected_font, fill=(255, 215, 0, 255))

    rgb_img = img_copy.convert("RGB")
    rgb_img.save(dest_thumb, "JPEG", quality=95)
    return dest_thumb

# ---------------------------------------------------------------------------
# 6. HIGH-SPEED VIDEO ASSEMBLY WITH BRANDING OVERLAYS
# ---------------------------------------------------------------------------
def locate_branding_asset(filename: str) -> Path:
    local_p = SCRIPT_DIR / filename
    if local_p.exists():
        return local_p
    parent_p = PROJECT_ROOT / filename
    if parent_p.exists():
        return parent_p
    return None

def get_audio_duration(file_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return float(res.stdout.strip()) if res.stdout.strip() else 0.0

def build_full_video_marathon(audio_tracks: list, chapter_thumbs: list, chapter_titles: list):
    log("[4/4] Mastering audio and compiling video marathon at accelerated render speeds...")
    master_audio = OUTPUT_DIR / "audio_master_durga_puja_01_11.mp3"
    final_video = OUTPUT_DIR / "final_durga_puja_01_11.mp4"
    timestamps_txt = OUTPUT_DIR / "youtube_timestamps.txt"

    # 1. Master Audio Concatenation & Vocal Warmth Polish
    audio_concat = BUILD_DIR / "audio_concat.txt"
    with open(audio_concat, "w", encoding="utf-8") as f:
        for at in audio_tracks:
            f.write(f"file '{at.resolve().as_posix()}'\n")

    cmd_audio = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_concat),
        "-af", "highpass=f=80,loudnorm=I=-14:LRA=10:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(master_audio)
    ]
    subprocess.run(cmd_audio, check=True)

    # 2. YouTube Timestamps Generation
    elapsed = 0.0
    with open(timestamps_txt, "w", encoding="utf-8") as tf:
        for i, at in enumerate(audio_tracks):
            dur = get_audio_duration(at)
            hrs = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            secs = int(elapsed % 60)
            t_str = f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"
            
            if i == 0:
                tf.write(f"{t_str} - Channel Intro & Author Tribute\n")
            else:
                tf.write(f"{t_str} - Chapter {i:02d}: {chapter_titles[i-1]}\n")
            elapsed += dur

    # 3. Create FFmpeg Concat Slide List
    intro_dur = get_audio_duration(audio_tracks[0])
    slideshow_concat_txt = BUILD_DIR / "slideshow_concat.txt"
    with open(slideshow_concat_txt, "w", encoding="utf-8") as sf:
        for idx, thumb in enumerate(chapter_thumbs, 1):
            dur = get_audio_duration(audio_tracks[idx])
            if idx == 1:
                dur += intro_dur
            sf.write(f"file '{thumb.resolve().as_posix()}'\n")
            sf.write(f"duration {dur:.3f}\n")
        if chapter_thumbs:
            sf.write(f"file '{chapter_thumbs[-1].resolve().as_posix()}'\n")

    # 4. Locate Branding Badges
    logo_file = locate_branding_asset("logo.png")
    sub_file = locate_branding_asset("subscribe.png")
    like_file = locate_branding_asset("like.png")

    inputs = [
        "-f", "concat", "-safe", "0", "-i", str(slideshow_concat_txt),
        "-i", str(master_audio)
    ]
    
    current_layer = "[0:v]"
    filter_chains = [f"{current_layer}scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[base];"]
    current_layer = "[base]"
    overlay_idx = 2

    if logo_file:
        inputs.extend(["-i", str(logo_file)])
        filter_chains.append(f"{current_layer}[{overlay_idx}:v]overlay=W-w-40:40[with_logo];")
        current_layer = "[with_logo]"
        overlay_idx += 1

    if like_file:
        inputs.extend(["-i", str(like_file)])
        filter_chains.append(f"{current_layer}[{overlay_idx}:v]overlay=50:H-h-50[with_like];")
        current_layer = "[with_like]"
        overlay_idx += 1

    if sub_file:
        inputs.extend(["-i", str(sub_file)])
        filter_chains.append(f"{current_layer}[{overlay_idx}:v]overlay=W-w-50:H-h-50[vout]")
    else:
        filter_chains.append(f"{current_layer}null[vout]")

    # Performance-optimized FFmpeg video encoding (-tune stillimage, -preset veryfast, -r 24)
    cmd_video = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", "".join(filter_chains),
        "-map", "[vout]", "-map", "1:a",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast", "-crf", "20",
        "-r", "24", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_video)
    ]

    subprocess.run(cmd_video, check=True)
    log(f"Successfully compiled final video marathon -> {final_video}")

# ---------------------------------------------------------------------------
# 7. METADATA EXPORT
# ---------------------------------------------------------------------------
def export_youtube_payload():
    log("[5/5] Generating YouTube metadata payload...")
    timestamps_path = OUTPUT_DIR / "youtube_timestamps.txt"
    timestamps_content = timestamps_path.read_text(encoding="utf-8") if timestamps_path.exists() else ""

    payload = {
        "title": "When Durga Puja Brought You To Me | Romantic | Teens | Fantasy Romance Audiobook #fantasyaudiobooks",
        "tags": [
            "Being A Bong", "Durga Puja Romance", "Bengali Love Story", "Audiobook Marathon",
            "Michi_0204", "Indian Romance Audiobook", "Guwahati", "Tezpur",
            "ROMANCE", "SLICEOFLIFE", "TEEN", "SWEETLOVE", "FATEDLOVE", "FIRSTLOVE", "SWEET", "1V1", "EASTERN"
        ],
        "description": (
            "Welcome to Being A Bong! Please like, share, and subscribe to support our channel.\n\n"
            f"A heartfelt thank you to the author, {ORIGINAL_AUTHOR}, for writing this charming and nostalgic festive romance!\n\n"
            "An unexpected car ride during Durga Puja shopping brings seventeen-year-old dreamer Arijit Chatterjee face-to-face "
            "with the lively, expressive Tara Mazumder. What begins as a simple ride between colleagues turns into playful "
            "sibling teasing, chaotic road trips, matching blue traditional outfits, and unforgettable memories under the festive pandal lights.\n\n"
            "══════════════════════════════════════════════\n"
            "TIMESTAMPS:\n"
            f"{timestamps_content}\n"
            "══════════════════════════════════════════════\n\n"
            "🎧 BROADCAST MASTER: -14 LUFS vocal clarity with authentic Indian voice casting.\n"
            "🎨 VISUALS: Red & Gold Watermarked Chapter Thumbnails (at X=1320, Y=220) + Channel Branding Overlay.\n"
            "Subscribe to Being A Bong for more audiobooks and cultural stories!\n\n"
            "#BeingABong #DurgaPuja #BengaliStory #AudiobookMarathon #IndianRomance #FullAudiobook #fantasyaudiobooks"
        )
    }

    payload_file = OUTPUT_DIR / "youtube_upload_payload.json"
    with open(payload_file, "w", encoding="utf-8") as f:
        f.write(json_dumps(payload))
    log(f"YouTube upload metadata saved -> {payload_file}")

# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------
def natural_chapter_sort_key(file_path: str) -> int:
    match = re.search(r"Chapter\s*(\d+)", Path(file_path).name, re.IGNORECASE)
    return int(match.group(1)) if match else 0

async def main():
    log("==================================================================")
    log("  DURGA PUJA ROMANCE - HIGH PERFORMANCE ENGINE (CH 01 - 11)      ")
    log("==================================================================")

    merge_novel_entities_registry()

    chapter_files = sorted(glob.glob(str(EXTRACTED_CHAPTERS_DIR / "Chapter *.txt")), key=natural_chapter_sort_key)
    if not chapter_files:
        log(f"Error: No text files found in '{EXTRACTED_CHAPTERS_DIR}'")
        return

    log(f"Found {len(chapter_files)} chapters ready to process.")

    # High-performance async semaphore (8 parallel non-blocking streams)
    sem = asyncio.Semaphore(8)
    audio_tracks = []
    chapter_thumbs = []
    chapter_titles = []

    log("\n--- [INTRO] BEING A BONG PRESENTATION ---")
    intro_audio = await build_intro_audio(sem)
    audio_tracks.append(intro_audio)

    for idx, cf in enumerate(chapter_files, 1):
        raw_text = Path(cf).read_text(encoding="utf-8")
        first_line = raw_text.splitlines()[0] if raw_text.splitlines() else f"Chapter {idx:02d}"
        clean_title = re.sub(r"^Chapter\s*\d+\s*-\s*", "", first_line).strip()
        chapter_titles.append(clean_title)

        log(f"\n--- [CHAPTER {idx:02d}/{len(chapter_files):02d}] {clean_title} ---")
        ch_thumb = generate_watermarked_thumbnail(idx, raw_text)
        chapter_thumbs.append(ch_thumb)

        lines = await stage_chapter_with_gemini(idx, raw_text)
        log(f"Synthesizing Chapter {idx:02d} audio ({len(lines)} directed lines via high-speed async)...")
        ca = await build_chapter_audio(idx, lines, sem)
        audio_tracks.append(ca)

    build_full_video_marathon(audio_tracks, chapter_thumbs, chapter_titles)
    export_youtube_payload()

    log("\n[Finished] All 11 chapters rendered at high performance!")
    log(f"Outputs saved to: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
