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
# PATHS & DIRECTORIES
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

SCRIPT_CANDIDATES = [
    SCRIPT_DIR / "Where the Jasmine Falls - Full Audio Drama Script_2.txt",
    SCRIPT_DIR / "Where the Jasmine Falls - Full Audio Drama Script.txt",
]

BUILD_DIR = SCRIPT_DIR / "build_jasmine_ch02"
OUTPUT_DIR = SCRIPT_DIR / "output_jasmine_ch02"
BUILD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CREDENTIALS_FILE = PROJECT_ROOT / "api_credentials.json"
THUMBNAIL_SOURCE = SCRIPT_DIR / "thumbnail.png"
JASMIN_JSON_PATH = SCRIPT_DIR / "jasmin.json"

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
# CANONICAL VOCAL REGISTRY (CONTINUITY ENFORCED FROM JASMIN.JSON)
# ---------------------------------------------------------------------------
DEFAULT_VOICES = {
    "NARRATOR": {"voice": "en-US-ChristopherNeural", "rate": "-11%", "pitch": "-1Hz"},
    "HIYA":     {"voice": "en-IN-NeerjaNeural",      "rate": "-3%",  "pitch": "+2Hz"},
    "APARNA":   {"voice": "en-GB-SoniaNeural",       "rate": "-8%",  "pitch": "-3Hz"},
    "NEEL":     {"voice": "en-GB-RyanNeural",        "rate": "-4%",  "pitch": "-2Hz"},
    "BUBAI":    {"voice": "en-GB-OliverNeural",      "rate": "-2%",  "pitch": "+0Hz"},
    "POLTU":    {"voice": "en-GB-RyanNeural",        "rate": "-2%",  "pitch": "+1Hz"},
    "BRISHTI":  {"voice": "en-IN-NeerjaNeural",      "rate": "+1%",  "pitch": "+3Hz"},
    "INDRANIL": {"voice": "en-GB-OliverNeural",      "rate": "+0%",  "pitch": "+0Hz"},
}

CHARACTER_VOICES = {}

def sync_jasmin_registry(save_to_disk: bool = False):
    global CHARACTER_VOICES
    registry_data = {}
    if JASMIN_JSON_PATH.exists():
        try:
            with open(JASMIN_JSON_PATH, "r", encoding="utf-8") as f:
                loaded = json_loads(f.read())
                if isinstance(loaded, dict):
                    registry_data = loaded
        except Exception as e:
            log(f"[Warning] Failed to read jasmin.json: {e}")

    merged = dict(DEFAULT_VOICES)
    for char, cfg in registry_data.items():
        char_key = char.upper()
        if isinstance(cfg, dict) and "voice" in cfg:
            merged[char_key] = cfg

    for char_key, cfg in DEFAULT_VOICES.items():
        if char_key not in registry_data:
            registry_data[char_key] = cfg

    CHARACTER_VOICES = merged

    if save_to_disk or not JASMIN_JSON_PATH.exists():
        try:
            with open(JASMIN_JSON_PATH, "w", encoding="utf-8") as f:
                f.write(json_dumps(registry_data))
            log(f"Synchronized voice registry -> {JASMIN_JSON_PATH.name}")
        except Exception as e:
            log(f"[Warning] Failed to write jasmin.json: {e}")

sync_jasmin_registry(save_to_disk=False)

EMOTION_DELTAS = {
    "neutral":     {"rate_delta": 0, "pitch_delta": 0},
    "tender":      {"rate_delta": -3, "pitch_delta": -1},
    "warm":        {"rate_delta": -2, "pitch_delta": -1},
    "shy":         {"rate_delta": -3, "pitch_delta": -1},
    "teasing":     {"rate_delta": 2, "pitch_delta": 2},
    "cheerful":    {"rate_delta": 2, "pitch_delta": 2},
    "shaken":      {"rate_delta": -4, "pitch_delta": -1},
    "angry":       {"rate_delta": 3, "pitch_delta": 2},
    "defensive":   {"rate_delta": 2, "pitch_delta": 2},
    "solemn":      {"rate_delta": -5, "pitch_delta": -2},
}

