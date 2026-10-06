import os
import re
import io
import sys
import json
import time
import random
import shutil
import base64
import asyncio
import subprocess
import urllib.parse
import requests
from bs4 import BeautifulSoup
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pydantic import BaseModel, Field

# Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from entity_manager import EntityManager
except ImportError:
    EntityManager = None

# ==================== ARCHITECTURAL & API CONFIG ====================
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AQ.Ab8RN6IAz25x6_DTjjrmdSenfUJJJq-oFLMndRdjtl_BNuPo-A"
)

# Cloudflare Workers AI Credentials (Tier 1 GPU Visual Engine)
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "60ea0428a4b6bd44eeef701cee024518")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "cfut_jFW6WAXHIsZAwayo09xXRQxsupmNPa0BecNmrnMM70d9ea43")

START_CHAPTER = 201
END_CHAPTER = 250
BATCH_SIZE = 5
PARALLEL_CHAPTERS = 2
GLOBAL_MAX_CONCURRENT_TTS = 3
MAX_NARRATION_MERGE_WORDS = 210
TARGET_DIALOGUE_CHUNK_WORDS = 65

CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"
REQUEST_TIMEOUT = 50

# 4 Watermark Overlay Assets
BRANDING_ASSETS = {
    "logo": "logo.png",
    "subscribe": "subscribe.png",
    "like": "like.png",
    "voice": "voice.png"
}

# Pollinations fallback cooldown queue
POLLINATIONS_COOLDOWNS = [38, 10, 10, 10, 10, 10]

NOVEL_SLUG = "global-rainstorm-my-shelter-is-an-air-fortress"
START_URL = "https://mtl-novel.com/novel/global-rainstorm-my-shelter-is-an-air-fortress/chapter-201-fetal-movement-at-the-earths-core-the-pressure-of-a-divinity/"

BUILD_DIR = "build_global_rainstorm_201_250"
FINAL_AUDIO = "output_global_rainstorm_201_250.mp3"
FINAL_VIDEO = "final_global_rainstorm_201_250.mp4"
COVER_IMAGE = "cover_global_rainstorm_201_250.jpg"
TIMESTAMPS_FILE = "youtube_timestamps_global_rainstorm_201_250.txt"
SUBTITLES_FILE = "subtitles_global_rainstorm_201_250.srt"
PAYLOAD_FILE = "youtube_upload_payload_global_rainstorm_201_250.json"

VIDEO_TITLE = "EARTH'S CORE AWAKENS, MY AIR FORTRESS CRUSHES DIVINITY! [Ch 201-250] | LitRPG Audiobook"
TAGS = [
    "LitRPG Audiobook", "Global Rainstorm", "Doomsday Shelter",
    "Air Fortress", "Earth Core Divinity", "Spatial Warp", "Apocalypse Survival", 
    "Full Audiobook Marathon", "Being A Bong"
]

DESC_HEADER = (
    "As tectonic plates rupture and the planetary core begins its catastrophic fetal pulse, "
    "a primordial slumbering divinity awakens beneath the submerged mantle!\n\n"
    "While boiling magma tsunamis vaporize surface fleets and divine pressure crushes human shelters, "
    "Lu Zhou engages the Air Fortress's maximum anti-gravity thrusters and antimatter void matrices. "
    "Hovering above the shattered crust, humanity's apex airborne citadel aims its hyper-velocity orbital "
    "railguns straight into the awakening godhead!\n\n"
    "Welcome to Chapters 201 to 250 of 'Global Rainstorm: My Shelter is an Air Fortress' "
    "in full multi-voice dramatization!\n\n"
    "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
    "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system warnings, and module diagnostics).\n"
    "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
    "══════════════════════════════════════════════\nTIMESTAMPS:\n"
)

DESC_FOOTER = (
    "\n══════════════════════════════════════════════\n\n"
    "🌟 KEY ARC HIGHLIGHTS:\n"
    "• Ch 201: Fetal Movement of Earth's Core & Primordial Divine Pressure\n"
    "• Ch 210: Boiling Magma Deluge & Sub-Crustal Energy Eruption\n"
    "• Ch 222: Fortress Hull Overload & Spatial Forcefield Defiance\n"
    "• Ch 235: Decapitating the Awakened Core Colossus\n"
    "• Ch 245: Harnessing the Divine Core Law Reactor\n"
    "• Ch 250: Orbital Sovereign Ascent Above the Ruined Planet\n\n"
    "══════════════════════════════════════════════\n"
    "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
    "All original novel concepts belong to the author. Subscribe for more!\n\n"
    "#GlobalRainstorm #LitRPG #DoomsdayShelter #AudiobookMarathon #FullAudiobook #BeingABong"
)

GRADIENT_PALETTES = [
    ((100, 230, 255), (20, 110, 240)),
    ((255, 215, 100), (240, 90, 30)),
    ((180, 120, 255), (90, 30, 210)),
]

