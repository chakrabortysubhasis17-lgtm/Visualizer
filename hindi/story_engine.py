import argparse
import asyncio
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import warnings

warnings.filterwarnings("ignore")

# Force UTF-8 streams on Windows to prevent Devanagari encoding crashes
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import edge_tts
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import errors, types
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Global Settings & Seed Glossary
# ---------------------------------------------------------------------------
DEFAULT_URL = "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-1-entry-system-water-and-wood-spiritual-roots/"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LDLGssoorHQXPt6Zgn3AWmaWk2yH8JK2PH6WmtPpdD7w")

BLOCK_SIZE = 10
COOLDOWN_SECONDS = 45

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.7",
}

FULLWIDTH_TO_ASCII = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '「': '"', '」': '"',
    '，': ', ', '。': '. ', '！': '! ', '？': '? ',
    '：': ': ', '；': '; ', '（': '(', '）': ')'
})

WATERMARK_PATTERNS = [
    re.compile(r"\(End of this chapter\)", re.I),
    re.compile(r"Please visit mtl-novel\.com.*", re.I),
    re.compile(r"Check out our latest novel.*", re.I),
    re.compile(r"\[TL Note:.*?\]", re.I),
    re.compile(r"https?://\S+", re.I),
    re.compile(r"【?\s*Brain Storage\s*】?", re.I),
    re.compile(r"【?\s*Please come in, dear readers\.?\s*】?", re.I)
]

RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')

# Verified baseline seed glossary to guarantee character & clan continuity
SEED_GLOSSARY = {
    "Li Qing": {
        "indianized": "Rudra",
        "devanagari": "रुद्र",
        "category": "character"
    },
    "Qing'er": {
        "indianized": "Rudra",
        "devanagari": "रुद्र",
        "category": "character"
    },
    "Li Canghai": {
        "indianized": "Grandfather Devvrat",
        "devanagari": "दादाजी देवव्रत",
        "category": "character"
    },
    "Grand Elder Li": {
        "indianized": "Grand Elder Devvrat",
        "devanagari": "ग्रैंड एल्डर देवव्रत",
        "category": "character"
    },
    "Li Tianheng": {
        "indianized": "Clan Leader Rishabh",
        "devanagari": "कुल प्रमुख ऋषभ",
        "category": "character"
    },
    "Li Family": {
        "indianized": "Suryakul Clan",
        "devanagari": "सूर्यकुल",
        "category": "faction"
    },
    "Li Clan": {
        "indianized": "Suryakul Clan",
        "devanagari": "सूर्यकुल",
        "category": "faction"
    },
    "Canglan Prefecture": {
        "indianized": "Neelanchal Province",
        "devanagari": "नीलांचल प्रांत",
        "category": "location"
    },
    "Tainan Mountains": {
        "indianized": "Dakshingiri Mountains",
        "devanagari": "दक्षिणगिरि पर्वतमाला",
        "category": "location"
    },
    "Myriad Things Entry System": {
        "indianized": "Sarvatra Gunank Pranali",
        "devanagari": "सर्वत्र गुणांक प्रणाली",
        "category": "artifact"
    }
}