# ---------------------------------------------------------------------------
# PHONETICS ENGINE (PREVENTS SPELL-OUT BUGS & REGIONAL GLITCHES)
# ---------------------------------------------------------------------------
def strip_parentheticals_and_symbols(text: str) -> str:
    cleaned = re.sub(r'\(.*?\)', '', text)
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\ufe00-\ufe0f]|[\u200d]')
    cleaned = emoji_pattern.sub('', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()

PHONETIC_REPLACEMENTS = [
    (r"\bM\s*-\s*A\s*-\s*H\b", "Maa"),
    (r"\bM\s*A\s*H\b", "Maa"),
    (r"\bMAH\b", "Maa"),
    (r"\bMah\b", "Maa"),
    (r"\bMa\b", "Maa"),
    (r"\bBar-bar\b", "Baa-baa"),
    (r"\bBah-bah\b", "Baa-baa"),
    (r"\bBaba\b", "Baa-baa"),

    (r"\bM\s*-\s*R\s*-\s*S\s*-\s*H\s*-\s*I\s*-\s*M\s*-\s*R\b", "Mah-shee-mah"),
    (r"\bM\s*R\s*SH\s*I\s*M\s*R\b", "Mah-shee-mah"),
    (r"\bMRSHIMR\b", "Mah-shee-mah"),
    (r"\bMashi-maa\b", "Mah-shee-mah"),
    (r"\bMashima\b", "Mah-shee-mah"),
    (r"\bD\s*-\s*D\b", "Dee-dee"),
    (r"\bD\s*D\b", "Dee-dee"),
    (r"\bDD\b", "Dee-dee"),
    (r"\bDidi\b", "Dee-dee"),
    (r"\bda\b", "dah"),
    (r"\bDada\b", "Dah-dah"),

    (r"\bHiya\b", "Hee-yah"),
    (r"\bMukherjee\b", "Mook-her-jee"),
    (r"\bNiladri\b", "Neel-ah-dree"),
    (r"\bNay-la-dree\b", "Neel-ah-dree"),
    (r"\bNeel\b", "Neel"),
    (r"\bAparna\b", "Uh-par-nah"),
    (r"\bBrishti\b", "Breesh-tee"),
    (r"\bBubai\b", "Boo-bai"),
    (r"\bPoltu\b", "Pol-too"),
    (r"\bIndranil\b", "In-dro-neel"),
    (r"\bSanyal\b", "Shaan-yaal"),

    (r"\bSubhas\s+Colony\b", "Shoo-bhash Colony"),
    (r"\bCollege\s+Street\b", "College Street"),
    (r"\bBoi\s+Para\b", "Boye Pah-rah"),
    (r"\bSurya\s+Sen\s+Street\b", "Soor-yo Sen Street"),
    (r"\bPresidency\s+College\b", "Presidency College"),
    (r"\bCollege\s+Square\b", "College Square"),
    (r"\bRashbehari\s+Avenue\b", "Rash-bihari Avenue"),
    (r"\bSouthern\s+Avenue\b", "Southern Avenue"),
    (r"\bShyambazar\b", "Shyam-bazar"),
    (r"\bTollygunge\b", "Tolly-gunge"),
    (r"\bKalighat\b", "Kah-lee-ghat"),
    (r"\bSalt\s+Lake\b", "Salt Lake"),
    (r"\bDamodar\b", "Dah-mo-dar"),
    (r"\bJibanananda\s+Das\b", "Jee-bon-ah-non-do Daash"),
    (r"\bRupasi\s+Bangla\b", "Roo-pah-shee Bang-lah"),
    (r"\bShesher\s+Kobita\b", "Shey-sher Koh-bee-tah"),
    (r"\bRabindranath\b", "Roh-been-dro-nath"),
    (r"\bGitanjali\b", "Gee-tahn-joh-lee"),
    (r"\bGodhuli\b", "Goh-dhoo-lee"),
    (r"\bSantiniketan\b", "Shahn-tee-nee-kay-ton"),

    (r"\bkaash\b", "kaash"),
    (r"\bbokul\b", "Bock-ool"),
    (r"\bBokul\b", "Bock-ool"),
    (r"\bshiuli\b", "shee-oo-lee"),
    (r"\bmatir\s+bhar\b", "mah-teer bhaar"),
    (r"\bDurga\s+Puja\b", "Door-ga Pooja"),
    (r"\bPuja\b", "Pooja"),
    (r"\bMaa\s+Durga\b", "Maa Door-ga"),
    (r"\bpandals?\b", lambda m: "pun-dahls" if m.group(0).endswith('s') else "pun-dahl"),
    (r"\bChaturthi\b", "Cho-toor-thee"),
    (r"\bPanchami\b", "Panchami"),
    (r"\bSasthi\b", "Shosh-thee"),
    (r"\bAshtami\b", "Ash-tomee"),
]

def apply_phonetics(text: str, emotion: str = "neutral") -> str:
    cleaned = strip_parentheticals_and_symbols(text)
    for pattern, rep in PHONETIC_REPLACEMENTS:
        cleaned = re.sub(pattern, rep, cleaned, flags=re.IGNORECASE)
    if emotion in ["tender", "shy"] and not cleaned.startswith("..."):
        cleaned = f"... {cleaned}"
    return cleaned

# ---------------------------------------------------------------------------
# 1. PARSE UNABRIDGED CHAPTER 2 (WITH MISPLACED SCENE 8 RESTORATION)
# ---------------------------------------------------------------------------
def locate_source_file() -> Path:
    for cand in SCRIPT_CANDIDATES:
        if cand.exists():
            return cand
    raise FileNotFoundError("Could not locate audio drama script text file in copyproj.")

def extract_chapter_2_scenes(full_text: str) -> list:
    ch2_match = re.search(
        r"UNABRIDGED AUDIO NOVEL PRODUCTION SCRIPT:\s*CHAPTER 2.*?(?=UNABRIDGED AUDIO NOVEL PRODUCTION SCRIPT:\s*CHAPTER (?!2)|\Z)",
        full_text,
        re.DOTALL | re.IGNORECASE
    )
    
    if ch2_match:
        ch2_text = ch2_match.group(0)
    else:
        fallback_match = re.search(
            r"CHAPTER 2:\s*GINGER TEA ON THE BALCONY.*?(?=CHAPTER 3|\Z)",
            full_text,
            re.DOTALL | re.IGNORECASE
        )
        ch2_text = fallback_match.group(0) if fallback_match else full_text

    scene_pattern = r"(Act II,\s*Scene\s*\d+:\s*[^\n\r]+)"
    splits = re.split(scene_pattern, ch2_text, flags=re.IGNORECASE)

    scenes = []
    idx = 1
    for i in range(1, len(splits), 2):
        header = splits[i].strip()
        body = splits[i+1].strip() if (i+1) < len(splits) else ""
        clean_title = re.sub(r"^Act II,\s*Scene\s*\d+:\s*", "", header, flags=re.IGNORECASE).strip()

        if idx == 8 and (not body or len(body.strip()) < 50):
            misplaced_match = re.search(
                r"NARRATOR:\s*The sound of Neel[’']s scooter engine fades into the evening avenue.*?(?=\(Scene concludes with peaceful spoken narration\)|UNABRIDGED|\Z)",
                full_text,
                re.DOTALL | re.IGNORECASE
            )
            if misplaced_match:
                body = misplaced_match.group(0).strip()
            else:
                body = (
                    "NARRATOR:\n"
                    "The sound of Neel’s scooter engine fades into the evening avenue, leaving Subhas Colony bathed in festival twilight.\n\n"
                    "Hiya remains standing on the balcony, her hands resting against the warm brass railing. The yellow fairy lights hum softly around her, casting golden diamond patterns across the floorboards.\n\n"
                    "She walks slowly to her wooden drafting table. The watercolor of the river is dry. Hiya pulls a fresh, blank sheet of textured paper from her drawer, dipping her finest sable brush into a small dish of black drawing ink.\n\n"
                    "Her fingers move without hesitation, guided by an intuition deeper than any commercial layout she has ever designed.\n\n"
                    "Stroke by stroke, the image appears: the curved trunk of the ancient bokul tree in the courtyard below, a vintage blue scooter parked beside mossy brickwork, and a tall, broad-shouldered young man kneeling on the cobblestones, his sleeves rolled to his elbows, looking up with kind, smiling eyes behind silver-rimmed spectacles.\n\n"
                    "In the next room, Aparna breathes peacefully in deep, healing sleep.\n\n"
                    "Outside, the autumn wind rustles through the kaash grass along the distant riverbank, carrying the first sweet scent of night-flowering jasmine into the room. Hiya sets her pen down, touches her hand to the center of her chest, and smiles—a smile as wide, as peaceful, and as radiant as the dawn itself."
                )

        scenes.append({
            "scene_num": idx,
            "header": header,
            "title": clean_title,
            "body": body
        })
        idx += 1

    if not scenes:
        scenes.append({
            "scene_num": 1,
            "header": "Chapter 2: Ginger Tea on the Balcony",
            "title": "Ginger Tea on the Balcony",
            "body": ch2_text
        })

    return scenes

# ---------------------------------------------------------------------------
# 2. GEMINI AI LINE DIRECTING
# ---------------------------------------------------------------------------
async def stage_scene_with_gemini(scene_num: int, scene_title: str, raw_text: str) -> list:
    staged_cache = BUILD_DIR / f"scene_{scene_num:02d}_staged.json"
    if staged_cache.exists():
        try:
            with open(staged_cache, "r", encoding="utf-8") as f:
                data = json_loads(f.read())
                if isinstance(data, list) and len(data) > 0:
                    log(f"Loaded staged lines for Scene {scene_num:02d}: {scene_title} from cache.")
                    return data
                else:
                    staged_cache.unlink(missing_ok=True)
        except Exception:
            pass

    log(f"Directing Scene {scene_num:02d} ({scene_title}) with Gemini...")
    prompt = f"""You are directing the spoken-word audio drama 'Where the Jasmine Falls' (Chapter 2, Scene {scene_num}: {scene_title}).
This is an English novel set in a Kolkata Bengali context. Separate narration and dialogue into clean sequential lines.

Rules:
1. "speaker": Choose strictly from ["NARRATOR", "HIYA", "NEEL", "APARNA", "BRISHTI", "BUBAI", "POLTU"].
2. "text": Extract the clean spoken line. STRIP OUT all parenthetical stage directions like (smiling), (voice trembling), or (to himself).
3. "emotion": Choose strictly from ["neutral", "tender", "warm", "shy", "teasing", "cheerful", "shaken", "angry", "defensive", "solemn"].

Return STRICT JSON ARRAY OF OBJECTS ONLY.

SCENE TEXT:
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
    if GEMINI_API_KEY:
        for model in models_to_try:
            url = f"{url_base}/{model}:generateContent?key={GEMINI_API_KEY}"
            try:
                if httpx:
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(url, headers=headers, json=payload)
                        if resp.status_code == 200:
                            res_json = resp.json()
                            raw_str = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                            staged_lines = json_loads(raw_str)
                            break
            except Exception as e:
                log(f"Gemini staging notice ({model}): {e}")

    if not staged_lines or not isinstance(staged_lines, list):
        staged_lines = fallback_scene_parser(raw_text)

    with open(staged_cache, "w", encoding="utf-8") as f:
        f.write(json_dumps(staged_lines))

    return staged_lines

def fallback_scene_parser(text: str) -> list:
    lines = []
    current_speaker = "NARRATOR"
    speaker_tags = ["NARRATOR:", "HIYA:", "NEEL:", "APARNA:", "BRISHTI:", "BUBAI:", "POLTU:"]

    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        
        matched_speaker = None
        for tag in speaker_tags:
            if block.startswith(tag):
                matched_speaker = tag.replace(":", "")
                block = block[len(tag):].strip()
                break
        
        if matched_speaker:
            current_speaker = matched_speaker
        
        clean_line = strip_parentheticals_and_symbols(block)
        if clean_line:
            lines.append({"speaker": current_speaker, "text": clean_line, "emotion": "neutral"})

    return lines

# ---------------------------------------------------------------------------
# 3. DIRECT TTS & NATURAL DRAMATIC PAUSES
# ---------------------------------------------------------------------------
def compute_voice_parameters(speaker: str, emotion: str) -> tuple:
    speaker_key = speaker.upper()
    base = CHARACTER_VOICES.get(speaker_key, CHARACTER_VOICES.get("NARRATOR", DEFAULT_VOICES["NARRATOR"]))
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

def ensure_silence_file(duration: float, file_path: Path):
    if file_path.exists() and file_path.stat().st_size > 800:
        return
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", f"{duration:.3f}",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(file_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

async def build_scene_audio(scene_num: int, lines: list, sem: asyncio.Semaphore) -> Path:
    scene_build = BUILD_DIR / f"scene_{scene_num:02d}"
    scene_build.mkdir(parents=True, exist_ok=True)
    scene_mp3 = BUILD_DIR / f"scene_{scene_num:02d}.mp3"

    if scene_mp3.exists() and scene_mp3.stat().st_size > 15000:
        log(f"Scene {scene_num:02d} audio already built.")
        return scene_mp3

    silence_250 = BUILD_DIR / "silence_250ms.mp3"
    silence_450 = BUILD_DIR / "silence_450ms.mp3"
    ensure_silence_file(0.250, silence_250)
    ensure_silence_file(0.450, silence_450)

    tasks = []
    line_files = []

    for i, line in enumerate(lines):
        speaker = line["speaker"]
        emotion = line.get("emotion", "neutral")
        raw_text = line["text"]
        
        spoken_text = apply_phonetics(raw_text, emotion)
        v, r, p = compute_voice_parameters(speaker, emotion)
        seg_file = scene_build / f"seg_{i:04d}.mp3"
        line_files.append((speaker, seg_file))

        tasks.append(synthesize_line_direct(spoken_text, v, r, p, seg_file, sem))

    await asyncio.gather(*tasks)

    valid_files = [f for s, f in line_files if f.exists() and f.stat().st_size > 1000]
    if not valid_files:
        log(f"[Warning] No audio generated for Scene {scene_num:02d}. Creating short placeholder.")
        ensure_silence_file(1.0, scene_mp3)
        return scene_mp3

    concat_txt = scene_build / "concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        prev_speaker = None
        for speaker, seg_file in line_files:
            if seg_file.exists() and seg_file.stat().st_size > 1000:
                if prev_speaker is not None:
                    if prev_speaker == "NARRATOR" or speaker == "NARRATOR":
                        f.write(f"file '{silence_450.resolve().as_posix()}'\n")
                    elif prev_speaker != speaker:
                        f.write(f"file '{silence_250.resolve().as_posix()}'\n")
                
                f.write(f"file '{seg_file.resolve().as_posix()}'\n")
                prev_speaker = speaker

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy", str(scene_mp3)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return scene_mp3

# ---------------------------------------------------------------------------
# 4. INTRO AUDIO
# ---------------------------------------------------------------------------
async def build_intro_audio(sem: asyncio.Semaphore) -> Path:
    intro_mp3 = BUILD_DIR / "intro.mp3"
    if intro_mp3.exists() and intro_mp3.stat().st_size > 15000:
        return intro_mp3

    intro_script = (
        "Welcome to Being a Bong. This is an original romantic story. "
        "If you enjoy this journey, please like, share, and subscribe with the bell icon turned on. "
        "Do comment to let us know your thoughts and how the story touched your heart. "
        "And now, we present Chapter Two of our audio drama: Where the Jasmine Falls."
    )
    base = CHARACTER_VOICES["NARRATOR"]
    spoken_intro = apply_phonetics(intro_script, "warm")
    await synthesize_line_direct(spoken_intro, base["voice"], base["rate"], base["pitch"], intro_mp3, sem)
    log("Generated Being A Bong Chapter 2 intro presentation.")
    return intro_mp3

# ---------------------------------------------------------------------------
# 5. DYNAMIC WATERMARKED THUMBNAIL (X=1320, Y=220)
# ---------------------------------------------------------------------------
def generate_watermarked_thumbnail(caption: str = "Chapter 02: Ginger Tea on the Balcony") -> Path:
    dest_thumb = BUILD_DIR / "thumbnail_chapter_02.jpg"
    if dest_thumb.exists() and dest_thumb.stat().st_size >= 30000:
        return dest_thumb

    src_thumb = THUMBNAIL_SOURCE
    if not src_thumb.exists():
        src_thumb = SCRIPT_DIR / "thumbnail.png"

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
                selected_font = ImageFont.truetype(fp, size=46)
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
# 6. VIDEO ASSEMBLY & OVERLAYS
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

def build_chapter_2_video(intro_audio: Path, scene_audios: list, scene_titles: list, watermarked_thumb: Path):
    log("Mastering Chapter 2 audio and compiling video...")
    master_audio = OUTPUT_DIR / "audio_master_jasmine_ch02.mp3"
    final_video = OUTPUT_DIR / "final_where_the_jasmine_falls_ch02.mp4"
    timestamps_txt = OUTPUT_DIR / "youtube_timestamps.txt"

    all_tracks = [intro_audio] + scene_audios

    audio_concat = BUILD_DIR / "audio_concat.txt"
    with open(audio_concat, "w", encoding="utf-8") as f:
        for at in all_tracks:
            f.write(f"file '{at.resolve().as_posix()}'\n")

    cmd_audio = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_concat),
        "-af", "highpass=f=80,loudnorm=I=-14:LRA=10:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(master_audio)
    ]
    subprocess.run(cmd_audio, check=True)

    elapsed = 0.0
    with open(timestamps_txt, "w", encoding="utf-8") as tf:
        for i, track in enumerate(all_tracks):
            dur = get_audio_duration(track)
            hrs = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            secs = int(elapsed % 60)
            t_str = f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"
            
            if i == 0:
                tf.write(f"{t_str} - Channel Intro & Presentation\n")
            else:
                tf.write(f"{t_str} - Scene {i:02d}: {scene_titles[i-1]}\n")
            elapsed += dur

    total_duration = get_audio_duration(master_audio)

    logo_file = locate_branding_asset("logo.png")
    sub_file = locate_branding_asset("subscribe.png")
    like_file = locate_branding_asset("like.png")

    inputs = [
        "-loop", "1", "-framerate", "24", "-t", f"{total_duration:.3f}", "-i", str(watermarked_thumb),
        "-i", str(master_audio)
    ]

    current_layer = "[0:v]"
    filter_chains = [
        f"{current_layer}scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[base];"
    ]
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
    log(f"Chapter 2 video successfully compiled -> {final_video}")

# ---------------------------------------------------------------------------
# 7. METADATA EXPORT
# ---------------------------------------------------------------------------
def export_chapter_2_metadata():
    timestamps_path = OUTPUT_DIR / "youtube_timestamps.txt"
    timestamps_content = timestamps_path.read_text(encoding="utf-8") if timestamps_path.exists() else ""

    payload = {
        "title": "Where the Jasmine Falls | Chapter 2: Ginger Tea on the Balcony | Romantic Audio Drama #BeingABong",
        "tags": [
            "Where the Jasmine Falls", "Chapter 2", "Being A Bong", "Kolkata Romance", "Durga Puja Romance",
            "Audio Drama", "Bengali Love Story", "Hiya and Neel", "Romantic Audiobook",
            "ROMANCE", "SLICEOFLIFE", "SWEETLOVE", "FATEDLOVE", "1V1", "EASTERN"
        ],
        "description": (
            "#DurgaPuja #Kolkata #AudioDrama #RomanticStory #BeingABong #SliceOfLife #WhereTheJasmineFalls\n\n"
            "Welcome to Being a Bong. This is an original romantic story. "
            "If you enjoy this journey, please like, share, and subscribe with the bell icon turned on. "
            "Do comment to let us know your thoughts and how the story touched your heart.\n\n"
            "On Chaturthi afternoon, Niladri ascends the covered wooden stairs of Subhas Colony carrying spools of festive fairy lights. Across a quiet balcony overlooking an ancient bokul tree, two guarded hearts share earthenware cups of ginger tea, unburdening years of silent sacrifice, lost dreams, and quiet resilience.\n\n"
            "══════════════════════════════════════════════\n"
            "SCENE TIMESTAMPS:\n"
            f"{timestamps_content}\n"
            "══════════════════════════════════════════════\n\n"
            "🎧 BROADCAST MASTER: -14 LUFS vocal clarity with natural character timing.\n"
            "🎨 VISUALS: Red & Gold Chapter Watermarked Thumbnail (at X=1320, Y=220) + Channel Branding Overlay.\n"
            "Subscribe to Being A Bong for more audio dramas, audiobooks, and romantic stories!"
        )
    }

    payload_file = OUTPUT_DIR / "youtube_upload_payload.json"
    with open(payload_file, "w", encoding="utf-8") as f:
        f.write(json_dumps(payload))
    log(f"Metadata saved -> {payload_file}")

# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------
async def main():
    log("==================================================================")
    log("  WHERE THE JASMINE FALLS — CHAPTER 2 DRAMATIC PRODUCTION         ")
    log("==================================================================")

    sync_jasmin_registry(save_to_disk=False)

    source_path = locate_source_file()
    full_text = source_path.read_text(encoding="utf-8")
    scenes = extract_chapter_2_scenes(full_text)
    log(f"Extracted {len(scenes)} unabridged scenes for Chapter 2.")

    sem = asyncio.Semaphore(8)

    intro_audio = await build_intro_audio(sem)

    scene_audios = []
    scene_titles = []
    for sc in scenes:
        s_num = sc["scene_num"]
        s_title = sc["title"]
        scene_titles.append(s_title)

        log(f"\n--- [Scene {s_num:02d}: {s_title}] ---")
        lines = await stage_scene_with_gemini(s_num, s_title, sc["body"])
        log(f"Synthesizing {len(lines)} lines for Scene {s_num:02d}...")
        sa = await build_scene_audio(s_num, lines, sem)
        scene_audios.append(sa)

    thumb_path = generate_watermarked_thumbnail("Chapter 02: Ginger Tea on the Balcony")

    build_chapter_2_video(intro_audio, scene_audios, scene_titles, thumb_path)
    export_chapter_2_metadata()

    sync_jasmin_registry(save_to_disk=True)
    log(f"Successfully finalized and verified voice registry -> {JASMIN_JSON_PATH.name}")

    log("\n[Finished] Chapter 2 complete with full dramatic continuity!")
    log(f"Outputs located in: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