# 10 High-contrast 3D action portrait blocks for Chapters 201 to 250
BLOCKS = [
    {
        "index": 1, "range": (201, 205),
        "title": ["EARTH CORE PULSE", "PRESSURE OF A DIVINITY"],
        "fallback_color": (15, 25, 40),
        "prompt": (
            "Ultra-sharp cinematic close-up portrait of a male manhwa hero with jet-black hair "
            "and brilliant golden-amber eyes, wearing heavy silver-and-cobalt armor plates. Flawless facial features, "
            "crisp detailed skin textures, macro studio focus. Directly in the background behind him, deep cracks in the ocean floor "
            "radiate blinding subterranean crimson magma and boiling orange steam, while a massive high-tech sky fortress hovers securely "
            "above the vortex. Sharp streaks of violet spatial lightning arc across the dark indigo sky, creating high color contrast."
        )
    },
    {
        "index": 2, "range": (206, 210),
        "title": ["MAGMA TSUNAMI", "STRATOSPHERE LIFT-OFF"],
        "fallback_color": (35, 20, 15),
        "prompt": (
            "Clear, high-contrast 3D portrait layout of a dark-haired commander wearing crimson-trimmed tactical power armor. "
            "Razor-sharp foreground focus on the character, clean studio lighting, pristine face definition. In the scene behind him, "
            "a colossal wave of boiling orange magma and bright volcanic sparks erupts violently out of a dark teal sea. "
            "In the upper background, the clean silhouette of a massive steel air fortress ascends into a dark indigo sky, "
            "creating a striking color separation between warm orange and cool tones."
        )
    },
    {
        "index": 3, "range": (211, 215),
        "title": ["ANCIENT GODHEAD SEAL", "VOID RAILGUN SALVO"],
        "fallback_color": (25, 20, 45),
        "prompt": (
            "Ultra-sharp high-contrast 3D action portrait of a handsome male commander standing on the open exterior command deck. "
            "Clear foreground focus, flawless facial features, sharp lines. Beside him, high-tech tactical interface nodes float cleanly, "
            "glowing with vibrant neon green and hot-pink matrix telemetry grids. In the background sky behind him, heavy mechanical railguns "
            "on the citadel fire blinding golden-white kinetic slugs downward into a massive glowing orange runic rift in the crust."
        )
    },
    {
        "index": 4, "range": (216, 220),
        "title": ["ABYSSAL GODHEAD", "DIVINE SHOCKWAVE"],
        "fallback_color": (30, 15, 35),
        "prompt": (
            "Cinematic close-up portrait of a dark-haired warrior hero with intense violet eyes, clad in midnight-blue armor. "
            "Razor-sharp edge definition, clear bright studio lighting, pristine texturing. Directly behind him in the background, a massive "
            "shadowy celestial titan entity with glowing amethyst eyes emerges from beneath a cracked mantle. Concentrated, solid cyan energy shields "
            "on the air fortress deflect explosive waves of amber and crimson volcanic sparks, creating clean color separation."
        )
    },
    {
        "index": 5, "range": (221, 225),
        "title": ["ANTIMATTER OVERLOAD", "SPATIAL CRUST PIERCER"],
        "fallback_color": (20, 35, 50),
        "prompt": (
            "Ultra-sharp 3D digital portrait of a male anime hero with crisp black hair and stark white-and-gold armor plating. "
            "Flawless facial features, crystal clear macro focus, perfectly balanced studio portrait light. Behind him, the mechanical hull "
            "of a giant sky fortress discharges a monumental antimatter beam cannon, unleashing a solid, concentrated pillar of brilliant "
            "sapphire-blue and emerald-green energy straight downward. Deep clean shadows, vivid multi-colored composition."
        )
    },
    {
        "index": 6, "range": (226, 230),
        "title": ["SUB-CRUSTAL DRONES", "CORE HARVEST OPERATION"],
        "fallback_color": (20, 40, 30),
        "prompt": (
            "High-contrast 3D action portrait of a powerful black-haired warrior hero clad in dark chrome armor with gold accents. "
            "Razor-sharp foreground focus, clean edges, flawless facial details, zero motion blur. In the background landscape behind him, "
            "advanced white aerospace drones dive into deep subterranean fissures, extracting colossal, glowing amber-gold crystal fragments. "
            "Deep clean shadows, sharp crimson plasma sparks erupting, completely multi-hued palette visualization."
        )
    },
    {
        "index": 7, "range": (231, 235),
        "title": ["CONTINENTAL SHATTER", "APEX BATTLE MATRIX"],
        "fallback_color": (40, 20, 25),
        "prompt": (
            "Ultra-sharp 3D portrait layout of a male manhwa warrior wearing highly detailed tactical power armor. "
            "Crystal clear focus on his face and hair, pristine textures, professional bright lighting. In the action scene behind him, "
            "massive continental tectonic plates break apart under dark teal oceans, while the citadel hull launches a salvo of hundreds "
            "of bright orange guided missiles tracking toward giant glowing crimson magma titans. Clean geometric details."
        )
    },
    {
        "index": 8, "range": (236, 240),
        "title": ["CORE AVATAR EXECUTION", "SLAYING THE DIVINITY"],
        "fallback_color": (35, 15, 45),
        "prompt": (
            "Breathtaking 3D cinematic visual. Close-up sharp focus on a powerful black-haired anime commander standing firm in ornate armor. "
            "Clear facial features, perfect edge definition, studio light alignment. Directly behind him, a colossal ancient core-avatar deity "
            "is pierced by solid, glowing golden electromagnetic spears from the sky. Explosive clouds of hot-pink, cyan, and violet divine energy "
            "burst in the background clouds, generating highly saturated color contrast."
        )
    },
    {
        "index": 9, "range": (241, 245),
        "title": ["DIVINE LAW ENGINE", "PLANETARY MATRIX BINDING"],
        "fallback_color": (20, 30, 55),
        "prompt": (
            "Dramatic high-contrast 3D visual. Close-up portrait of a powerful dark-haired hero wearing pitch-black armor with glowing cyan energy lines. "
            "Razor-sharp edge definition, clean facial details, macro focus. Directly behind him in the background scene, the central fortress reactor "
            "core absorbs an immense, floating crystalline artifact fragment, radiating clean, blinding concentric rings of golden, magenta, "
            "and turquoise light outward into the stratosphere."
        )
    },
    {
        "index": 10, "range": (246, 250),
        "title": ["ORBITAL SKY SOVEREIGN", "RULER OF THE NEW ERA"],
        "fallback_color": (15, 30, 45),
        "prompt": (
            "Premium cinematic 3D climax visual. Close-up profile shot of Commander Lu Zhou in ornate gold-trimmed silver naval armor at dawn. "
            "Razor-sharp focus on the profile, flawless skin and armor details, crisp clean lines. He stands firmly on an open sweeping flight deck. "
            "Behind him, a majestic upgraded sky fortress structure shines beneath brilliant multi-colored auroras of neon green, deep violet, and warm amber light."
        )
    }
]