BLOCK_CONFIGS = [
    {
        "index": 1,
        "prompt": (
            "Breathtaking 16:9 anime manhwa key visual of handsome 18-year-old Indian male cultivator Rudra. "
            "Warm wheatish skin, sharp South Asian facial features, messy dark warrior hair tied in a half-knot. "
            "Wearing dark royal blue silk angavastram draped over charcoal armored robes etched with golden Vedic sun motifs and copper arm bracers. "
            "Standing in an ancient sandstone Indian sun-temple courtyard with carved stone pillars and sacred banyan trees at sunrise. "
            "Floating translucent golden and purple holographic UI status panels hover before him with glowing Devanagari glyphs. "
            "Volumetric golden morning sunlight, prana dust particles, 8k resolution, cinematic manhwa aesthetic."
        ),
        "title": ["AWAKENING THE ENTRY SYSTEM", "DEVVRAT'S FATAL DEBUFF", "Chapters 1 – 10"],
        "fallback_color": (30, 160, 110)
    },
    {
        "index": 2,
        "prompt": (
            "Vibrant 16:9 widescreen fantasy anime visual. Handsome young Indian male cultivator Rudra with wheatish brown skin "
            "quietly meditating in full lotus posture inside an ancient subterranean Himalayan spirit cavern. "
            "Radiant emerald and azure Water-Wood prana energy swirling around his body, synthesizing glowing purple celestial trait orbs. "
            "Ancient Sanskrit talisman mantras carved into glowing crystal stalactites. "
            "Cinematic high fantasy, rim lighting, sharp anime line art, 8k resolution."
        ),
        "title": ["SYNTHESIZING PURPLE TRAITS", "CONCEALING SACRED PRANA", "Chapters 11 – 20"],
        "fallback_color": (140, 70, 210)
    },
    {
        "index": 3,
        "prompt": (
            "Dramatic 16:9 cinematic anime still. Young Indian cultivator Rudra channeling pure azure healing prana "
            "into a dignified, elderly Indian clan patriarch, Devvrat. "
            "The elder has weathered Indian warrior features, long white beard, wearing sage-gray ashram robes and sacred rudraksha beads. "
            "Set inside a grand sandstone royal darbar hall with ancient Indian architectural stone carvings. "
            "Sinister crimson fire-poison aura being extracted and dissolving into dark smoke. Dramatic cinematic anime lighting, 8k."
        ),
        "title": ["PURGING THE FIRE POISON", "SAVING PATRIARCH DEVVRAT", "Chapters 21 – 30"],
        "fallback_color": (210, 50, 40)
    },
    {
        "index": 4,
        "prompt": (
            "Epic 16:9 manhwa splash art. Young Indian protagonist Rudra standing in a bustling sandstone martial temple plaza under blazing sunlight. "
            "Observing passing Indian warrior disciples and prodigies, seeing towering vertical pillars of blinding golden fate and karma rising into the clouds. "
            "Rudra's eyes glow with divine perception as translucent golden trait cards float in mid-air. "
            "Vivid colors, sovereign Indian cultivation fantasy, highly detailed, 8k resolution."
        ),
        "title": ["CHILDREN OF DESTINY", "EXTRACTING GOLDEN TRAITS", "Chapters 31 – 40"],
        "fallback_color": (245, 190, 45)
    },
    {
        "index": 5,
        "prompt": (
            "Breathtaking 16:9 anime climax illustration. Indian cultivator Rudra levitating high above the grand carved stone gates of the Suryakul fortress. "
            "Billowing royal silk robes, sharp wheatish Indian facial features, commanding twin soaring spiritual dragons made of pure water and wood prana, "
            "while golden celestial lightning strikes around him. Enemy armies below recoil in awe. "
            "Sunset crimson sky, cinematic scale, high-octane webtoon climax illustration, 8k resolution."
        ),
        "title": ["SURYAKUL CLAN DOMINANCE", "FOUNDATION BREAKTHROUGH", "Chapters 41 – 50"],
        "fallback_color": (20, 140, 230)
    }
]

# ---------------------------------------------------------------------------
# Structured Schemas for Gemini Localization
# ---------------------------------------------------------------------------
class EntityItem(BaseModel):
    original_term: str = Field(description="Original Chinese/English entity name (e.g. 'Wang Clan', 'Spirit Void Sect')")
    indianized_name: str = Field(description="Heroic Indianized name (e.g. 'Nagvanshi Kul', 'Shunya Sampraday')")
    devanagari_tts: str = Field(description="Strict Devanagari script for speech synthesis (e.g. 'नागवंशी कुल', 'शून्य संप्रदाय')")
    category: str = Field(description="'character', 'faction', 'location', or 'artifact'")

class ChapterLine(BaseModel):
    speaker: str = Field(description="Speaker in Devanagari script (e.g. 'रुद्र', 'दादाजी देवव्रत', 'Narrator', 'System')")
    line_type: str = Field(description="'Narration', 'Dialogue', or 'System'")
    text: str = Field(description="Strictly Devanagari Hindi text. Zero Latin letters.")

class LocalizedPayload(BaseModel):
    chapter_number: int
    title: str
    new_entities_discovered: list[EntityItem]
    lines: list[ChapterLine]

# ---------------------------------------------------------------------------
# Stage 1: Web Scraper & DOM Cleaner
# ---------------------------------------------------------------------------
def extract_story_slug(url: str) -> str:
    match = re.search(r'/novel/([^/]+)/', url)
    return match.group(1) if match else "entry-cultivation-i-can-copy-entries"

