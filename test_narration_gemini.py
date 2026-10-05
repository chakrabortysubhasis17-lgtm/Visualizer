import os
import re
import json
import asyncio
import subprocess
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
import edge_tts

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AQ.Ab8RN6IAz25x6_DTjjrmdSenfUJJJq-oFLMndRdjtl_BNuPo-A"
)

TARGET_URL = "https://mtl-novel.com/novel/are-you-a-delicate-and-charming-educated-youth-from-the-1970s-youll-be-dead-in-a-flash/chapter-1-rampant-red-guards/"
OUTPUT_JSON = "chapter_1_speech_manifest.json"
FINAL_OUTPUT_MP3 = "chapter_1_preview.mp3"
BUILD_DIR = "build_test_audio"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# ==================== ADVANCED PYDANTIC SCHEMA ====================
class SpeechSegment(BaseModel):
    line_id: str = Field(description="Sequential identifier, e.g. '0001', '0002'")
    speaker_role: str = Field(description="Speaker name or crowd role label")
    gender: str = Field(description="Strictly: 'Male', 'Female', or 'Neutral'")
    age_category: str = Field(description="Strictly one of: 'toddler', 'young', 'teen', 'middle-aged', 'elder', or 'n/a'")
    emotion: str = Field(description="Dominant emotion: e.g. 'angry', 'romantic', 'cursing', 'fearful', 'sarcastic', 'neutral', 'excited', 'solemn'")
    edge_tts_voice: str = Field(description="Optimal Edge TTS voice name matched to gender and age")
    text: str = Field(description="The clean narrative sentence or spoken dialogue string")

class ChapterNarrationManifest(BaseModel):
    chapter_title: str = Field(description="Title extracted from the chapter")
    segments: list[SpeechSegment] = Field(description="Chronological ordered list of all parsed blocks")

def scrape_raw_chapter(url: str) -> tuple[str, str]:
    print(f"[*] Scraping content from: {url}", flush=True)
    resp = requests.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "Chapter 1"

    container = soup.find("article") or \
                soup.find("div", class_=re.compile(r"(chapter-content|entry-content|epcontent|post-content)", re.I)) or \
                soup.find("body")

    paragraphs = [p.get_text(strip=True) for p in container.find_all("p") if p.get_text(strip=True)]
    full_text = "\n\n".join(paragraphs)
    return title, full_text

def parse_chapter_via_gemini(client, title: str, raw_text: str) -> dict:
    print("[*] Sending chapter text to Gemini Director for Age, Emotion & Voice Mapping...", flush=True)

    system_instruction = """
You are an expert audiobook director and script supervisor.
Analyze raw novel text, separate exposition from dialogue, determine speaker demographics (gender and age bracket: toddler, young, teen, middle-aged, elder), extract emotion (angry, romantic, cursing, fearful, sarcastic, neutral, excited, solemn), and select matching Edge TTS voices.

VOICE MAPPING RULES:
- Narrator (Female): 'en-US-JennyNeural'
- Male Young / Teen: 'en-US-GuyNeural'
- Male Middle-Aged / Aggressive: 'en-US-RogerNeural'
- Male Elder: 'en-US-AndrewNeural' (lower pitch)
- Female Young / Protagonist: 'en-US-AriaNeural'
- Female Elder / Villager: 'en-US-EmmaNeural'
"""

    prompt_content = f"CHAPTER TITLE: {title}\n\nTEXT:\n{raw_text[:4000]}"

    if not client or not GENAI_AVAILABLE:
        return {}

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt_content,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=ChapterNarrationManifest,
            temperature=0.1
        )
    )

    if response and response.text:
        return json.loads(response.text)
    return {}