BASE_CHARACTERS = {
    "narrator": {"display_name": "Narrator", "gender": "Male", "line_type": "Narration", "voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+5%"},
    "mc": {"display_name": "Lu Zhou", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-GuyNeural", "pitch": "-2Hz", "rate": "+6%"},
    "fortress_system": {"display_name": "Fortress System", "gender": "Synthetic", "line_type": "System", "voice": "en-US-SteffanNeural", "pitch": "-18Hz", "rate": "-6%"},
    "liu_shishi": {"display_name": "Liu Shishi", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-JennyNeural", "pitch": "+2Hz", "rate": "+6%"},
    "boss_xu": {"display_name": "Boss Xu", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-JennyNeural", "pitch": "+2Hz", "rate": "+8%"},
    "chu_rou": {"display_name": "Chu Rou", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-AriaNeural", "pitch": "+1Hz", "rate": "+5%"},
    "aunt_zhang": {"display_name": "Aunt Zhang", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-EmmaNeural", "pitch": "+2Hz", "rate": "+8%"},
    "abyssal_lord": {"display_name": "Abyssal Divinity", "gender": "Synthetic", "line_type": "Dialogue", "voice": "en-US-SteffanNeural", "pitch": "-15Hz", "rate": "+4%"},
    "fleet_commander": {"display_name": "Fleet Commander", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-RogerNeural", "pitch": "-8Hz", "rate": "+2%"},
    "raider_captain": {"display_name": "Raider Captain", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-EricNeural", "pitch": "+6Hz", "rate": "+10%"},
    "survivors": {"display_name": "Survivors", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-TonyNeural", "pitch": "+2Hz", "rate": "+8%"}
}

# ==================== PYDANTIC SCHEMAS FOR GEMINI DIRECTOR ====================
class SpeechSegment(BaseModel):
    line_id: str = Field(description="Sequential identifier, e.g. '0001', '0002'")
    speaker_role: str = Field(description="Speaker name, character alias, or 'Narrator'")
    gender: str = Field(description="Strictly: 'Male', 'Female', or 'Neutral'")
    age_category: str = Field(description="Strictly: 'toddler', 'young', 'teen', 'middle-aged', 'elder', or 'n/a'")
    emotion: str = Field(description="Dominant emotion: e.g. 'angry', 'fearful', 'sarcastic', 'neutral', 'excited', 'solemn'")
    line_type: str = Field(description="'Dialogue', 'Narration', or 'System'")
    edge_tts_voice: str = Field(description="Optimal Edge TTS voice: en-US-GuyNeural, en-US-JennyNeural, en-US-AriaNeural, en-US-SteffanNeural, etc.")
    text: str = Field(description="The spoken dialogue string or exposition sentence")

class ChapterNarrationManifest(BaseModel):
    chapter_title: str = Field(description="Clean title of the chapter")
    segments: list[SpeechSegment] = Field(description="Chronological ordered list of parsed speech segments")

def calculate_prosody_adjustments(seg: dict) -> tuple[str, str]:
    age = seg.get("age_category", "young").lower()
    emotion = seg.get("emotion", "neutral").lower()
    line_type = seg.get("line_type", "Dialogue")

    base_pitch = 0
    base_rate = 5

    if age == "toddler":
        base_pitch += 6; base_rate += 10
    elif age == "teen":
        base_pitch += 2; base_rate += 8
    elif age == "elder":
        base_pitch -= 6; base_rate -= 6
    elif age == "middle-aged":
        base_pitch -= 2; base_rate += 2

    if "angry" in emotion or "cursing" in emotion:
        base_pitch -= 2; base_rate += 12
    elif "excited" in emotion:
        base_pitch += 4; base_rate += 10
    elif "fearful" in emotion:
        base_pitch += 3; base_rate += 14
    elif "romantic" in emotion or "solemn" in emotion:
        base_pitch -= 3; base_rate -= 6

    if line_type == "Narration":
        base_pitch = 0
        base_rate = 5

    return f"{base_pitch:+d}Hz", f"{base_rate:+d}%"

# ==================== AUTOMATED SEO TIMESTAMP CLEANER ====================
def clean_chapter_title_for_seo(raw_title: str, ch_num: int) -> str:
    cleaned = re.sub(r'^(?:chapter|ch\.?)\s*\d+[\s:\-–—]+(?:chapter|ch\.?)\s*\d+[\s:\-–—]*', '', raw_title, flags=re.I)
    cleaned = re.sub(r'^(?:chapter|ch\.?)\s*\d+[\s:\-–—]*', '', cleaned, flags=re.I).strip()
    if not cleaned:
        cleaned = f"Earth Core Divinity Phase {ch_num}"
    return f"Ch {ch_num:03d}: {cleaned.title()}"

# ==================== TEXT PROCESSING & SCRAPING ====================
RE_SYSTEM = re.compile(r"(?:\[|【|〔|『|〖|［)(Ding!|System|Notice|Warning|Announcement|Prompt|Module|Fortress|Scanner|Reward|Divinity|Core).*?(?:\]|】|〕|』|〗|］)", re.I)
RE_SCENE_DIVIDER = re.compile(r"^(\s*[*~=_#-]\s*){3,}$", re.MULTILINE)
WATERMARK_PATTERNS = [
    re.compile(r"\(End of this chapter\)", re.I),
    re.compile(r"Please visit mtl-novel\.com.*", re.I),
    re.compile(r"Check out our latest novel.*", re.I),
    re.compile(r"\[TL Note:.*?\]", re.I),
    re.compile(r"https?://\S+", re.I),
    re.compile(r"【?\s*Brain Storage\s*】?", re.I),
    re.compile(r"【?\s*Please come in, dear readers\.?\s*】?", re.I)
]
FULLWIDTH_TO_ASCII = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '「': '"', '」': '"',
    '，': ', ', '。': '. ', '！': '! ', '？': '? ',
    '：': ': ', '；': '; ', '（': '(', '）': ')'
})
RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def clean_and_normalize_text(text: str) -> str:
    cleaned = text.translate(FULLWIDTH_TO_ASCII)
    cleaned = RE_SCENE_DIVIDER.sub("", cleaned)
    for pat in WATERMARK_PATTERNS:
        cleaned = pat.sub("", cleaned)
    cleaned = re.sub(r'~+', '', cleaned)
    cleaned = re.sub(r'\*{2,}', '', cleaned)
    cleaned = re.sub(r'\.{4,}', '...', cleaned)
    return re.sub(r"[ \t]+", " ", cleaned).strip()

def balance_paragraph_quotes(paragraph: str) -> str:
    if paragraph.count('"') % 2 != 0:
        if re.search(r'\b(said|replied|whispered|murmured|asked|smiled|sneered)\b', paragraph, re.I):
            paragraph = paragraph + '"'
        else:
            paragraph = '"' + paragraph
    return paragraph

def scrape_chapter_content(session: requests.Session, url: str, ch_num: int):
    print(f"[{NOVEL_SLUG}] Connecting to Ch.{ch_num:03d}: {url}", flush=True)
    resp = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    raw_title = h1.get_text(strip=True) if h1 else f"Chapter {ch_num}"
    clean_title = clean_chapter_title_for_seo(raw_title, ch_num)

    container = soup.find("article") or \
                soup.find("div", class_=re.compile(r"(chapter-content|entry-content|epcontent|post-content|reading-content)", re.I)) or \
                soup.find("div", id=re.compile(r"(chapter-content|content|article)", re.I)) or \
                soup.find("body")

    paragraphs = [clean_and_normalize_text(p.get_text(strip=True)) for p in container.find_all("p")]
    paragraphs = [p for p in paragraphs if p and RE_ALPHANUM.search(p)]

    if not paragraphs:
        paragraphs = [f"Chapter {ch_num}. Deep beneath the ocean floor, the earth core stirs as divine pressure surges upward."]

    full_text = f"{clean_title}.\n\n" + "\n\n".join(paragraphs)

    next_url = None
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        rel = a.get("rel", "")
        if isinstance(rel, list): rel = " ".join(rel)
        t = a.get_text(strip=True).lower()
        if ("next" in rel.lower() or "next" in t or "»" in t or "next chapter" in t) and href not in ["#", ""]:
            full_next = urllib.parse.urljoin(url, href)
            if full_next != url:
                next_url = full_next
                break

    if not next_url:
        target_pattern = re.compile(rf"/chapter-{ch_num + 1}(?:[/-]|$)", re.I)
        for a in soup.find_all("a", href=True):
            if target_pattern.search(a["href"]):
                next_url = urllib.parse.urljoin(url, a["href"])
                break

    if not next_url:
        pattern_curr = re.compile(rf"(chapter-){ch_num}([/-])", re.I)
        if pattern_curr.search(url):
            next_url = pattern_curr.sub(rf"\g<1>{ch_num + 1}\g<2>", url)

    return clean_title, full_text, next_url

def parse_chapter_via_gemini_director(client, title: str, raw_text: str, fallback_char_map: dict) -> list:
    if not client or not GENAI_AVAILABLE:
        return fallback_rule_based_staging(raw_text, fallback_char_map)

    system_instruction = """
You are an expert audiobook director and script supervisor.
Analyze the chapter text, cleanly separating exposition/narration from spoken dialogue and shelter system alerts.
For every segment:
1. Identify the speaker (Lu Zhou, Liu Shishi, Boss Xu, Chu Rou, Aunt Zhang, Fortress System, Abyssal Divinity, Fleet Commander, Raider Captain, Survivors, or Narrator).
2. Determine gender ('Male', 'Female', 'Neutral') and age bracket ('young', 'teen', 'middle-aged', 'elder', 'n/a').
3. Detect dominant emotion ('angry', 'fearful', 'sarcastic', 'neutral', 'excited', 'solemn').
4. Assign optimal voice:
   - Narrator (Male): 'en-US-GuyNeural'
   - Lu Zhou / Commander: 'en-US-GuyNeural'
   - Liu Shishi / Boss Xu: 'en-US-JennyNeural'
   - Chu Rou / Medical Officer: 'en-US-AriaNeural'
   - Aunt Zhang / Older Female: 'en-US-EmmaNeural'
   - Fortress System / Core: 'en-US-SteffanNeural'
   - Fleet Commander: 'en-US-RogerNeural'
   - Raider Captain: 'en-US-EricNeural'
   - Survivors / Mob: 'en-US-TonyNeural'
"""

    prompt = f"CHAPTER: {title}\n\nCONTENT:\n{raw_text[:7000]}"

    try:
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChapterNarrationManifest,
                temperature=0.1
            )
        )
        if response and response.text:
            data = json.loads(response.text)
            staged = []
            for s in data.get("segments", []):
                pitch, rate = calculate_prosody_adjustments(s)
                staged.append({
                    "line_id": s.get("line_id", "0001"),
                    "speaker": s.get("speaker_role", "Narrator"),
                    "gender": s.get("gender", "Male"),
                    "line_type": s.get("line_type", "Narration"),
                    "emotion": s.get("emotion", "neutral"),
                    "age_category": s.get("age_category", "young"),
                    "text": s.get("text", "").strip(),
                    "voice": s.get("edge_tts_voice", "en-US-GuyNeural"),
                    "pitch": pitch,
                    "rate": rate
                })
            if staged:
                return staged
    except Exception as e:
        print(f"     [Gemini Director Notice] {e}. Using fallback staging...", flush=True)

    return fallback_rule_based_staging(raw_text, fallback_char_map)

def fallback_rule_based_staging(text: str, char_map: dict) -> list:
    paragraphs = text.split("\n\n")
    raw_tokens = []
    for p in paragraphs:
        p_clean = balance_paragraph_quotes(p.strip())
        if not p_clean or not RE_ALPHANUM.search(p_clean):
            continue
        parts = p_clean.split('"')
        for i, raw_chunk in enumerate(parts):
            chunk = raw_chunk.strip()
            if not chunk or not RE_ALPHANUM.search(chunk):
                continue
            raw_tokens.append({"is_quote": (i % 2 != 0), "text": chunk})

    staged_segments = []
    for idx, token in enumerate(raw_tokens):
        if not token["is_quote"]:
            line_type = "System" if RE_SYSTEM.search(token["text"]) else "Narration"
            role_key = "fortress_system" if line_type == "System" else "narrator"
            staged_segments.append({"role_key": role_key, "line_type": line_type, "text": token["text"]})
        else:
            prev_narr = ""
            for back_idx in range(idx - 1, -1, -1):
                if not raw_tokens[back_idx]["is_quote"]:
                    prev_narr = raw_tokens[back_idx]["text"][-85:]
                    break
            
            p_low = prev_narr.lower()
            if any(w in p_low for w in ["shishi", "liu shishi"]):
                role_key = "liu_shishi"
            elif any(w in p_low for w in ["boss xu", "xu wan", "director xu"]):
                role_key = "boss_xu"
            elif any(w in p_low for w in ["chu rou", "doctor", "officer chu"]):
                role_key = "chu_rou"
            elif any(w in p_low for w in ["aunt zhang", "director zhang"]):
                role_key = "aunt_zhang"
            elif any(w in p_low for w in ["divinity", "godhead", "primordial", "abyssal"]):
                role_key = "abyssal_lord"
            elif any(w in p_low for w in ["fleet commander", "admiral", "captain"]):
                role_key = "fleet_commander"
            elif any(w in p_low for w in ["raider", "pirate", "sneered"]):
                role_key = "raider_captain"
            elif any(w in p_low for w in ["survivor", "crowd", "refugee", "scavenger"]):
                role_key = "survivors"
            else:
                role_key = "mc"

            staged_segments.append({"role_key": role_key, "line_type": "Dialogue", "text": token["text"]})

    consolidated = []
    for seg in staged_segments:
        if consolidated and consolidated[-1]["role_key"] == "narrator" and seg["role_key"] == "narrator":
            if len(consolidated[-1]["text"].split()) + len(seg["text"].split()) <= MAX_NARRATION_MERGE_WORDS:
                consolidated[-1]["text"] += " " + seg["text"]
                continue
        consolidated.append(seg)

    staged_records = []
    line_seq = 1
    for seg in consolidated:
        rk = seg["role_key"]
        role_meta = char_map.get(rk, char_map["mc"] if seg["line_type"] == "Dialogue" else char_map["narrator"])
        tp = seg["text"].strip()
        if not re.search(r'[.!?…]$', tp):
            tp = tp + "."
        staged_records.append({
            "line_id": f"{line_seq:04d}",
            "speaker": role_meta["display_name"],
            "gender": role_meta["gender"],
            "line_type": seg["line_type"],
            "text": tp,
            "voice": role_meta["voice"],
            "pitch": role_meta["pitch"],
            "rate": role_meta["rate"]
        })
        line_seq += 1

    return staged_records

# ==================== VISUAL RENDERING ENGINE (CLOUDFLARE FLUX) ====================
def ensure_cinzel_font() -> str:
    if os.path.exists(CINZEL_LOCAL_PATH) and os.path.getsize(CINZEL_LOCAL_PATH) > 10000:
        return CINZEL_LOCAL_PATH
    try:
        resp = requests.get(CINZEL_URL, timeout=12)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(CINZEL_LOCAL_PATH, "wb") as f:
                f.write(resp.content)
            return CINZEL_LOCAL_PATH
    except Exception:
        pass
    for fp in ["C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/timesbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]:
        if os.path.exists(fp):
            return fp
    return "arialbd.ttf"

def fit_crop_and_sharpen_1080p(img: Image.Image) -> Image.Image:
    target_w, target_h = 1920, 1080
    target_ratio = target_w / target_h
    img_w, img_h = img.size
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        new_w = int(img_h * target_ratio)
        left = (img_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, img_h))
    else:
        new_h = int(img_w / target_ratio)
        top = (img_h - new_h) // 2
        img = img.crop((0, top, img_w, top + new_h))

    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(1.06)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Color(img).enhance(1.20)
    img = img.filter(ImageFilter.DETAIL)
    img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=145, threshold=0))
    img = ImageEnhance.Sharpness(img).enhance(1.25)
    return img

def fetch_comic_artwork_landscape(prompt: str, out_path: str, block_index: int) -> bool:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return True

    clean_p = " ".join(prompt.split()).strip()

    # ------------------ TIER 1: CLOUDFLARE WORKERS AI ------------------
    if CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN:
        print(f"     [Visual Engine] Requesting Block {block_index} via Cloudflare Workers AI (FLUX-1-schnell)...", flush=True)
        url_cf = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        headers_cf = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
        payload_cf = {"prompt": clean_p, "steps": 4}
        try:
            resp = requests.post(url_cf, headers=headers_cf, json=payload_cf, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                raw_bytes = None
                try:
                    data = resp.json()
                    if "result" in data and "image" in data["result"]:
                        raw_bytes = base64.b64decode(data["result"]["image"])
                except Exception:
                    pass
                if not raw_bytes and len(resp.content) > 5000:
                    raw_bytes = resp.content

                if raw_bytes:
                    img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
                    img = fit_crop_and_sharpen_1080p(img)
                    img.convert("RGB").save(out_path, "JPEG", quality=98)
                    print(f"     [Visual Engine] [✓] Delivered Block {block_index} via Cloudflare!", flush=True)
                    return True
            else:
                print(f"     [Visual Engine] Cloudflare HTTP {resp.status_code}: {resp.text[:120]}. Routing to Pollinations with cooldown...", flush=True)
        except Exception as e:
            print(f"     [Visual Engine] Cloudflare notice: {e}. Routing to Pollinations fallback...", flush=True)

    # ------------------ TIER 2: POLLINATIONS FALLBACK (38-10-10-10-10-10s COOLDOWN QUEUE) ------------------
    print(f"     [Visual Engine] Triggering Pollinations Fallback for Block {block_index} (Cooldown Queue: {POLLINATIONS_COOLDOWNS})...", flush=True)
    encoded = urllib.parse.quote(clean_p)

    for attempt, wait_sec in enumerate(POLLINATIONS_COOLDOWNS, start=1):
        seed = random.randint(10000, 9999999)
        target_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed}&model=flux&nologo=true"

        try:
            resp = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > 10000:
                raw_temp = out_path + ".tmp.jpg"
                with open(raw_temp, "wb") as f:
                    f.write(resp.content)
                base = Image.open(raw_temp).convert("RGBA")
                bw, bh = base.size
                base = base.crop((0, 0, bw, bh - int(bh * 0.055)))
                base = fit_crop_and_sharpen_1080p(base)
                base.convert("RGB").save(out_path, "JPEG", quality=98)
                try: os.remove(raw_temp)
                except OSError: pass
                print(f"     [Visual Engine] [✓] Delivered Block {block_index} via Pollinations (Attempt {attempt})!", flush=True)
                return True
            else:
                print(f"     [Visual Engine] Pollinations attempt {attempt}/{len(POLLINATIONS_COOLDOWNS)} returned HTTP {resp.status_code}. Waiting {wait_sec}s cooldown...", flush=True)
        except Exception as e:
            print(f"     [Visual Engine] Pollinations attempt {attempt}/{len(POLLINATIONS_COOLDOWNS)} network error: {e}. Waiting {wait_sec}s cooldown...", flush=True)

        time.sleep(wait_sec)

    return False

def apply_lower_third_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(overlay)
    vig_start = int(height * 0.72)
    for y in range(vig_start, height):
        alpha = int(85 * (((y - vig_start) / (height - vig_start)) ** 1.3))
        v_draw.line([(0, y), (width, y)], fill=(12, 18, 35, alpha))
    return Image.alpha_composite(base.convert("RGBA"), overlay)

def stamp_four_corner_branding(base: Image.Image, build_dir: str) -> Image.Image:
    """
    Stamps all 4 corner branding assets scaled to fill the marked corner boundaries:
    1. Top-Left: logo.png (Channel Identity, 380px wide)
    2. Top-Right: subscribe.png (CTA Pill, 460px wide)
    3. Bottom-Left: like.png (Engagement Thumbs-Up, 240px tall)
    4. Bottom-Right: voice.png (Audioform Badge, 480px wide)
    """
    if base.mode != "RGBA":
        base = base.convert("RGBA")

    # 1. Top-Left (logo.png -> 380px wide)[cite: 18]
    logo_path = os.path.join(build_dir, BRANDING_ASSETS["logo"])
    if os.path.exists(logo_path):
        try:
            img = Image.open(logo_path).convert("RGBA")
            target_w = 380
            target_h = int(img.size[1] * (target_w / float(img.size[0])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (30, 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting logo: {e}", flush=True)

    # 2. Top-Right (subscribe.png -> 460px wide)[cite: 18]
    sub_path = os.path.join(build_dir, BRANDING_ASSETS["subscribe"])
    if os.path.exists(sub_path):
        try:
            img = Image.open(sub_path).convert("RGBA")
            target_w = 460
            target_h = int(img.size[1] * (target_w / float(img.size[0])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (1920 - target_w - 30, 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting subscribe: {e}", flush=True)

    # 3. Bottom-Left (like.png -> 240px tall)[cite: 18]
    like_path = os.path.join(build_dir, BRANDING_ASSETS["like"])
    if os.path.exists(like_path):
        try:
            img = Image.open(like_path).convert("RGBA")
            target_h = 240
            target_w = int(img.size[0] * (target_h / float(img.size[1])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (30, 1080 - target_h - 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting like: {e}", flush=True)

    # 4. Bottom-Right (voice.png -> 480px wide)[cite: 18]
    voice_path = os.path.join(build_dir, BRANDING_ASSETS["voice"])
    if os.path.exists(voice_path):
        try:
            img = Image.open(voice_path).convert("RGBA")
            target_w = 480
            target_h = int(img.size[1] * (target_w / float(img.size[0])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (1920 - target_w - 30, 1080 - target_h - 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting voice: {e}", flush=True)

    return base

def create_vertical_gradient_text_mask(width: int, height: int, line: str, font: ImageFont.FreeTypeFont, top_col: tuple, bot_col: tuple) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.text((0, 0), line, fill=255, font=font)
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    for y in range(height):
        factor = y / max(1, height - 1)
        r = int(top_col[0] + (bot_col[0] - top_col[0]) * factor)
        g = int(top_col[1] + (bot_col[1] - top_col[1]) * factor)
        b = int(top_col[2] + (bot_col[2] - top_col[2]) * factor)
        g_draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    gradient.putalpha(mask)
    return gradient

def stamp_3d_metallic_flame_typography(base: Image.Image, lines: list) -> Image.Image:
    """
    Renders 2-line title typography shifted upwards towards the center (y ~ 66%)
    without chapter numbers, with enlarged font (78pt / 64pt) and thick stroke separation[cite: 18].
    """
    width, height = base.size
    font_path = ensure_cinzel_font()
    title_font = ImageFont.truetype(font_path, 78)
    sub_font = ImageFont.truetype(font_path, 64)
    line_spacing = 96
    
    clean_lines = [l for l in lines if not re.match(r"^chapters?\s*\d+", l.strip(), re.I)]
    total_text_h = (len(clean_lines) - 1) * line_spacing + 80
    
    start_y = int(height * 0.66) - (total_text_h // 2)

    for i, line in enumerate(clean_lines):
        active_font = sub_font if i > 0 else title_font
        bbox = ImageDraw.Draw(base).textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)
        
        # Dual-layer dark outline stroke
        ImageDraw.Draw(base).text((x + 4, y + 5), line, font=active_font, fill=(15, 20, 30, 255), stroke_width=7, stroke_fill=(15, 20, 30, 255))
        ImageDraw.Draw(base).text((x, y), line, font=active_font, fill=(30, 45, 60, 255), stroke_width=4, stroke_fill=(30, 45, 60, 255))
        
        # Gradient metallic fill
        palette = GRADIENT_PALETTES[min(i, len(GRADIENT_PALETTES) - 1)]
        grad_layer = create_vertical_gradient_text_mask(text_w + 25, text_h + 25, line, active_font, palette[0], palette[1])
        base.paste(grad_layer, (x, y), grad_layer)

    return base

def ensure_block_cover_jit(cfg: dict, build_dir: str):
    out_file = cfg["cover_file"]
    b_idx = cfg["index"]
    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        return

    raw_art = os.path.join(build_dir, f"raw_block_{b_idx}.jpg")
    success = fetch_comic_artwork_landscape(cfg["prompt"], raw_art, block_index=b_idx)
    if success and os.path.exists(raw_art):
        base = Image.open(raw_art).convert("RGBA")
    else:
        print(f"     [Visual Warning] Fallback color card generated for Block {b_idx}", flush=True)
        base = Image.new("RGBA", (1920, 1080), (*cfg["fallback_color"], 255))

    base = apply_lower_third_vignette(base)
    base = stamp_four_corner_branding(base, build_dir)
    base = stamp_3d_metallic_flame_typography(base, cfg["title"])
    base.convert("RGB").save(out_file, "JPEG", quality=98)
    print(f"[{NOVEL_SLUG}] [Saved Visual] Block {b_idx} Cover: '{out_file}'", flush=True)

def create_dynamic_outro_slate(out_path: str, build_dir: str):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return
    base = Image.new("RGB", (1920, 1080), (18, 22, 32))
    base = apply_lower_third_vignette(base)
    base = stamp_four_corner_branding(base, build_dir)
    draw = ImageDraw.Draw(base)
    font_path = ensure_cinzel_font()
    head_font = ImageFont.truetype(font_path, 60)
    cta_font = ImageFont.truetype(font_path, 46)
    line1 = "CHAPTER 251 COMING SOON"
    line2 = "SUBSCRIBE FOR THE NEXT MARATHON"
    for i, txt in enumerate([line1, line2]):
        font = head_font if i == 0 else cta_font
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        x = (1920 - tw) // 2
        y = 480 + (i * 85)
        draw.text((x + 3, y + 4), txt, font=font, fill=(10, 12, 18, 255))
        draw.text((x, y), txt, font=font, fill=(255, 215, 100, 255) if i == 0 else (255, 255, 255, 255))
    base.convert("RGB").save(out_path, "JPEG", quality=95)

# ==================== AUDIO SYNTHESIS & CONCURRENCY ====================
async def synthesize_line_record(row: dict, out_file: str, sem: asyncio.Semaphore, max_retries: int = 5):
    if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
        return

    text = row.get("text", "").strip()
    if not text or not RE_ALPHANUM.search(text):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", out_file
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    voice, pitch, rate = row["voice"], row["pitch"], row["rate"]
    chunk_timeout = max(35.0, 25.0 + (len(text.split()) * 0.40))

    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                active_voice = voice
                if attempt >= 4:
                    active_voice = "en-US-GuyNeural" if row.get("gender") == "Male" else "en-US-JennyNeural"
                comm = edge_tts.Communicate(text, active_voice, pitch=pitch, rate=rate)
                await asyncio.wait_for(comm.save(out_file), timeout=chunk_timeout)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
                    return
            except Exception:
                pass
            if attempt == max_retries:
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", out_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            await asyncio.sleep((attempt * 1.5) + random.uniform(0.5, 1.5))

def get_audio_duration(file_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 0.5

def format_timestamp(seconds: float) -> str:
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def format_srt_time(seconds: float) -> str:
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

async def synthesize_chapter_task(ch_num: int, rows: list, title: str, build_dir: str, global_sem: asyncio.Semaphore):
    chapter_mp3 = os.path.join(build_dir, f"ch_{ch_num:03d}.mp3")
    chapter_meta = os.path.join(build_dir, f"ch_{ch_num:03d}_meta.json")
    if os.path.exists(chapter_mp3) and os.path.exists(chapter_meta):
        try:
            with open(chapter_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("duration", 0) > 5.0 and len(meta.get("relative_subtitles", [])) > 0:
                return ch_num, chapter_mp3, meta["duration"], meta["title"], meta["relative_subtitles"]
        except Exception:
            pass

    temp_dir = os.path.join(build_dir, f"temp_ch_{ch_num:03d}")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files, tasks = [], []
    for row in rows:
        c_path = os.path.join(temp_dir, f"seg_{row['line_id']}.mp3")
        chunk_files.append(c_path)
        tasks.append(synthesize_line_record(row, c_path, global_sem))

    await asyncio.gather(*tasks)

    valid_chunks = []
    rel_subtitles = []
    rel_time = 0.0
    for cf, row in zip(chunk_files, rows):
        if os.path.exists(cf) and os.path.getsize(cf) > 100:
            valid_chunks.append(cf)
            dur = get_audio_duration(cf)
            sub_text = f"[{row['speaker']}]: {row['text']}" if row.get("line_type") == "Dialogue" else row.get("text", "")
            rel_subtitles.append((rel_time, rel_time + dur, sub_text))
            rel_time += dur

    if not valid_chunks:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "3.0", "-q:a", "9", "-acodec", "libmp3lame", chapter_mp3
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        manifest_path = os.path.join(temp_dir, "manifest.txt")
        with open(manifest_path, "w", encoding="utf-8") as f:
            for cf in valid_chunks:
                f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest_path, "-c", "copy", chapter_mp3],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    final_dur = get_audio_duration(chapter_mp3)
    with open(chapter_meta, "w", encoding="utf-8") as f:
        json.dump({"title": title, "duration": final_dur, "relative_subtitles": rel_subtitles}, f)

    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    try: os.remove(os.path.join(temp_dir, "manifest.txt"))
    except OSError: pass
    try: os.rmdir(temp_dir)
    except OSError: pass

    print(f"[{NOVEL_SLUG}] [Synthesized Audio] {title} ({format_timestamp(final_dur)})", flush=True)
    return ch_num, chapter_mp3, final_dur, title, rel_subtitles

def assemble_multi_image_video(block_durations: dict, final_audio_path: str, output_video_path: str):
    """
    Multiplexes pre-generated Block images directly without triggering any regeneration.
    """
    print(f"\n[{NOVEL_SLUG}] Assembling Video Frames + Outro Card using pre-rendered images...", flush=True)
    video_segments = []
    for cfg in BLOCKS:
        b_idx = cfg["index"]
        dur = block_durations.get(b_idx, 0.0)
        if dur <= 0.1:
            dur = 60.0
        
        cover_path = os.path.join(BUILD_DIR, f"cover_block_{cfg['range'][0]}_{cfg['range'][1]}.jpg")
        if not os.path.exists(cover_path):
            ensure_block_cover_jit(cfg, BUILD_DIR)
            
        segment_video = os.path.join(BUILD_DIR, f"v_seg_block_{b_idx}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", f"{dur:.3f}",
            "-i", cover_path, "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", segment_video
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        video_segments.append(segment_video)

    outro_slate = os.path.join(BUILD_DIR, "outro_slate_card.jpg")
    if not os.path.exists(outro_slate):
        create_dynamic_outro_slate(outro_slate, BUILD_DIR)

    outro_seg = os.path.join(BUILD_DIR, "v_seg_outro.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", "15.000",
        "-i", outro_slate, "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", outro_seg
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    video_segments.append(outro_seg)

    v_manifest = os.path.join(BUILD_DIR, "v_segments_list.txt")
    with open(v_manifest, "w", encoding="utf-8") as f:
        for vs in video_segments:
            f.write(f"file '{os.path.abspath(vs).replace(os.sep, '/')}'\n")

    full_video_track = os.path.join(BUILD_DIR, "full_video_track.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_manifest, "-c", "copy", full_video_track], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", full_video_track, "-i", final_audio_path, "-c", "copy", "-movflags", "+faststart", "-shortest", output_video_path], check=True)

    for vs in video_segments:
        try: os.remove(vs)
        except OSError: pass
    try: os.remove(v_manifest)
    except OSError: pass
    try: os.remove(full_video_track)
    except OSError: pass

# ==================== MAIN EXECUTION ====================
async def main():
    os.makedirs(BUILD_DIR, exist_ok=True)
    print(f"=== Starting Global Rainstorm Air Fortress Marathon: Ch.{START_CHAPTER}–{END_CHAPTER} ===", flush=True)

    # ------------------ ASSET VALIDATION: COPY ALL 4 BRANDING OVERLAYS ------------------
    for key, filename in BRANDING_ASSETS.items():
        dst = os.path.join(BUILD_DIR, filename)
        if os.path.exists(filename):
            shutil.copy2(filename, dst)
            print(f"[Asset Sync] [✓] Copied '{filename}' into '{BUILD_DIR}'.", flush=True)
        elif os.path.exists(dst):
            print(f"[Asset Sync] [✓] Verified '{filename}' in '{BUILD_DIR}'.", flush=True)
        else:
            print(f"[Asset Sync Warning] '{filename}' missing in root. Fallback will be used if needed.", flush=True)

    gemini_client = None
    if GENAI_AVAILABLE and GEMINI_API_KEY:
        try:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            print("[Gemini Director] GenAI Client initialized successfully for demographic/emotion speech analysis.", flush=True)
        except Exception as e:
            print(f"[Gemini Director Notice] Initialization skipped: {e}", flush=True)

    char_map = dict(BASE_CHARACTERS)
    staged_chapters = []

    # ------------------ PHASE 1: SCRAPING & STAGING (DISK-CHECKPOINTED) ------------------
    print(f"\n[{NOVEL_SLUG}] [Phase 1/5] Staging & Scraping Chapters with Disk Checkpointing...", flush=True)
    with requests.Session() as session:
        curr_url = START_URL
        for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
            if not curr_url:
                break
            ch_json = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}_staged.json")
            
            if os.path.exists(ch_json):
                try:
                    with open(ch_json, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                    
                    if isinstance(cached_data, dict) and "rows" in cached_data:
                        rows = cached_data["rows"]
                        title = cached_data.get("title", f"Ch {ch_num:03d}")
                        cached_next = cached_data.get("next_url")
                        if cached_next:
                            curr_url = cached_next
                        else:
                            _, _, curr_url = scrape_chapter_content(session, curr_url, ch_num)
                    elif isinstance(cached_data, list):
                        rows = cached_data
                        title, _, curr_url = scrape_chapter_content(session, curr_url, ch_num)
                    
                    print(f"     [Stage Cached] Ch.{ch_num:03d} verified on disk ({len(rows)} segments)", flush=True)
                except Exception as e:
                    print(f"     [Stage Cache Reset] Re-scraping Ch.{ch_num:03d} due to notice: {e}", flush=True)
                    title, text, next_url = scrape_chapter_content(session, curr_url, ch_num)
                    rows = parse_chapter_via_gemini_director(gemini_client, title, text, char_map)
                    with open(ch_json, "w", encoding="utf-8") as f:
                        json.dump({"title": title, "rows": rows, "next_url": next_url}, f, indent=2, ensure_ascii=False)
                    curr_url = next_url
            else:
                title, text, next_url = scrape_chapter_content(session, curr_url, ch_num)
                rows = parse_chapter_via_gemini_director(gemini_client, title, text, char_map)
                
                with open(ch_json, "w", encoding="utf-8") as f:
                    json.dump({"title": title, "rows": rows, "next_url": next_url}, f, indent=2, ensure_ascii=False)
                
                print(f"     [✓ Saved Stage] Ch.{ch_num:03d} -> '{ch_json}' ({len(rows)} segments)", flush=True)
                curr_url = next_url

            staged_chapters.append((ch_num, rows, title))

    # ------------------ PHASE 2: VISUAL GENERATION ENGINE (EXECUTED UPFRONT) ------------------
    print(f"\n[{NOVEL_SLUG}] [Phase 2/5] Generating 10 Key Visual Block Covers & Outro Card UPFRONT...", flush=True)
    for cfg in BLOCKS:
        cfg["cover_file"] = os.path.join(BUILD_DIR, f"cover_block_{cfg['range'][0]}_{cfg['range'][1]}.jpg")
        ensure_block_cover_jit(cfg, BUILD_DIR)

    outro_slate = os.path.join(BUILD_DIR, "outro_slate_card.jpg")
    create_dynamic_outro_slate(outro_slate, BUILD_DIR)

    first_block_cover = BLOCKS[0]["cover_file"]
    if os.path.exists(first_block_cover) and not os.path.exists(COVER_IMAGE):
        try:
            shutil.copy2(first_block_cover, COVER_IMAGE)
            print(f"[{NOVEL_SLUG}] [✓] Primary Marathon Thumbnail Prepared: '{COVER_IMAGE}'", flush=True)
        except Exception:
            pass

    # ------------------ PHASE 3: AUDIO TTS SYNTHESIS ------------------
    print(f"\n[{NOVEL_SLUG}] [Phase 3/5] Synthesizing Audio Batches with Edge-TTS...", flush=True)
    global_sem = asyncio.Semaphore(GLOBAL_MAX_CONCURRENT_TTS)
    chapter_semaphore = asyncio.Semaphore(PARALLEL_CHAPTERS)

    async def run_chapter_bounded(cn, rw, tt):
        async with chapter_semaphore:
            return await synthesize_chapter_task(cn, rw, tt, BUILD_DIR, global_sem)

    all_results = []
    for b_idx in range(0, len(staged_chapters), BATCH_SIZE):
        batch = staged_chapters[b_idx:b_idx + BATCH_SIZE]
        batch_results = await asyncio.gather(*[run_chapter_bounded(cn, rw, tt) for cn, rw, tt in batch])
        all_results.extend(batch_results)

    all_results.sort(key=lambda x: x[0])
    chapter_files, chapter_durations, timestamps, all_subtitles = [], {}, [], []
    global_offset = 0.0

    for ch_num, mp3_path, dur, title, rel_subs in all_results:
        chapter_files.append(mp3_path)
        chapter_durations[ch_num] = dur
        timestamps.append(f"{format_timestamp(global_offset)} - {title}")
        for s_rel, e_rel, text in rel_subs:
            all_subtitles.append((format_srt_time(global_offset + s_rel), format_srt_time(global_offset + e_rel), text))
        global_offset += dur

    block_durations = {cfg["index"]: sum(chapter_durations.get(c, 0.0) for c in range(cfg["range"][0], cfg["range"][1] + 1)) for cfg in BLOCKS}

    with open(TIMESTAMPS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(timestamps))
    with open(SUBTITLES_FILE, "w", encoding="utf-8") as f:
        for idx, (s_time, e_time, text) in enumerate(all_subtitles, 1):
            f.write(f"{idx}\n{s_time} --> {e_time}\n{text}\n\n")

    # ------------------ PHASE 4: AUDIO MASTERING & NORMALIZATION ------------------
    print(f"\n[{NOVEL_SLUG}] [Phase 4/5] Audio Normalization (-14 LUFS)...", flush=True)
    raw_master_audio = os.path.join(BUILD_DIR, "raw_master.mp3")
    master_manifest = os.path.join(BUILD_DIR, "master_list.txt")
    with open(master_manifest, "w", encoding="utf-8") as f:
        for cf in chapter_files:
            f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", master_manifest, "-c", "copy", raw_master_audio], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_master_audio,
        "-af", "highpass=f=85,equalizer=f=3200:t=q:w=1.5:g=2.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50,loudnorm=I=-14:TP=-1.5:LRA=7,apad=pad_dur=15",
        "-c:a", "libmp3lame", "-b:a", "192k", FINAL_AUDIO
    ], check=True)

    # ------------------ PHASE 5: VIDEO MULTIPLEXING ------------------
    print(f"\n[{NOVEL_SLUG}] [Phase 5/5] Assembling Video Frames + Outro Card (Using Phase 2 Covers)...", flush=True)
    assemble_multi_image_video(block_durations, FINAL_AUDIO, FINAL_VIDEO)

    payload = {
        "snippet": {
            "title": VIDEO_TITLE,
            "description": f"{DESC_HEADER}{chr(10).join(timestamps)}{DESC_FOOTER}",
            "tags": TAGS,
            "categoryId": "24",
            "defaultLanguage": "en-US"
        },
        "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
        "assets": {
            "video_file": os.path.abspath(FINAL_VIDEO),
            "thumbnail_file": os.path.abspath(COVER_IMAGE),
            "subtitles_file": os.path.abspath(SUBTITLES_FILE),
            "timestamps_file": os.path.abspath(TIMESTAMPS_FILE)
        }
    }
    with open(PAYLOAD_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] SUCCESS: Production Pipeline Completed for Chapters 201-250! Video: {FINAL_VIDEO}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