def clean_and_normalize_text(text: str) -> str:
    cleaned = text.translate(FULLWIDTH_TO_ASCII)
    cleaned = re.sub(r"^(\s*[*~=_#-]\s*){3,}$", "", cleaned, flags=re.MULTILINE)
    for pat in WATERMARK_PATTERNS:
        cleaned = pat.sub("", cleaned)
    return re.sub(r"[ \t]+", " ", cleaned).strip()

def scrape_chapter_content(session: requests.Session, url: str, novel_slug: str) -> tuple[str, str, str | None]:
    resp = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    title = clean_and_normalize_text(h1.get_text(strip=True)) if h1 else "Untitled Chapter"

    article = soup.find("article")
    if not article:
        article = (
            soup.select_one("div.chapter-content")
            or soup.select_one("div.entry-content")
            or soup.select_one("div#chapter-content")
            or soup.select_one("div.read-container")
        )
    if not article:
        raise ValueError(f"Target article container missing at: {url}")

    paragraphs = [clean_and_normalize_text(p.get_text(strip=True)) for p in article.find_all("p")]
    paragraphs = [p for p in paragraphs if p and RE_ALPHANUM.search(p)]
    full_text = f"{title}.\n\n" + "\n\n".join(paragraphs)

    next_url = None
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True).lower()
        if "next" in t or "»" in t or "next chapter" in t:
            if novel_slug in a["href"]:
                next_url = urllib.parse.urljoin(url, a["href"])
                break

    return title, full_text, next_url

def print_progress_bar(current: int, total: int, prefix: str = "", bar_length: int = 30):
    fraction = current / total
    filled = int(bar_length * fraction)
    bar = "█" * filled + "░" * (bar_length - filled)
    percent = int(fraction * 100)
    sys.stdout.write(f"\r{prefix} |{bar}| {percent:3d}% ({current:02d}/{total:02d})")
    sys.stdout.flush()

def pre_scrape_all_chapters(start_ch: int, end_ch: int, initial_url: str, dir_raw: str, url_index_path: str, novel_slug: str):
    print(f"\n==================================================")
    print(f"  STEP 1: PRE-SCRAPING ALL {end_ch - start_ch + 1} EPISODES TO LOCAL")
    print(f"==================================================")

    url_index = load_json_file(url_index_path, {})
    current_url = url_index.get(str(start_ch), initial_url)
    total_chapters = end_ch - start_ch + 1

    with requests.Session() as session:
        for idx, ch_num in enumerate(range(start_ch, end_ch + 1), start=1):
            raw_file = os.path.join(dir_raw, f"ch_{ch_num:03d}.txt")

            if os.path.exists(raw_file) and os.path.getsize(raw_file) > 200:
                print_progress_bar(idx, total_chapters, prefix="[Scraper Cache]")
                if str(ch_num + 1) in url_index:
                    current_url = url_index[str(ch_num + 1)]
                continue

            if not current_url:
                sys.exit(f"\n[Scraper Error] Could not determine URL for Chapter {ch_num}.")

            print_progress_bar(idx, total_chapters, prefix=f"[Scraping Ch {ch_num:03d}]")
            title, raw_text, next_url = scrape_chapter_content(session, current_url, novel_slug)

            with open(raw_file, "w", encoding="utf-8") as f:
                f.write(raw_text)

            url_index[str(ch_num)] = current_url
            if next_url:
                url_index[str(ch_num + 1)] = next_url
            save_json_file(url_index_path, url_index)

            current_url = next_url
            time.sleep(1.0)

    print("\n[Done] Step 1 Complete: All raw chapter files cached locally!\n")

