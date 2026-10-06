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

START_CHAPTER = 101
END_CHAPTER = 150
BATCH_SIZE = 5
PARALLEL_CHAPTERS = 2
GLOBAL_MAX_CONCURRENT_TTS = 3
MAX_NARRATION_MERGE_WORDS = 210
TARGET_DIALOGUE_CHUNK_WORDS = 65

CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"
LOGO_FILE = "logo.png"
REQUEST_TIMEOUT = 45

NOVEL_SLUG = "transforming-beasts-into-demons-the-beast-taming-immortal-clan-begins-as-hunters"
START_URL = "https://mtl-novel.com/novel/transforming-beasts-into-demons-the-beast-taming-immortal-clan-begins-as-hunters/chapter-101-executed-on-the-spot/"

BUILD_DIR = "build_transforming_beasts_101_150"
FINAL_AUDIO = "output_transforming_beasts_101_150.mp3"
FINAL_VIDEO = "final_transforming_beasts_101_150.mp4"
COVER_IMAGE = "cover_transforming_beasts_101_150.jpg"
TIMESTAMPS_FILE = "youtube_timestamps_transforming_beasts_101_150.txt"
SUBTITLES_FILE = "subtitles_transforming_beasts_101_150.srt"
PAYLOAD_FILE = "youtube_upload_payload_transforming_beasts_101_150.json"

VIDEO_TITLE = "EXECUTED ON THE SPOT! DEMON BEAST DYNASTY ASCENT [Ch 101-150] | Progression Fantasy Audiobook"
TAGS = [
    "Progression Fantasy", "Beast Taming", "Xianxia Audiobook",
    "Transforming Beasts Into Demons", "Immortal Clan", "Demon Beasts", 
    "Full Audiobook Marathon", "Being A Bong"
]

DESC_HEADER = (
    "Zhao Fangnian shatters the corrupt power structures of Linglan City!\n\n"
    "With corrupt constables and arrogant young masters executed on the spot, the Zhao Clan "
    "unleashes their blood-evolved demon beasts to claim supreme dominance over the Great Mountain wilderness.\n\n"
    "Welcome to Chapters 101 to 150 of 'Transforming Beasts Into Demons: The Beast Taming Immortal Clan Begins As Hunters' "
    "in full multi-voice dramatization!\n\n"
    "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
    "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, stele resonance, and martial directives).\n"
    "🎨 VISUAL ENGINE: 10 High-Contrast 4K Manhwa Visuals + 15s End-Card Outro with official branding.\n\n"
    "══════════════════════════════════════════════\nTIMESTAMPS:\n"
)

DESC_FOOTER = (
    "\n══════════════════════════════════════════════\n\n"
    "🌟 KEY ARC HIGHLIGHTS:\n"
    "• Ch 101: Executed on the Spot! No Mercy for Corrupt Officials\n"
    "• Ch 110: Xiao Hei's Shadow Wolf Bloodline Metamorphosis\n"
    "• Ch 120: Fortifying the Zhao Clan Mountain Estate\n"
    "• Ch 130: The Zhao Clan Subjugates Linglan City Trade Routes\n"
    "• Ch 140: Ancient Myriad Beast Stele Resonance & Grotto-Heaven Expansion\n"
    "• Ch 150: Sovereign Hunter Clan Ascent & Immortal Gate Shimmer\n\n"
    "══════════════════════════════════════════════\n"
    "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
    "All original novel concepts belong to the author. Subscribe for more!\n\n"
    "#ProgressionFantasy #Xianxia #BeastTaming #AudiobookMarathon #FullAudiobook #BeingABong"
)

GRADIENT_PALETTES = [
    ((255, 215, 100), (200, 50, 30)),
    ((150, 220, 255), (40, 100, 220)),
    ((255, 130, 220), (140, 30, 160)),
]