def calculate_prosody_adjustments(seg: dict) -> tuple[str, str]:
    """Calculates pitch and rate adjustments dynamically based on age and emotion."""
    age = seg.get("age_category", "young").lower()
    emotion = seg.get("emotion", "neutral").lower()
    line_type = seg.get("line_type", "Dialogue")

    base_pitch = 0
    base_rate = 5 # +5%

    # Age adjustments
    if age == "toddler":
        base_pitch += 6
        base_rate += 10
    elif age == "teen":
        base_pitch += 2
        base_rate += 8
    elif age == "elder":
        base_pitch -= 6
        base_rate -= 6
    elif age == "middle-aged":
        base_pitch -= 2
        base_rate += 2

    # Emotion adjustments
    if "angry" in emotion or "cursing" in emotion:
        base_pitch -= 2
        base_rate += 12 # Faster, aggressive pacing
    elif "excited" in emotion:
        base_pitch += 4
        base_rate += 10
    elif "fearful" in emotion:
        base_pitch += 3
        base_rate += 14
    elif "romantic" in emotion or "solemn" in emotion:
        base_pitch -= 3
        base_rate -= 6 # Slower, softer pacing

    if line_type == "Narration":
        base_pitch = 1
        base_rate = 4

    return f"{base_pitch:+d}Hz", f"{base_rate:+d}%"

async def synthesize_segment(seg: dict, out_path: str):
    voice = seg.get("edge_tts_voice", "en-US-JennyNeural")
    text = seg.get("text", "")
    pitch, rate = calculate_prosody_adjustments(seg)

    try:
        communicate = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
        await communicate.save(out_path)
    except Exception as e:
        print(f"[!] TTS error on line {seg['line_id']}: {e}", flush=True)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "1.0", "-q:a", "9", "-acodec", "libmp3lame", out_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

async def build_audio_preview(manifest: dict):
    os.makedirs(BUILD_DIR, exist_ok=True)
    segments = manifest.get("segments", [])
    print(f"\n[*] Synthesizing {len(segments)} emotion-modulated segments...", flush=True)

    chunk_files = []
    for seg in segments:
        line_id = seg["line_id"]
        c_path = os.path.join(BUILD_DIR, f"seg_{line_id}.mp3")
        chunk_files.append(c_path)
        print(f"    [{line_id}] ({seg['speaker_role']} | Age: {seg['age_category']} | Emotion: {seg['emotion']}): \"{seg['text'][:35]}...\"", flush=True)
        await synthesize_segment(seg, c_path)

    manifest_path = os.path.join(BUILD_DIR, "manifest.txt")
    valid_chunks = [cf for cf in chunk_files if os.path.exists(cf) and os.path.getsize(cf) > 100]

    if not valid_chunks:
        print("[!] No valid audio chunks generated.")
        return

    with open(manifest_path, "w", encoding="utf-8") as f:
        for cf in valid_chunks:
            f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

    print(f"[*] Stitching master preview: {FINAL_OUTPUT_MP3}...", flush=True)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest_path, "-c", "copy", FINAL_OUTPUT_MP3],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )

    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    try: os.remove(manifest_path)
    except OSError: pass
    try: os.rmdir(BUILD_DIR)
    except OSError: pass

    print(f"\n[✓] SUCCESS! Emotion & Age modulated preview ready: '{FINAL_OUTPUT_MP3}'")

def main():
    print("=" * 65)
    print(" GEMINI EMOTIONAL & DEMOGRAPHIC AUDIO SYNTHESIS TEST")
    print("=" * 65)

    client = None
    if GENAI_AVAILABLE and GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)

    title, raw_text = scrape_raw_chapter(TARGET_URL)
    print(f"[✓] Extracted Title: '{title}' ({len(raw_text)} characters total)", flush=True)

    manifest = parse_chapter_via_gemini(client, title, raw_text)

    if manifest:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"[✓] Manifest saved to '{OUTPUT_JSON}'")

        asyncio.run(build_audio_preview(manifest))
    else:
        print("[!] Failed to parse chapter manifest.")

if __name__ == "__main__":
    main()