# ---------------------------------------------------------------------------
# Storage & Text Utilities
# ---------------------------------------------------------------------------
def load_json_file(path: str, default: dict) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json_file(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_glossary(glossary_path: str, existing: dict, new_discoveries: list[EntityItem]) -> dict:
    updated = False
    for entity in new_discoveries:
        key = entity.original_term.strip()
        dev = entity.devanagari_tts.strip()

        # Reject any Chinese phonetic transliterations from entering persistent memory
        if any(bad in dev for bad in ["ली ", "चिंग", "चांगहाई", "तियान", "चांगलान", "ताइनान", "वांग"]):
            continue

        if key and key not in existing:
            existing[key] = {
                "indianized": entity.indianized_name.strip(),
                "devanagari": dev,
                "category": entity.category.strip()
            }
            updated = True
            print(f"      [Glossary +] '{key}' -> '{dev}' ({entity.category})")

    if updated or not os.path.exists(glossary_path):
        save_json_file(glossary_path, existing)

    return existing

def get_scoped_glossary(raw_text: str, full_glossary: dict) -> dict:
    """Optimizes API prompt token size: includes core seed plus entities found in text."""
    scoped = {k: v for k, v in full_glossary.items() if k in SEED_GLOSSARY}
    raw_lower = raw_text.lower()
    for orig_term, data in full_glossary.items():
        if orig_term.lower() in raw_lower:
            scoped[orig_term] = data
    return scoped

def sanitize_for_tts(text: str) -> str:
    text = re.sub(r'\.\s*', '। ', text)
    text = re.sub(r'\b[A-Za-z]+\b', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def compact_lines_for_tts(lines: list[dict], max_words: int = 180) -> list[dict]:
    """Merges adjacent narration lines to minimize TTS chunk overhead and audio seams."""
    compacted = []
    for line in lines:
        if (
            compacted
            and compacted[-1]["speaker"] == "Narrator"
            and line.get("speaker") == "Narrator"
            and compacted[-1]["line_type"] == "Narration"
            and line.get("line_type") == "Narration"
        ):
            combined = compacted[-1]["text"] + " " + line["text"]
            if len(combined.split()) <= max_words:
                compacted[-1]["text"] = combined
                continue
        compacted.append(dict(line))
    return compacted

# ---------------------------------------------------------------------------
# Step 2: Gemini Localization Engine (Lookup -> Invent -> Persist)
# ---------------------------------------------------------------------------
def localize_chapter(raw_text: str, ch_num: int, glossary_path: str, current_glossary: dict) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)
    active_glossary = get_scoped_glossary(raw_text, current_glossary)

    system_instruction = f"""
You are the creative director of a premium Indian anime and web novel audio drama studio.
Your task is to adapt this Chinese Xianxia novel into an authentic Indian cultural localization written strictly in Devanagari script.

CORE MANDATE: 100% INDIANIZED PROPER NOUN SUBSTITUTION
Every single proper noun—Character, Clan, Sect, Kingdom, Empire, City, Mountain, River, or Relic—MUST be given an Indian/Sanskritic name.
Under NO circumstances should any Chinese, East-Asian, or foreign phonetic name remain (DO NOT write 'ली', 'चिंग', 'वांग', 'चांग', 'हान', etc.).

TWO-STEP ENTITY RESOLUTION:
1. STEP 1 (LOOKUP EXISTING GLOSSARY): Check this CURRENT PERSISTENT GLOSSARY:
{json.dumps(active_glossary, ensure_ascii=False, indent=2)}
If an entity exists in the glossary above, you MUST use the exact Indian name specified.

2. STEP 2 (INVENT & REGISTER NEW ENTITIES): If an entity is NOT in the glossary:
   - Invent a heroic, evocative Indian/Sanskritic equivalent based on its narrative role:
     * Protagonist / Ally / Rival -> Heroic Indian personal name (e.g. रुद्र, विक्रांत, शौर्य, देवराज, भास्कर, भैरव, चिन्मय).
     * Clan / Family -> Indian Kul / Vansh (e.g. सूर्यकुल, नागवंशी, चंद्रवंशी, रघुवंशी).
     * Sect / School / Faction -> Sampraday / Akhada / Math (e.g. शून्यसंन्यास संप्रदाय, नीलमेघ अखाड़ा).
     * Kingdom / Empire / Country -> Indic Rajya / Samrajya (e.g. आर्यावर्त, गंधर्व साम्राज्य, कलिंग राज्य).
     * Mountain / River / Province -> Indic Geography (e.g. दक्षिणगिरि, नीलांचल, अमरकंटक).
     * Cultivation Relic / Technique -> Indic Shastra / Vidya / Mani (e.g. दिव्य स्फटिक, मूल जलतत्व विद्या).
   - Register every single newly coined term in 'new_entities_discovered' so it is saved to the persistent glossary.

3. SCRIPT & SYSTEM TERMINOLOGY:
   - ZERO LATIN CHARACTERS: Every word must be written in Devanagari script.
   - Gaming loanwords stay conversational but written in Devanagari (सिस्टम, लेवल, डिबफ़, स्पिरिट रूट, कल्टिवेशन).
   - System prompts enclosed in full-width brackets 【...】.
   - Numbers and tiers written out as Hindi words ('तीसरा चरण', 'तीन साल', 'दो सौ परसेंट').
   - Keep dialogue high-tension and cinematic.
"""

    model_candidates = [
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
    ]
    response = None

    for model_name in model_candidates:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=f"Localize Chapter {ch_num}:\n\n{raw_text}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=LocalizedPayload,
                    temperature=0.2,
                ),
            )
            break
        except (errors.ServerError, errors.APIError) as e:
            err = e.message if hasattr(e, "message") else str(e)
            print(f"      [{model_name} busy]: {err}. Retrying in 4s...")
            time.sleep(4)

    if not response or not response.text:
        raise RuntimeError(f"Localization failed for Chapter {ch_num}")

    payload = json.loads(response.text)
    update_glossary(glossary_path, current_glossary, [EntityItem(**item) for item in payload.get("new_entities_discovered", [])])

    for line in payload["lines"]:
        line["text"] = sanitize_for_tts(line["text"])

    payload["lines"] = compact_lines_for_tts(payload["lines"])
    return payload