BLOCKS = [
    {
        "index": 1, "range": (101, 105),
        "title": ["EXECUTED ON THE SPOT", "IRON BLOOD RETRIBUTION", "Chapters 101 – 105"],
        "fallback_color": (35, 15, 20),
        "prompt": (
            "2D anime manhwa key visual, bold vector black ink linework, flat cel-shading. "
            "Protagonist hunter decapitating a corrupt martial magistrate in a public pavilion. "
            "Severed golden badges flying, dark blood arcs, crowd trembling in terror. Sharp contours, high contrast, no 3D CGI."
        )
    },
    {
        "index": 2, "range": (106, 110),
        "title": ["SHADOW WOLF SURGE", "NIGHT PACK AMBUSH", "Chapters 106 – 110"],
        "fallback_color": (20, 25, 35),
        "prompt": (
            "2D manhwa visual, bold vector outlines. "
            "Giant demonic black hound Xiao Hei with crimson glowing eyes tearing through enemy martial artists in a moonlit mountain pass. "
            "Electrified dark aura, crisp vector linework, sharp focus, no blur."
        )
    },
    {
        "index": 3, "range": (111, 115),
        "title": ["SPIRIT CROW SCOUTING", "AERIAL RECONNAISSANCE", "Chapters 111 – 115"],
        "fallback_color": (30, 20, 40),
        "prompt": (
            "2D manhwa illustration, flat cel-shading. "
            "Colorful spirit crow Xiao Cai radiating prismatic azure flames, circling above a fortified mountain stronghold. "
            "Protagonist giving orders from the cliffside. High saturation, sharp contours, no 3D CGI."
        )
    },
    {
        "index": 4, "range": (116, 120),
        "title": ["ZHAO CLAN GATHERING", "FORTIFYING THE ESTATE", "Chapters 116 – 120"],
        "fallback_color": (25, 35, 25),
        "prompt": (
            "2D manhwa key visual, bold black contours. "
            "Entire hunter clan assembled inside a fortified ancestral hall. Master Zhao Fangnian distributing high-tier demon pills to his sons. "
            "Ancient ancestral banners, deep shadows, crisp vector edges."
        )
    },
    {
        "index": 5, "range": (121, 125),
        "title": ["CITY LORD'S WRATH", "LINGLAN CITY CONFLICT", "Chapters 121 – 125"],
        "fallback_color": (40, 25, 15),
        "prompt": (
            "2D manhwa action scene, flat cel-shading. "
            "Grand City Lord of Linglan descending with golden broadswords, clashing against the protagonist's twin hunting spears at the city gates. "
            "Sparks flying, shattered flagstones, sharp contrast, razor-sharp focus."
        )
    },
    {
        "index": 6, "range": (126, 130),
        "title": ["DEMON TRIBULATION", "TIER BREAKTHROUGH", "Chapters 126 – 130"],
        "fallback_color": (15, 30, 45),
        "prompt": (
            "2D manhwa visual, flat cel-shading. "
            "Golden heavenly tribulation lightning striking a deep forest clearing where an enormous demonic beast roars in defiance. "
            "Dark purple clouds, razor-sharp outlines, no blur, no 3D CGI."
        )
    },
    {
        "index": 7, "range": (131, 135),
        "title": ["MERCHANT ROUTE CONTROL", "RIVAL SECTS PURGED", "Chapters 131 – 135"],
        "fallback_color": (35, 35, 20),
        "prompt": (
            "2D manhwa action scene, bold vector linework. "
            "Armed Zhao clan hunters leading heavily laden iron carts through conquered canyon roads. "
            "Slain rogue cultivators littering the roadside. Crisp linework, vibrant daylight, no 3D CGI."
        )
    },
    {
        "index": 8, "range": (136, 140),
        "title": ["MYRIAD BEAST STELE", "ANCESTRAL GLYPH RESIGN", "Chapters 136 – 140"],
        "fallback_color": (20, 40, 40),
        "prompt": (
            "2D anime manhwa key visual, bold vector outlines. "
            "Protagonist touching a colossal moss-covered ancient stele etched with glowing red beast silhouettes. "
            "Spirit resonance shockwaves shaking the grotto. High contrast, sharp vector art."
        )
    },
    {
        "index": 9, "range": (141, 145),
        "title": ["HUNTING DYNASTY", "EXPANDING TO THE MOUNTAINS", "Chapters 141 – 145"],
        "fallback_color": (45, 20, 30),
        "prompt": (
            "2D manhwa illustration, flat cel-shading. "
            "Thousands of tamed forest beasts organized in disciplined ranks beneath the Zhao Clan war flags. "
            "Protagonist overseeing from atop a tamed ape sovereign. Razor-sharp contours, high saturation."
        )
    },
    {
        "index": 10, "range": (146, 150),
        "title": ["SOVEREIGN HUNTER", "THE SECT ASCENT", "Chapters 146 – 150"],
        "fallback_color": (30, 20, 45),
        "prompt": (
            "2D anime manhwa climax illustration, Solo Leveling style. "
            "Master Zhao Fangnian standing on the highest peak of Linglan mountain at sunrise with his demon pets. "
            "Celestial immortal gates faintly shimmering in the clouds above. Crisp outlines, high detail, no 3D CGI."
        )
    }
]