# ---------------------------------------------------------------------------
# Step 3: Pure Pillow Visual & Tactical Typography Engine
# ---------------------------------------------------------------------------
def fetch_image_safe(prompt: str, out_path: str, width: int = 1280, height: int = 720) -> bool:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 3000:
        return True
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1000, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
        if resp.status_code == 200 and len(resp.content) > 3000:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False

def build_celestial_atmosphere_canvas(width: int, height: int, tint_color: tuple) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (12, 14, 18, 255))
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    cx, cy = width // 2, int(height * 0.45)
    max_r = int(height * 0.75)
    for r in range(max_r, 0, -12):
        factor = 1.0 - (r / max_r)
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(*tint_color, int(90 * factor)))

    for radius in [180, 290, 410]:
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(255, 230, 140, 160), width=2)

    return Image.alpha_composite(canvas, glow)

def stamp_tactical_typography(base: Image.Image, lines: list) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    band_top, band_bottom = int(height * 0.32), int(height * 0.70)
    for y in range(band_top, band_bottom):
        dist = min(y - band_top, band_bottom - y)
        d_over.line([(0, y), (width, y)], fill=(8, 10, 14, min(140, int(dist * 1.8))))

    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    draw.rectangle([(50, 50), (width - 50, height - 50)], outline=(40, 55, 45, 220), width=2)
    draw.rectangle([(64, 64), (width - 64, height - 64)], outline=(180, 150, 60, 180), width=1)

    c = 40
    corners = [
        ((64, 64), (64 + c, 64), (64, 64 + c)),
        ((width - 64, 64), (width - 64 - c, 64), (width - 64, 64 + c)),
        ((64, height - 64), (64 + c, height - 64), (64, height - 64 - c)),
        ((width - 64, height - 64), (width - 64 - c, height - 64), (width - 64, height - 64 - c))
    ]
    for orig, h_pt, v_pt in corners:
        draw.line([orig, h_pt], fill=(245, 215, 90, 255), width=3)
        draw.line([orig, v_pt], fill=(245, 215, 90, 255), width=3)

    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    font = None
    sub_font = None
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

    line_spacing = 92
    total_text_h = (len(lines) - 1) * line_spacing + 50
    start_y = (height - total_text_h) // 2

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else font
        bbox = draw.textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)

        draw.text((x + 4, y + 4), line, fill=(0, 0, 0, 245), font=active_font)
        fill_col = (245, 220, 160) if i == len(lines) - 1 else (255, 252, 245)
        draw.text((x, y), line, fill=fill_col, font=active_font)

    return base

def ensure_block_cover_jit(block_idx: int, start_ch: int, end_ch: int, part_tag: str, art_dir: str):
    out_file = os.path.join(art_dir, f"{part_tag}_block_{block_idx:02d}_ch{start_ch:03d}_{end_ch:03d}.png")
    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        return out_file

    cfg = BLOCK_CONFIGS[min(block_idx - 1, len(BLOCK_CONFIGS) - 1)]
    width, height = 1920, 1080
    raw_art = os.path.join(art_dir, f"raw_block_{block_idx:02d}.jpg")

    print(f"      [Art Engine] Generating Indianized Visual for Block {block_idx} (Ch {start_ch:03d}–{end_ch:03d})...")
    downloaded = fetch_image_safe(cfg["prompt"], raw_art, width=1280, height=720)

    if downloaded and os.path.exists(raw_art) and os.path.getsize(raw_art) > 3000:
        try:
            base = Image.open(raw_art).convert("RGBA")
            bw, bh = base.size
            base = base.crop((0, 0, bw, max(10, bh - 50))).resize((width, height), Image.Resampling.LANCZOS)
        except Exception:
            base = build_celestial_atmosphere_canvas(width, height, cfg["fallback_color"])
    else:
        base = build_celestial_atmosphere_canvas(width, height, cfg["fallback_color"])

    stamped = stamp_tactical_typography(base, cfg["title"])
    stamped.convert("RGB").save(out_file, "PNG")
    print(f"      [Art Engine] Scene Ready: '{out_file}'")

    if block_idx == 1:
        cover_path = os.path.join(art_dir, f"{part_tag}_cover.png")
        shutil.copy2(out_file, cover_path)
        print(f"      [Art Engine] Master Cover / Thumbnail Saved: '{cover_path}'")

    return out_file

# ---------------------------------------------------------------------------
# Step 4: Edge-TTS In-Process Async Synthesis & DSP Mastering
# ---------------------------------------------------------------------------
def get_voice_config_for_speaker(speaker: str) -> dict:
    if speaker == "System":
        return {"voice": "hi-IN-SwaraNeural", "rate": "+8%", "pitch": "+4Hz"}
    if any(k in speaker for k in ["दादाजी", "एल्डर", "Elder", "देवव्रत", "ऋषभ", "भैरव"]):
        return {"voice": "hi-IN-MadhurNeural", "rate": "-6%", "pitch": "-6Hz"}
    if speaker in ["Narrator", "सूत्रधार"]:
        return {"voice": "hi-IN-MadhurNeural", "rate": "+0%", "pitch": "+0Hz"}
    # Hero Rudra and conversational dialogue
    return {"voice": "hi-IN-MadhurNeural", "rate": "+4%", "pitch": "+3Hz"}

async def synthesize_line(index: int, line: dict, temp_dir: str, semaphore: asyncio.Semaphore) -> str:
    async with semaphore:
        speaker = line["speaker"]
        cfg = get_voice_config_for_speaker(speaker)
        chunk_path = os.path.join(temp_dir, f"line_{index:04d}.mp3")

        # In-process asynchronous Communicate call (no OS process creation overhead)
        for attempt in range(1, 4):
            try:
                comm = edge_tts.Communicate(
                    text=line["text"],
                    voice=cfg["voice"],
                    rate=cfg["rate"],
                    pitch=cfg["pitch"]
                )
                await asyncio.wait_for(comm.save(chunk_path), timeout=35.0)
                if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 100:
                    return chunk_path
            except Exception:
                if attempt == 3:
                    # Write silent audio placeholder if connection fails
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                        "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", chunk_path
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return chunk_path
                await asyncio.sleep(0.5 * attempt)

        return chunk_path

async def run_tts_for_chapter(lines: list[dict], temp_dir: str) -> list[str]:
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)
    semaphore = asyncio.Semaphore(5)
    tasks = [synthesize_line(i, line, temp_dir, semaphore) for i, line in enumerate(lines)]
    return await asyncio.gather(*tasks)