BASE_CHARACTERS = {
    "narrator": {"display_name": "Narrator", "gender": "Male", "line_type": "Narration", "voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+5%"},
    "mc": {"display_name": "Zhao Fangnian", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+6%"},
    "wife": {"display_name": "Huang Wanyun", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-JennyNeural", "pitch": "+2Hz", "rate": "+6%"},
    "eldest_son": {"display_name": "Zhao Zhengze", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-AnaNeural", "pitch": "+5Hz", "rate": "+6%"},
    "second_son": {"display_name": "Zhao Zhengchuan", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-AnaNeural", "pitch": "+7Hz", "rate": "+6%"},
    "stele_system": {"display_name": "Myriad Beast Stele", "gender": "Synthetic", "line_type": "System", "voice": "en-US-SteffanNeural", "pitch": "-18Hz", "rate": "-6%"},
    "xiao_hei": {"display_name": "Xiao Hei", "gender": "Synthetic", "line_type": "Dialogue", "voice": "en-US-SteffanNeural", "pitch": "-14Hz", "rate": "+4%"},
    "xiao_cai": {"display_name": "Xiao Cai", "gender": "Synthetic", "line_type": "Dialogue", "voice": "en-US-SteffanNeural", "pitch": "-10Hz", "rate": "+6%"},
    "zhang_yidao": {"display_name": "Zhang Yidao", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-ChristopherNeural", "pitch": "-4Hz", "rate": "+4%"},
    "yang_qingzhou": {"display_name": "Yang Qingzhou", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-RogerNeural", "pitch": "-6Hz", "rate": "+2%"},
    "constable_li": {"display_name": "Constable Li", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-EricNeural", "pitch": "+2Hz", "rate": "+6%"},
    "arrogant_scion": {"display_name": "Arrogant Scion", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-EricNeural", "pitch": "+6Hz", "rate": "+10%"},
    "city_lord": {"display_name": "City Lord", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-RogerNeural", "pitch": "-6Hz", "rate": "+2%"}
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
        cleaned = f"Demon Beast Clan Ascent {ch_num}"
    return f"Ch {ch_num:02d}: {cleaned.title()}"

# ==================== TEXT PROCESSING & SCRAPING ====================
RE_SYSTEM = re.compile(r"(?:\[|【|〔|『|〖|［)(Ding!|Stele|System|Notice|Warning|Announcement|Prompt|Bloodline|Resonance).*?(?:\]|】|〕|』|〗|］)", re.I)
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
    print(f"[{NOVEL_SLUG}] Connecting to Ch.{ch_num:02d}: {url}", flush=True)
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
        paragraphs = [f"Chapter {ch_num}. In the wilderness outside Linglan City, the Zhao Clan prepares their demon beasts."]

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
Analyze the chapter text, cleanly separating exposition/narration from spoken dialogue and ancient stele prompts.
For every segment:
1. Identify the speaker (Zhao Fangnian, Huang Wanyun, Zhao Zhengze, Zhao Zhengchuan, Xiao Hei, Xiao Cai, Zhang Yidao, Constable Li, City Lord, Arrogant Scion, Myriad Beast Stele, or Narrator).
2. Determine gender ('Male', 'Female', 'Neutral') and age bracket ('young', 'teen', 'middle-aged', 'elder', 'n/a').
3. Detect dominant emotion ('angry', 'fearful', 'sarcastic', 'neutral', 'excited', 'solemn').
4. Assign optimal voice:
   - Narrator (Male): 'en-US-GuyNeural'
   - Zhao Fangnian / Clan Head: 'en-US-GuyNeural'
   - Huang Wanyun / Wife: 'en-US-JennyNeural'
   - Zhao Zhengze / Zhao Zhengchuan (Sons): 'en-US-AnaNeural'
   - Myriad Beast Stele / Demon Pets: 'en-US-SteffanNeural'
   - Constable Li / Scions: 'en-US-EricNeural'
   - City Lord / Masters: 'en-US-RogerNeural'
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
        print(f"     [Gemini Director Error] {e}. Falling back to rule-based staging...", flush=True)

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
            role_key = "stele_system" if line_type == "System" else "narrator"
            staged_segments.append({"role_key": role_key, "line_type": line_type, "text": token["text"]})
        else:
            prev_narr = ""
            for back_idx in range(idx - 1, -1, -1):
                if not raw_tokens[back_idx]["is_quote"]:
                    prev_narr = raw_tokens[back_idx]["text"][-85:]
                    break
            
            p_low = prev_narr.lower()
            if any(w in p_low for w in ["wife", "wanyun", "mother", "mom", "she", "her"]):
                role_key = "wife"
            elif any(w in p_low for w in ["zhengze", "eldest son", "big brother"]):
                role_key = "eldest_son"
            elif any(w in p_low for w in ["zhengchuan", "second son", "younger brother"]):
                role_key = "second_son"
            elif any(w in p_low for w in ["xiao hei", "black dog", "wolf"]):
                role_key = "xiao_hei"
            elif any(w in p_low for w in ["xiao cai", "crow"]):
                role_key = "xiao_cai"
            elif any(w in p_low for w in ["constable", "officer li"]):
                role_key = "constable_li"
            elif any(w in p_low for w in ["young master", "scion", "wang", "pockmark"]):
                role_key = "arrogant_scion"
            elif any(w in p_low for w in ["city lord", "lord linglan"]):
                role_key = "city_lord"
            elif any(w in p_low for w in ["zhang yidao", "butcher"]):
                role_key = "zhang_yidao"
            elif any(w in p_low for w in ["head yang", "master yang"]):
                role_key = "yang_qingzhou"
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
        except Exception as e:
            print(f"     [Visual Engine] Cloudflare notice: {e}. Routing to Pollinations fallback...")

    print(f"     [Visual Engine] Triggering Pollinations Fallback for Block {block_index}...", flush=True)
    encoded = urllib.parse.quote(clean_p)
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
            return True
    except Exception:
        pass
    return False

def apply_lower_third_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(overlay)
    vig_start = int(height * 0.82)
    for y in range(vig_start, height):
        alpha = int(75 * (((y - vig_start) / (height - vig_start)) ** 1.3))
        v_draw.line([(0, y), (width, y)], fill=(12, 18, 35, alpha))
    return Image.alpha_composite(base.convert("RGBA"), overlay)

def stamp_channel_watermark(base: Image.Image, build_dir: str) -> Image.Image:
    """
    Stamps the Being A Bong branding logo strictly into the top-left corner.
    Loads logo.png directly from the build directory to ensure exact scale and alpha composite.
    """
    build_logo = os.path.join(build_dir, LOGO_FILE)
    if os.path.exists(LOGO_FILE) and not os.path.exists(build_logo):
        try:
            shutil.copy2(LOGO_FILE, build_logo)
        except Exception:
            pass

    active_logo_path = build_logo if os.path.exists(build_logo) else (LOGO_FILE if os.path.exists(LOGO_FILE) else None)
    if active_logo_path:
        try:
            logo_img = Image.open(active_logo_path).convert("RGBA")
            target_width = 320
            w_percent = target_width / float(logo_img.size[0])
            target_height = int(float(logo_img.size[1]) * w_percent)
            logo_resized = logo_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            if base.mode != "RGBA":
                base = base.convert("RGBA")
            
            base.paste(logo_resized, (35, 35), mask=logo_resized.split()[3])
            return base
        except Exception as e:
            print(f"[Watermark] Failed pasting logo image: {e}", flush=True)

    # Clean Fallback
    draw = ImageDraw.Draw(base)
    wx, wy = 55, 45
    crest_r = 22
    draw.ellipse([(wx - crest_r, wy - crest_r), (wx + crest_r, wy + crest_r)], fill=(225, 150, 40, 255), outline=(255, 245, 220, 255), width=2)
    name_fp = "C:/Windows/Fonts/arialbd.ttf"
    if not os.path.exists(name_fp):
        name_fp = ensure_cinzel_font()
    name_font = ImageFont.truetype(name_fp, 36)
    handle_font = ImageFont.truetype(name_fp, 22)
    tx = wx + 36
    draw.text((tx + 2, wy - 18 + 2), "Being a Bong", fill=(20, 15, 10, 255), font=name_font)
    draw.text((tx, wy - 18), "Being a Bong", fill=(255, 255, 255, 255), font=name_font)
    draw.text((tx + 1, wy + 20 + 1), "@beingabong", fill=(20, 15, 10, 220), font=handle_font)
    draw.text((tx, wy + 20), "@beingabong", fill=(255, 215, 100, 255), font=handle_font)
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
    width, height = base.size
    font_path = ensure_cinzel_font()
    title_font = ImageFont.truetype(font_path, 60)
    sub_font = ImageFont.truetype(font_path, 46)
    line_spacing = 76
    total_text_h = (len(lines) - 1) * line_spacing + 60
    start_y = int(height * 0.81) - (total_text_h // 2)

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else title_font
        bbox = ImageDraw.Draw(base).textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)
        ImageDraw.Draw(base).text((x + 3, y + 4), line, font=active_font, fill=(15, 20, 30, 255), stroke_width=5, stroke_fill=(15, 20, 30, 255))
        ImageDraw.Draw(base).text((x, y), line, font=active_font, fill=(30, 45, 60, 255), stroke_width=3, stroke_fill=(30, 45, 60, 255))
        palette = GRADIENT_PALETTES[min(i, len(GRADIENT_PALETTES) - 1)]
        grad_layer = create_vertical_gradient_text_mask(text_w + 20, text_h + 20, line, active_font, palette[0], palette[1])
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
        base = Image.new("RGBA", (1920, 1080), (*cfg["fallback_color"], 255))

    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base, build_dir)
    base = stamp_3d_metallic_flame_typography(base, cfg["title"])
    base.convert("RGB").save(out_file, "JPEG", quality=98)
    print(f"[{NOVEL_SLUG}] [Saved Visual] Block {b_idx} Cover: '{out_file}'", flush=True)

def create_dynamic_outro_slate(out_path: str, build_dir: str):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return
    base = Image.new("RGB", (1920, 1080), (18, 22, 32))
    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base, build_dir)
    draw = ImageDraw.Draw(base)
    font_path = ensure_cinzel_font()
    head_font = ImageFont.truetype(font_path, 54)
    cta_font = ImageFont.truetype(font_path, 42)
    line1 = "CHAPTER 151 COMING SOON"
    line2 = "SUBSCRIBE FOR THE NEXT MARATHON"
    for i, txt in enumerate([line1, line2]):
        font = head_font if i == 0 else cta_font
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        x = (1920 - tw) // 2
        y = 480 + (i * 80)
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
    print(f"\n[{NOVEL_SLUG}] Assembling Video Frames + Outro Card into Final Master Video...", flush=True)
    video_segments = []
    for cfg in BLOCKS:
        b_idx = cfg["index"]
        dur = block_durations.get(b_idx, 0.0)
        if dur <= 0.1:
            dur = 60.0
        cfg["cover_file"] = os.path.join(BUILD_DIR, f"cover_block_{cfg['range'][0]}_{cfg['range'][1]}.jpg")
        ensure_block_cover_jit(cfg, BUILD_DIR)
        segment_video = os.path.join(BUILD_DIR, f"v_seg_block_{b_idx}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", f"{dur:.3f}",
            "-i", cfg["cover_file"], "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", segment_video
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        video_segments.append(segment_video)

    outro_slate = os.path.join(BUILD_DIR, "outro_slate_card.jpg")
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
    print(f"=== Starting Demon Beast Taming Marathon: Ch.{START_CHAPTER}–{END_CHAPTER} ===", flush=True)

    # ------------------ ASSET VALIDATION: COPY LOGO IMMEDIATELY ------------------
    build_logo_path = os.path.join(BUILD_DIR, LOGO_FILE)
    if os.path.exists(LOGO_FILE):
        shutil.copy2(LOGO_FILE, build_logo_path)
        print(f"[Asset Sync] [✓] Copied '{LOGO_FILE}' directly into '{BUILD_DIR}' for top-left branding.", flush=True)
    elif os.path.exists(build_logo_path):
        print(f"[Asset Sync] [✓] Verified '{LOGO_FILE}' already present in '{BUILD_DIR}'.", flush=True)
    else:
        print(f"[Asset Sync Warning] '{LOGO_FILE}' not found in root. Watermark fallback typography will be used.", flush=True)

    gemini_client = None
    if GENAI_AVAILABLE and GEMINI_API_KEY:
        try:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            print("[Gemini Director] GenAI Client initialized successfully for demographic/emotion speech analysis.", flush=True)
        except Exception as e:
            print(f"[Gemini Director Notice] Initialization skipped: {e}", flush=True)

    char_map = dict(BASE_CHARACTERS)
    staged_chapters = []

    # ------------------ PHASE 1: SCRAPING & STAGING ------------------
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
                        title = cached_data.get("title", f"Ch {ch_num:02d}")
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

    # ------------------ PHASE 2: VISUAL GENERATION ENGINE ------------------
    print(f"\n[{NOVEL_SLUG}] [Phase 2/5] Generating 10 Key Visual Block Covers & Outro Card...", flush=True)
    for cfg in BLOCKS:
        cfg["cover_file"] = os.path.join(BUILD_DIR, f"cover_block_{cfg['range'][0]}_{cfg['range'][1]}.jpg")
        ensure_block_cover_jit(cfg, BUILD_DIR)

    outro_slate = os.path.join(BUILD_DIR, "outro_slate_card.jpg")
    create_dynamic_outro_slate(outro_slate, BUILD_DIR)

    first_block_cover = BLOCKS[0]["cover_file"]
    if os.path.exists(first_block_cover) and not os.path.exists(COVER_IMAGE):
        try:
            shutil.copy2(first_block_cover, COVER_IMAGE)
            print(f"[{NOVEL_SLUG}] Primary Marathon Thumbnail Prepared: '{COVER_IMAGE}'", flush=True)
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
    print(f"\n[{NOVEL_SLUG}] [Phase 5/5] Assembling Video Frames + Outro Card...", flush=True)
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

    print(f"\n[✓] SUCCESS: Production Pipeline Completed for Chapters 101-150! Video: {FINAL_VIDEO}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