def master_chapter_audio(chunk_files: list[str], output_path: str, temp_dir: str):
    concat_manifest = os.path.join(temp_dir, "concat.txt")
    with open(concat_manifest, "w", encoding="utf-8") as f:
        for chunk in chunk_files:
            abs_p = os.path.abspath(chunk).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")

    raw_temp = os.path.join(temp_dir, "raw_temp.mp3")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_manifest, "-c", "copy", raw_temp
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run([
        "ffmpeg", "-y", "-i", raw_temp,
        "-af", "loudnorm=I=-14:LRA=7:TP=-1.5",
        "-ar", "44100", "-b:a", "192k", output_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_audio_duration_seconds(file_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
    return float(result.stdout.strip())

def format_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

# ---------------------------------------------------------------------------
# Marathon Audio & Progressive 1 FPS Video Assembly
# ---------------------------------------------------------------------------
def build_marathon_audio(chapters_dir: str, release_dir: str, part_tag: str, start_ch: int, end_ch: int) -> str:
    marathon_audio = os.path.join(release_dir, f"{part_tag}_audio_marathon.mp3")
    concat_file = os.path.join(release_dir, "marathon_concat.txt")

    with open(concat_file, "w", encoding="utf-8") as f:
        for ch in range(start_ch, end_ch + 1):
            ch_path = os.path.abspath(os.path.join(chapters_dir, f"ch_{ch:03d}_master.mp3")).replace("\\", "/")
            f.write(f"file '{ch_path}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file, "-c", "copy", marathon_audio
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(concat_file):
        os.remove(concat_file)

    return marathon_audio

def build_progressive_video(chapters_dir: str, art_dir: str, release_dir: str, part_tag: str,
                            start_ch: int, end_ch: int, block_size: int, marathon_audio: str):
    video_out = os.path.join(release_dir, f"{part_tag}_video_1080p.mp4")
    num_blocks = (end_ch - start_ch + 1) // block_size
    manifest_path = os.path.join(release_dir, "images_manifest.txt")

    with open(manifest_path, "w", encoding="utf-8") as f:
        for b_idx in range(1, num_blocks + 1):
            b_start = start_ch + (b_idx - 1) * block_size
            b_end = b_start + block_size - 1
            block_seconds = 0.0

            for ch in range(b_start, b_end + 1):
                ch_mp3 = os.path.join(chapters_dir, f"ch_{ch:03d}_master.mp3")
                block_seconds += get_audio_duration_seconds(ch_mp3)

            img_name = f"{part_tag}_block_{b_idx:02d}_ch{b_start:03d}_{b_end:03d}.png"
            img_path = os.path.abspath(os.path.join(art_dir, img_name)).replace("\\", "/")

            f.write(f"file '{img_path}'\n")
            f.write(f"duration {block_seconds:.3f}\n")
        f.write(f"file '{img_path}'\n")

    print("[Video Assembly] Losslessly muxing 1 FPS progressive video with mastered audio...")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", manifest_path,
        "-i", marathon_audio,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-r", "1",
        "-c:a", "copy",
        "-shortest",
        video_out
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(manifest_path):
        os.remove(manifest_path)

    print(f"\n[COMPLETE] Video ready: {video_out}")

# ---------------------------------------------------------------------------
# Main Controller Pipeline (Phased: 1 -> [2 -> 3 -> 4] -> Repeat)
# ---------------------------------------------------------------------------
async def run_pipeline():
    parser = argparse.ArgumentParser(description="Universal Novel-to-Audiobook Pipeline")
    parser.add_argument("--start", type=int, required=True, help="Starting chapter number (e.g. 1)")
    parser.add_argument("--end", type=int, required=True, help="Ending chapter number (e.g. 50)")
    parser.add_argument("--url", default=DEFAULT_URL, help="Starting URL if not previously indexed")
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("Error: 'ffmpeg' or 'ffprobe' not found in system PATH.")

    start_ch = args.start
    end_ch = args.end

    part_number = ((start_ch - 1) // 50) + 1
    part_tag = f"part_{part_number:02d}"

    novel_slug = extract_story_slug(args.url)
    story_id = novel_slug.replace("-", "_")
    base_story_dir = os.path.join("stories", story_id)

    glossary_path = os.path.join(base_story_dir, "lore_glossary.json")
    url_index_path = os.path.join(base_story_dir, "url_index.json")
    dir_art = os.path.join(base_story_dir, "assets", part_tag)
    dir_raw = os.path.join(base_story_dir, "raw", part_tag)
    dir_staged = os.path.join(base_story_dir, "staged", part_tag)
    dir_chapters = os.path.join(base_story_dir, "output_chapters", part_tag)
    dir_releases = os.path.join(base_story_dir, "releases", part_tag)
    temp_dir = os.path.join(base_story_dir, "temp_chunks")

    for d in [dir_art, dir_raw, dir_staged, dir_chapters, dir_releases, temp_dir]:
        os.makedirs(d, exist_ok=True)

    # STEP 1: Pre-scrape all chapters locally
    pre_scrape_all_chapters(start_ch, end_ch, args.url, dir_raw, url_index_path, novel_slug)

    # Initialize glossary with verified Indianized seed
    glossary = load_json_file(glossary_path, {})
    for k, v in SEED_GLOSSARY.items():
        if k not in glossary:
            glossary[k] = v
    save_json_file(glossary_path, glossary)

    total_chapters = end_ch - start_ch + 1
    num_blocks = (total_chapters + BLOCK_SIZE - 1) // BLOCK_SIZE

    cumulative_seconds = 0.0
    timestamps_path = os.path.join(dir_releases, f"{part_tag}_timestamps.txt")
    with open(timestamps_path, "w", encoding="utf-8") as f:
        f.write(f"# YouTube Timestamps: {story_id.upper()} - {part_tag.upper()} (Chapters {start_ch} to {end_ch})\n")

    for b_idx in range(1, num_blocks + 1):
        block_start = start_ch + (b_idx - 1) * BLOCK_SIZE
        block_end = min(block_start + BLOCK_SIZE - 1, end_ch)

        print(f"\n==================================================")
        print(f"  BLOCK {b_idx}/{num_blocks}: CHAPTERS {block_start:03d} TO {block_end:03d}")
        print(f"==================================================")

        # -------------------------------------------------------------
        # STEP 2: CONVERT 10 EPISODES IN GEMINI (Indianized)
        # -------------------------------------------------------------
        print(f"\n[Step 2] Localizing Chapters {block_start:03d} to {block_end:03d} via Gemini...")
        for ch_num in range(block_start, block_end + 1):
            raw_file = os.path.join(dir_raw, f"ch_{ch_num:03d}.txt")
            staged_file = os.path.join(dir_staged, f"ch_{ch_num:03d}.json")

            if not os.path.exists(staged_file):
                with open(raw_file, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                print(f"  -> Localizing Chapter {ch_num:03d} (Indian Heroic Names)...")
                payload = localize_chapter(raw_text, ch_num, glossary_path, glossary)
                save_json_file(staged_file, payload)
            else:
                print(f"  -> Chapter {ch_num:03d} localization already cached.")

        # -------------------------------------------------------------
        # STEP 3: MAKE IMAGE FOR THIS BLOCK
        # -------------------------------------------------------------
        print(f"\n[Step 3] Creating Artwork for Block {b_idx}...")
        ensure_block_cover_jit(b_idx, block_start, block_end, part_tag, dir_art)

        # -------------------------------------------------------------
        # STEP 4: MAKE MP3 & MASTER AUDIO FOR THE 10 EPISODES
        # -------------------------------------------------------------
        print(f"\n[Step 4] Synthesizing & Mastering MP3s for Chapters {block_start:03d} to {block_end:03d}...")
        for ch_num in range(block_start, block_end + 1):
            staged_file = os.path.join(dir_staged, f"ch_{ch_num:03d}.json")
            chapter_mp3 = os.path.join(dir_chapters, f"ch_{ch_num:03d}_master.mp3")
            payload = load_json_file(staged_file, {})

            if not os.path.exists(chapter_mp3):
                print(f"  -> [TTS] Synthesizing Chapter {ch_num:03d}...")
                chunks = await run_tts_for_chapter(payload["lines"], temp_dir)
                print(f"  -> [Mastering] Applying -14 LUFS standard to Chapter {ch_num:03d}...")
                master_chapter_audio(chunks, chapter_mp3, temp_dir)
                shutil.rmtree(temp_dir, ignore_errors=True)
            else:
                print(f"  -> Chapter {ch_num:03d} MP3 already mastered.")

            dur = get_audio_duration_seconds(chapter_mp3)
            time_str = format_timestamp(cumulative_seconds)
            title = payload.get("title", f"Chapter {ch_num:03d}")
            ts_line = f"{time_str} - Chapter {ch_num:03d}: {title}\n"
            print(f"     [Timestamp] {ts_line.strip()}")
            with open(timestamps_path, "a", encoding="utf-8") as f:
                f.write(ts_line)

            cumulative_seconds += dur

        # -------------------------------------------------------------
        # STEP 5: COOLDOWN PAUSE BETWEEN BLOCKS
        # -------------------------------------------------------------
        if b_idx < num_blocks:
            print(f"\n[Step 5] Block {b_idx} Complete! Cooldown pause of {COOLDOWN_SECONDS}s before Block {b_idx + 1}...")
            time.sleep(COOLDOWN_SECONDS)

    # FINAL ASSEMBLY
    print("\n==================================================")
    print("  ASSEMBLING 50-CHAPTER MARATHON MP3 & PROGRESSIVE MP4")
    print("==================================================")
    marathon_audio = build_marathon_audio(dir_chapters, dir_releases, part_tag, start_ch, end_ch)
    build_progressive_video(dir_chapters, dir_art, dir_releases, part_tag, start_ch, end_ch, BLOCK_SIZE, marathon_audio)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
