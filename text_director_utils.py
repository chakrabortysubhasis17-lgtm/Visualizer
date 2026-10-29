import os
import re
import time
import math
import json
import hashlib
import asyncio
import unicodedata
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from registry_utils import sync_new_characters_to_staging, FALLBACK_BASE_CHARACTERS

# =====================================================================
# OPTIONAL & ADVANCED PERFORMANCE LIBRARIES (Graceful Fallbacks)
# =====================================================================

try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    FTFY_AVAILABLE = False

try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

try:
    import diskcache
    CACHE_DIR = os.path.join(os.getcwd(), ".pipeline_cache")
    _disk_cache = diskcache.Cache(CACHE_DIR)
except Exception:
    _disk_cache = None

try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False


# =====================================================================
# CONSTANTS, PATTERNS & REGEX RULES
# =====================================================================

CONTAINER_SELECTORS = [
    ("div", {"id": "chr-content"}),
    ("div", {"id": "chapter-content"}),
    ("div", {"class": re.compile(r"(chapter-content|entry-content|epcontent|reading-content)", re.I)}),
    ("div", {"class": "txt"}),
    ("div", {"class": "m-read"}),
    ("div", {"id": "arrticle"}),
    ("article", {}),
]

# Clean UTF-8 brackets and standard regex '|' alternates
RE_SYSTEM = re.compile(
    r"(?:\[\vert{}【\vert{}〖\vert{}『\vert{}《\vert{}［\vert{}\{)(Ding!\vert{}System\vert{}Notice\vert{}Warning\vert{}Announcement\vert{}Prompt\vert{}Quest\vert{}Stat\vert{}Skill\vert{}Level\vert{}Lv\.\vert{}Inventory\vert{}Reward).*?(?:\]|】|〗|』|》|］|\})",
    re.I
)
RE_SCENE_DIVIDER = re.compile(r"^(\s*[*~=_#-]\s*){3,}$", re.MULTILINE)

WATERMARK_PATTERNS = [
    re.compile(r"(?:free\s*web\s*novel|freewebnovel)\s*\.?\s*c[o0]m", re.I),
    re.compile(r"^(?:translator|editor|proofreader|tl)\s*:\s*.*$", re.I | re.MULTILINE),
    re.compile(r"Translation\s+Nation", re.I),
    re.compile(r"(?:mtl-?\s*novel|mtlnovel)\s*\.?\s*c[o0]m", re.I),
    re.compile(r"(?:novelbin|novelfull|ranobes)\s*\.?\s*c[o0]m", re.I),
    re.compile(r"\(End of this chapter\)", re.I),
    re.compile(r"Please visit [a-zA-Z0-9.-]+\s*.*", re.I),
    re.compile(r"Read latest chapters at\s+.*", re.I),
    re.compile(r"Check out our latest novel.*", re.I),
    re.compile(r"\[TL Note:.*?\]", re.I),
    re.compile(r"https?://\S+", re.I),
    re.compile(r"【?\s*Brain Storage\s*】?", re.I),
    re.compile(r"【?\s*Please come in, dear readers\.?\s*】?", re.I),
    re.compile(r"Click here:.*?\((?:Visual scene|illustration).*?\)", re.I),
    re.compile(r"(?:Hey\s+everyone\s+)?don'?t\s+forget\s+to\s+vote\s+and\s+support.*", re.I),
    re.compile(r"Check\s+out\s+the\s+mass\s+release\s+goals.*", re.I),
    re.compile(r"Add\s+to\s+library\s+and\s+give\s+your\s+thoughts.*", re.I),
    re.compile(r"[\U0001D400-\U0001D7FF]+", re.UNICODE),
]

FULLWIDTH_TO_ASCII = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '「': '"', '」': '"',
    '，': ', ', '。': '. ', '！': '! ', '？': '? ',
    '：': ': ', '；': '; ', '（': '(', '）': ')'
})
RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')

# SFX additions: only these exact 53 keys may be emitted or staged.
SFX_KEYS = frozenset({
    # Physical movement & transport
    "footsteps", "run", "tiptoe", "horseandcart",
    # Environmental & atmosphere
    "creak", "crackle", "thunder", "drip", "wind", "forest", "ocean",
    # Magic, portals & energy
    "hum", "whoosh",
    # Combat, martial & bodily impact
    "impact", "thud", "blade", "armor", "slash", "monster", "wardrum", "pain",
    # LitRPG, item & system events
    "chime", "levelup", "interface", "swish", "quest", "alert",
    "achievement", "reward", "loot", "coin", "chest", "equip",
    # Character reactions & everyday actions
    "heartbeat", "gasp", "knock", "rustle", "splash", "squeak", "sigh",
    # Social, culinary & crowd dynamics
    "market", "cheer", "disappointed", "dishes", "eating", "cooking",
    # Romance & intimacy
    "heartwarm", "intimate",
    # Supernatural, occult & sacred
    "whisper", "haunt", "howl", "bells", "gong",
})


def normalize_sfx_key(value: Any) -> str:
    """Return an allowed lowercase SFX key, or an empty string."""
    if not isinstance(value, str):
        return ""
    key = value.strip().lower()
    return key if key in SFX_KEYS else ""


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://freewebnovel.com/",
}


# =====================================================================
# DATA MODELS
# =====================================================================

class SpeechSegment(BaseModel):
    line_id: str = Field(description="Sequential identifier, e.g. '0001', '0002'")
    speaker_role: str = Field(description="Speaker name, character alias, or 'Narrator'")
    gender: str = Field(description="Strictly: 'Male', 'Female', or 'Neutral'")
    age_category: str = Field(description="Strictly: 'toddler', 'young', 'teen', 'middle-aged', 'elder', or 'n/a'")
    emotion: str = Field(description="Dominant emotion: e.g. 'angry', 'fearful', 'sarcastic', 'neutral', 'excited', 'solemn'")
    line_type: str = Field(description="'Dialogue', 'Narration', or 'System'")
    edge_tts_voice: str = Field(description="Edge TTS neural voice")
    text: str = Field(description="Spoken dialogue or narrative string")
    sfx: str = Field(default="", description="One permitted SFX key or an empty string")


class ChapterNarrationManifest(BaseModel):
    chapter_title: str = Field(description="Clean title of the chapter")
    segments: list[SpeechSegment] = Field(description="Chronologically ordered speech segments")


# =====================================================================
# DISKCACHE & SANITIZATION HELPERS
# =====================================================================

def make_cache_key(prefix: str, content: str) -> str:
    content_hash = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()
    return f"{prefix}:{content_hash}"


def cache_get(key: str) -> Optional[Any]:
    if _disk_cache is None:
        return None
    try:
        return _disk_cache.get(key)
    except Exception:
        return None


def cache_set(key: str, value: Any, expire_seconds: Optional[int] = 86400 * 7):
    if _disk_cache is None:
        return
    try:
        _disk_cache.set(key, value, expire=expire_seconds)
    except Exception:
        pass


def clean_and_parse_json(raw_text: str):
    clean = raw_text.strip()
    
    # Strip markdown wrappers if present
    if clean.startswith("```"):
        clean = re.sub(r"^```[a-zA-Z]*\n", "", clean)
        clean = re.sub(r"\n```$", "", clean).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Recovery: Attempt auto-closing truncated segment arrays
    if clean.startswith("{") and not clean.endswith("}"):
        last_brace = clean.rfind("}")
        if last_brace != -1:
            repaired = clean[:last_brace + 1] + "]}"
            try:
                return json.loads(repaired)
            except Exception:
                pass
                
    if clean.startswith("[") and not clean.endswith("]"):
        last_brace = clean.rfind("}")
        if last_brace != -1:
            repaired = clean[:last_brace + 1] + "]"
            try:
                return json.loads(repaired)
            except Exception:
                pass

    raise json.JSONDecodeError("Failed to parse or repair Gemini JSON output", clean, 0)


# =====================================================================
# RAPIDFUZZ VOICE RESOLUTION HELPER
# =====================================================================

def resolve_character_voice(
    speaker: str,
    voice_registry: Dict[str, Any],
    default_voice: str = "en-US-ChristopherNeural",
    similarity_threshold: float = 82.0
) -> str:
    """
    Resolves character voice using exact lookup, case-insensitive match,
    and RapidFuzz C++ fuzzy matching against registry keys and aliases.
    """
    if not speaker or not voice_registry:
        return default_voice

    clean_sp = speaker.strip()

    if clean_sp in voice_registry:
        val = voice_registry[clean_sp]
        return val.get("voice", default_voice) if isinstance(val, dict) else val

    sp_lower = clean_sp.lower()
    for reg_key, reg_val in voice_registry.items():
        if reg_key.lower() == sp_lower:
            return reg_val.get("voice", default_voice) if isinstance(reg_val, dict) else reg_val
        if isinstance(reg_val, dict):
            aliases = [a.lower() for a in reg_val.get("aliases", [])]
            if sp_lower in aliases:
                return reg_val.get("voice", default_voice)

    if RAPIDFUZZ_AVAILABLE and voice_registry:
        choices = list(voice_registry.keys())
        match = process.extractOne(clean_sp, choices, scorer=fuzz.WRatio)
        if match and match[1] >= similarity_threshold:
            val = voice_registry[match[0]]
            return val.get("voice", default_voice) if isinstance(val, dict) else val

    return default_voice


# =====================================================================
# TEXT PROCESSING & SEGMENTATION UTILS
# =====================================================================

def split_by_sentence_threshold(text: str, threshold: int = 650) -> list[str]:
    if not text:
        return []

    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= threshold:
        return [cleaned]

    sentence_pattern = re.compile(r'.*?[.!?]["\'”’)]?(?=\s+|$)', re.DOTALL)
    parts = []
    remaining = cleaned

    while remaining:
        if len(remaining) <= threshold:
            parts.append(remaining)
            break

        current_chunk = []
        accumulated_len = 0
        last_match_end = 0

        for match in sentence_pattern.finditer(remaining):
            sentence = match.group(0).strip()
            current_chunk.append(sentence)
            accumulated_len += len(sentence) + 1
            last_match_end = match.end()

            if accumulated_len >= threshold:
                break

        if current_chunk and last_match_end > 0:
            parts.append(" ".join(current_chunk))
            remaining = remaining[last_match_end:].strip()
        else:
            parts.append(remaining)
            break

    return parts


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
        base_pitch = -2
        base_rate = 0

    return f"{base_pitch:+d}Hz", f"{base_rate:+d}%"


def clean_chapter_title_for_seo(raw_title: str, ch_num: int, default_topic: str = "Arc") -> str:
    cleaned = unicodedata.normalize('NFKC', raw_title)
    cleaned = re.sub(r'^(?:chapter|ch\.?)\s*\d+[\s:\-–—]+(?:chapter|ch\.?)\s*\d+[\s:\-–—]*', '', cleaned, flags=re.I)
    cleaned = re.sub(r'^(?:chapter|ch\.?)\s*\d+[\s:\-–—]*', '', cleaned, flags=re.I).strip()
    if not cleaned:
        cleaned = f"{default_topic} Phase {ch_num}"
    return f"Ch {ch_num:03d}: {cleaned.title()}"


def clean_and_normalize_text(text: str) -> str:
    if FTFY_AVAILABLE:
        try:
            text = ftfy.fix_text(text)
        except Exception:
            pass

    text = unicodedata.normalize('NFKC', text)
    text = text.translate(FULLWIDTH_TO_ASCII)
    text = RE_SCENE_DIVIDER.sub("", text)

    for pat in WATERMARK_PATTERNS:
        text = pat.sub("", text)

    text = re.sub(r'~+', '', text)
    text = re.sub(r'\*{2,}', '', text)
    text = re.sub(r'\.{4,}', '...', text)
    return re.sub(r"[ \t]+", " ", text).strip()


def balance_paragraph_quotes(paragraph: str) -> str:
    if paragraph.count('"') % 2 != 0:
        if re.search(r'\b(said|replied|whispered|murmured|asked|smiled|sneered)\b', paragraph, re.I):
            paragraph = paragraph + '"'
        else:
            paragraph = '"' + paragraph
    return paragraph


# =====================================================================
# PDF PAGE EXTRACTION ENGINE
# =====================================================================

def is_pdf_source(path_or_url: str) -> bool:
    """Safely detect if start_url is a local PDF file path (not a web URL)."""
    if not path_or_url or not isinstance(path_or_url, str):
        return False
    clean = path_or_url.strip().strip('"').strip("'")
    if clean.lower().startswith(("http://", "https://")):
        return False
    return clean.lower().endswith(".pdf")


def extract_pdf_page_content(pdf_path: str, page_num: int, default_topic: str = "Arc", is_start: bool = True) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts text from a single page (1-indexed) of a local PDF document.
    Returns: (clean_title, full_text, next_source_or_page)
    """
    pdf_path = pdf_path.strip().strip('"').strip("'")
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Local PDF file not found at: {pdf_path}")

    text = ""
    total_pages = 0

    # 1. Try PyMuPDF (fitz) with auto-closing context manager
    try:
        import fitz  # PyMuPDF
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            if page_num > total_pages or page_num < 1:
                print(f"[PDF Engine] Page {page_num} is beyond document bounds (Total: {total_pages}). End of PDF reached.", flush=True)
                return None, None, None
            text = doc[page_num - 1].get_text("text")
    except ImportError:
        # 2. Fallback to pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            total_pages = len(reader.pages)
            if page_num > total_pages or page_num < 1:
                print(f"[PDF Engine] Page {page_num} is beyond document bounds (Total: {total_pages}). End of PDF reached.", flush=True)
                return None, None, None
            text = reader.pages[page_num - 1].extract_text() or ""
        except ImportError:
            # 3. Fallback to pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    total_pages = len(pdf.pages)
                    if page_num > total_pages or page_num < 1:
                        print(f"[PDF Engine] Page {page_num} is beyond document bounds (Total: {total_pages}). End of PDF reached.", flush=True)
                        return None, None, None
                    text = pdf.pages[page_num - 1].extract_text() or ""
            except ImportError:
                raise ImportError(
                    "No PDF library found. Please install PyMuPDF or pypdf: pip install pypdf"
                )

    clean_title = f"Ch {page_num:03d}: Page {page_num}"

    # Normalize double linebreaks to preserve true paragraphs while unwrapping soft PDF linebreaks
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\n\n" in normalized_text:
        raw_blocks = re.split(r'\n\s*\n+', normalized_text)
    else:
        # Reconstruct paragraphs by checking for terminal punctuation
        lines = [l.strip() for l in normalized_text.split("\n") if l.strip()]
        raw_blocks = []
        curr_p = []
        for l in lines:
            curr_p.append(l)
            if re.search(r'[.!?]["\'”’)]?$', l):
                raw_blocks.append(" ".join(curr_p))
                curr_p = []
        if curr_p:
            raw_blocks.append(" ".join(curr_p))

    paragraphs = []
    for block in raw_blocks:
        unified = " ".join(block.split())
        cleaned = clean_and_normalize_text(unified)
        # Skip isolated header/footer running page numbers (e.g. standalone "14")
        if re.match(r'^\s*\d+\s*$', cleaned):
            continue
        if cleaned and RE_ALPHANUM.search(cleaned):
            paragraphs.append(cleaned)

    if not paragraphs:
        paragraphs = [f"Page {page_num}. Visual illustration or blank page."]

    # If is_start is False, do not prepend title into spoken narrative
    if is_start:
        full_text = f"{clean_title}.\n\n" + "\n\n".join(paragraphs)
    else:
        full_text = "\n\n".join(paragraphs)
    
    print(f"[PDF Engine] [OK] Extracted Page {page_num}/{total_pages} ({len(full_text.split())} words) from '{os.path.basename(pdf_path)}'", flush=True)

    next_source = pdf_path if page_num < total_pages else None
    return clean_title, full_text, next_source


# =====================================================================
# SCRAPING ENGINE (With DiskCache & Retries)
# =====================================================================

def scrape_chapter_content(session, url: str, ch_num: int, default_topic: str = "Arc", is_start: bool = True) -> tuple[str, str, Optional[str]]:
    if is_pdf_source(url):
        return extract_pdf_page_content(url, page_num=ch_num, default_topic=default_topic, is_start=is_start)

    cache_key = make_cache_key("scrape", url)
    cached = cache_get(cache_key)
    if cached and isinstance(cached, dict):
        clean_title = cached.get("clean_title")
        full_text = cached.get("full_text")
        next_url = cached.get("next_url")
        if clean_title and full_text and len(full_text.split()) > 40:
            print(f"[Scraper Cache] [✓] Retrieved cached Ch.{ch_num:03d}: {clean_title}", flush=True)
            return clean_title, full_text, next_url

    print(f"[Scraper] Connecting to Ch.{ch_num:03d}: {url}", flush=True)

    resp = None
    for attempt in range(1, 4):
        try:
            if isinstance(session, httpx.Client):
                resp = session.get(url, headers=HEADERS, timeout=25.0, follow_redirects=True)
            else:
                resp = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(attempt * 1.5)

    current_url_str = str(resp.url).lower()
    if f"chapter-{ch_num}" not in current_url_str:
        print(f"     [Scraper Notice] Requested Ch.{ch_num}, landed on: {resp.url}", flush=True)

    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1") or soup.find("h2", class_=re.compile(r"(title|chapter-title)", re.I))
    raw_title = h1.get_text(strip=True) if h1 else f"Chapter {ch_num}"
    clean_title = clean_chapter_title_for_seo(raw_title, ch_num, default_topic)

    container = None
    for tag, attrs in CONTAINER_SELECTORS:
        found = soup.find(tag, attrs)
        if found:
            container = found
            break
    if not container:
        container = soup.find("body")

    paragraphs = []
    p_tags = container.find_all("p") if container else []
    p_tags = sort_paragraphs_by_order_index(p_tags)

    if len(p_tags) >= 3:
        indexed_paragraphs = []
        for p in p_tags:
            ptxt = clean_and_normalize_text(p.get_text(strip=True))
            if ptxt and RE_ALPHANUM.search(ptxt):
                if re.search(r"^(?:freewebnovel|novelbin|mtl-novel|read novel)\b", ptxt, re.I):
                    continue
                
                # Parse the CSS order index to handle DOM-scrambling anti-scraping
                order_idx = 0
                style_attr = p.get("style", "")
                order_match = re.search(r'order\s*:\s*(\d+)', style_attr, re.I)
                if order_match:
                    order_idx = int(order_match.group(1))
                else:
                    data_idx = p.get("data-reader-order-index")
                    if data_idx and str(data_idx).isdigit():
                        order_idx = int(data_idx)
                        
                indexed_paragraphs.append((order_idx, ptxt))
                
        # Sort by the extracted order index so paragraphs match the true reading sequence
        indexed_paragraphs.sort(key=lambda x: x[0])
        paragraphs = [item[1] for item in indexed_paragraphs]

    elif container:
        raw_html = str(container)
        text_with_newlines = re.sub(r"<br\s*/?>", "\n", raw_html, flags=re.I)
        fallback_soup = BeautifulSoup(text_with_newlines, "html.parser")
        for line in fallback_soup.get_text().split("\n"):
            ltxt = clean_and_normalize_text(line)
            if ltxt and RE_ALPHANUM.search(ltxt):
                if re.search(r"^(?:freewebnovel|novelbin|mtl-novel|read novel)\b", ltxt, re.I):
                    continue
                paragraphs.append(ltxt)

    if not paragraphs:
        paragraphs = [f"Chapter {ch_num}. Exposition details continue."]

    preview_snippet = " ".join(paragraphs[:2])[:110]
    print(f"     [Scraper Preview Ch.{ch_num:03d}]: \"{preview_snippet}...\"", flush=True)

    full_text = f"{clean_title}.\n\n" + "\n\n".join(paragraphs)
    print(f"[Scraper] [✓] Scraped {len(paragraphs)} paragraphs ({len(full_text.split())} words) for Ch.{ch_num:03d}", flush=True)

    next_url = None
    next_btn = soup.find("a", id=re.compile(r"next_chap", re.I)) or soup.find("a", class_=re.compile(r"next-chap", re.I))
    if next_btn and next_btn.get("href"):
        href = next_btn["href"].strip()
        if href and href not in ["#", "javascript:void(0);", url]:
            full_next = urllib.parse.urljoin(url, href)
            if full_next != url:
                next_url = full_next

    if not next_url:
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            rel = a.get("rel", "")
            if isinstance(rel, list):
                rel = " ".join(rel)
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
        pattern_curr = re.compile(rf"(chapter[-_/]){ch_num}([/-]|$)", re.I)
        if pattern_curr.search(url):
            next_url = pattern_curr.sub(rf"\g<1>{ch_num + 1}\g<2>", url)

    if len(paragraphs) >= 5:
        cache_set(cache_key, {
            "clean_title": clean_title,
            "full_text": full_text,
            "next_url": next_url
        }, expire_seconds=86400 * 14)

    return clean_title, full_text, next_url


def sort_paragraphs_by_order_index(p_tags):
    """Sorts BeautifulSoup paragraph tags based on CSS flexbox order or reader-order index."""
    def _get_order_idx(p):
        style_attr = p.get("style", "")
        order_match = re.search(r'order\s*:\s*(\d+)', style_attr, re.I)
        if order_match:
            return int(order_match.group(1))
        data_idx = p.get("data-reader-order-index")
        if data_idx and str(data_idx).isdigit():
            return int(data_idx)
        return 0
    
    return sorted(p_tags, key=_get_order_idx)

# =====================================================================
# GEMINI DIRECTOR & CHUNK PARSER (With Resilient JSON & DiskCache)
# =====================================================================

def split_text_into_logical_parts(raw_text: str, max_single_part_chars: int = 5500, target_part_chars: int = 4800, max_parts: int = 5) -> list[str]:
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    if not paragraphs:
        return [raw_text]

    total_chars = sum(len(p) for p in paragraphs)
    if total_chars <= max_single_part_chars:
        return ["\n\n".join(paragraphs)]

    num_parts = min(max_parts, max(2, math.ceil(total_chars / target_part_chars)))
    target_chars_per_part = total_chars / num_parts

    parts = []
    current_part = []
    current_len = 0

    for p in paragraphs:
        current_part.append(p)
        current_len += len(p)

        if current_len >= target_chars_per_part and len(parts) < num_parts - 1:
            parts.append("\n\n".join(current_part))
            current_part = []
            current_len = 0

    if current_part:
        parts.append("\n\n".join(current_part))

    return parts


def extract_retry_delay_seconds(error_obj: Exception, attempt: int) -> float:
    err_str = str(error_obj)
    m1 = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str, re.I)
    if m1:
        return math.ceil(float(m1.group(1))) + 2.0
    m2 = re.search(r"retryDelay['\":\s]+(\d+)s", err_str, re.I)
    if m2:
        return float(m2.group(1)) + 2.0
    return float(attempt * 10.0)


def parse_single_chunk_via_gemini(
    client,
    title: str,
    chunk_text: str,
    system_instruction: str,
    max_retries: int = 3,
    refresh_legacy_cache_for_sfx: bool = False,
) -> list:
    # Bumped namespace to v4: enforces strict anti-consecutive and anti-metaphor audio cues
    chunk_cache_key = make_cache_key("gemini_chunk_sfx_v4", chunk_text)

    if not refresh_legacy_cache_for_sfx:
        cached_segments = cache_get(chunk_cache_key)
        if cached_segments and isinstance(cached_segments, list) and len(cached_segments) > 0:
            return cached_segments

        legacy_cache_key = make_cache_key("gemini_chunk", chunk_text)
        legacy_segments = cache_get(legacy_cache_key)
        if legacy_segments and isinstance(legacy_segments, list) and len(legacy_segments) > 0:
            migrated_segments = []
            for item in legacy_segments:
                if isinstance(item, dict):
                    migrated = dict(item)
                    migrated["sfx"] = normalize_sfx_key(migrated.get("sfx", ""))
                    migrated_segments.append(migrated)
            if migrated_segments:
                cache_set(chunk_cache_key, migrated_segments, expire_seconds=86400 * 14)
                return migrated_segments

    prompt = f"CHAPTER: {title}\n\nCONTENT:\n{chunk_text}"

    safety_settings = [
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    ]

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    safety_settings=safety_settings,
                    temperature=0.1
                )
            )

            if response and hasattr(response, "prompt_feedback") and response.prompt_feedback:
                block_reason = getattr(response.prompt_feedback, "block_reason", None)
                if block_reason:
                    print(f"     [Gemini Policy Block] Prompt blocked: {block_reason}. Fallback to rule-based staging.", flush=True)
                    return []

            raw_json = None
            if response:
                if response.text:
                    raw_json = response.text
                elif response.candidates:
                    cand = response.candidates[0]
                    finish_reason = getattr(cand, "finish_reason", "UNKNOWN")

                    if "SAFETY" in str(finish_reason):
                        print(f"     [Gemini Safety Block] Candidate blocked ({finish_reason}). Fallback to rule-based staging.", flush=True)
                        return []

                    if hasattr(cand, "content") and cand.content and cand.content.parts:
                        for part in cand.content.parts:
                            if hasattr(part, "text") and part.text:
                                raw_json = part.text
                                break

            if raw_json:
                data = clean_and_parse_json(raw_json)
                staged = []
                raw_list = data if isinstance(data, list) else data.get("segments", [])

                for s in raw_list:
                    pitch, rate = calculate_prosody_adjustments(s)
                    staged.append({
                        "line_id": s.get("line_id", "0001"),
                        "speaker": s.get("speaker_role") or s.get("speaker") or "Narrator",
                        "gender": s.get("gender", "Male"),
                        "line_type": s.get("line_type", "Narration"),
                        "emotion": s.get("emotion", "neutral"),
                        "age_category": s.get("age_category", "young"),
                        "text": s.get("text", "").strip(),
                        "voice": s.get("edge_tts_voice") or s.get("voice") or "en-US-GuyNeural",
                        "pitch": pitch,
                        "rate": rate,
                        "sfx": normalize_sfx_key(s.get("sfx", ""))
                    })

                if staged:
                    cache_set(chunk_cache_key, staged, expire_seconds=86400 * 14)
                    time.sleep(2.0)
                    return staged
                else:
                    print(f"     [Gemini Director] Attempt {attempt}/{max_retries} produced empty segments array.", flush=True)

            if attempt < max_retries:
                retry_wait = float(attempt * 8.0)
                print(f"     [Gemini Cooldown] Retrying chunk (Attempt {attempt + 1}/{max_retries}) in {retry_wait:.1f}s...", flush=True)
                time.sleep(retry_wait)

        except Exception as e:
            err_str = str(e)
            if "PROHIBITED_CONTENT" in err_str or "BLOCKED" in err_str:
                print(f"     [Gemini Policy Block] Exception flagged hard policy violation. Fallback to rule-based staging.", flush=True)
                return []

            delay = extract_retry_delay_seconds(e, attempt)
            print(f"     [Gemini Director] Request error (Attempt {attempt}/{max_retries}): {e}", flush=True)
            if attempt < max_retries:
                print(f"     [Dynamic Cooldown] Waiting {delay:.1f}s before retrying...", flush=True)
                time.sleep(delay)

    return []


def parse_chapter_via_gemini_director(
    client,
    title: str,
    raw_text: str,
    stage_file: str,
    max_narr_merge: int = 650,
    refresh_legacy_cache_for_sfx: bool = False,
) -> list:
    staged_chars = {}
    if os.path.exists(stage_file):
        try:
            with open(stage_file, "rb") as f:
                parsed_staged = clean_and_parse_json(f.read().decode("utf-8", errors="ignore"))
                if isinstance(parsed_staged, dict):
                    staged_chars = parsed_staged.get("characters", {})
        except Exception as e:
            print(f"     [Gemini Director Warning] Failed reading stage file: {e}", flush=True)

    if not staged_chars:
        staged_chars = dict(FALLBACK_BASE_CHARACTERS)

    if not client or not GENAI_AVAILABLE:
        return fallback_rule_based_staging(raw_text, staged_chars, max_narr_merge)

    # Build active cast manifest with aliases, gender locks, and neural voice assignments
    char_manifest = []
    for c_key, c_val in staged_chars.items():
        disp = c_val.get("display_name", c_key.title())
        gender = c_val.get("gender", "Male")
        voice = c_val.get("voice", "en-US-GuyNeural")
        aliases = ", ".join(c_val.get("aliases", [c_key]))
        char_manifest.append(f"• {disp} | GENDER: {gender} | VOICE: {voice} | ALIASES: [{aliases}]")

    registered_manifest_str = "\n".join(char_manifest)

    # Tightened director system instruction with strict negative constraints & deduplication
    system_instruction = f"""You are an expert Audiobook Screenplay Director, Dramaturg, and Voice Acting Lead specialized in neural Text-to-Speech (Edge TTS) script synthesis.
Your mandate is to convert web novel chapter text into an execution-grade JSON screenplay array for multi-voice TTS synthesis.

You must follow every directive below without deviation:

### CORE DIRECTIVE 1: STRICT NARRATIVE INTEGRITY & LOSSLESS TEXT PRESERVATION
1. Zero Text Elimination: Every single narrative description, dialogue line, interior monologue, interjection, title, and sound effect must appear in the final output array in exact, chronological reading order.
2. Prohibited Alterations: NEVER summarize, truncate, paraphrase, reword, sanitize, or censor any narrative content.
3. Clause Order: Keep the exact internal order of sentences and clauses as provided in the raw chunk.

### CORE DIRECTIVE 2: CHARACTER, ENTITY & DIALOGUE SEGREGATION
1. Dialogue Tag Separation: Spoken dialogue MUST be isolated from adjacent narrative tags.
   - Example: '"Shall we?" she whispered, glancing back.' -> Segment 1: Dialogue by speaker; Segment 2: Narration by Narrator.
2. Speaker Identification & Gender Lock:
   - Always reference the ACTIVE STAGED CHARACTERS manifest below first. A female character must NEVER become male, and a male character must NEVER become female.
   - The "speaker" field must be a CLEAN character name or "Narrator". NEVER put spoken quotes, phrases, or full sentences into the speaker field.
   - If a character is the first-person narrator ('I', 'me') and has an explicit identity established in context, assign them their true character name and gender instead of a generic "Protagonist" label.
   - Mark general narration and descriptive actions with speaker "Narrator", gender "Neutral", and line_type "Narration".
3. System & Interface Blocks: Screen prompts, level-up banners, and robotic notifications must be marked with speaker "System", gender "Neutral", and line_type "System". Character internal thoughts must NEVER be marked as "System".

### CORE DIRECTIVE 3: EDGE TTS PUNCTUATION, CADENCE & PHONETIC STABILITY
1. Mandatory Terminal Punctuation: Every segment's text field MUST terminate with a valid punctuation mark ('.', '!', '?', '...', or '—'). If missing in the raw text, append the contextually appropriate mark.
2. Pause & Cadence Upgrades:
   - Retain all natural internal commas.
   - Convert trailing hyphens or incomplete thoughts into ellipses ('...') and abrupt speech cut-offs into em-dashes ('—') to prevent Edge TTS from clipping syllables.
   - Use exclamation marks ('!') for shouted lines or screams to trigger dynamic neural inflections.
3. Phonetic Normalization for Repetitive Character Patterns:
   - Leading Repetitions (Stutters): When a word is preceded by detached or hyphenated repeating characters (e.g., 'W W W WHAT' or 'W-w-w-what'), collapse them into a single hyphenated stutter attached directly to the base word (e.g., 'W-what'). Do NOT leave isolated single letters detached so Edge TTS does not spell out alphabet names.
   - Internal & Trailing Elongations: When words contain excessively multiplied characters to simulate shouting or shock (e.g., 'OH H H H', 'NOOOO!'), normalize the run to a natural 2-to-3 character sequence (e.g., 'Ohhh...', 'Nooo!') with appropriate terminal punctuation.
   - Semantic Boundary: These phonetic adjustments are strictly restricted to smoothing vocal delivery. Never drop, rewrite, replace, or invent underlying vocabulary words.

### CORE DIRECTIVE 4: JSON SCHEMA & OUTPUT FORMAT
Return ONLY a valid JSON object with a single key "segments" containing an array of objects. Do NOT output markdown code fences, citations, or conversational text.

Each object in the array must strictly comply with this schema:
{{
  "line_id": "0001",
  "speaker": "Speaker Name",
  "gender": "Female / Male / Neutral",
  "line_type": "Narration / Dialogue / System",
  "style": "omniscient_narrator / kinetic_action / whispered / system_monolith",
  "pause_duration": 0.3,
  "text": "Verbatim text segment with normalized Edge TTS punctuation.",
  "voice": "en-US-GuyNeural",
  "sfx": "footsteps"
}}

### CORE DIRECTIVE 5: CONTEXT-AWARE SOUND EFFECT TAGGING (SFX) & STRICT NEGATIVE CONSTRAINTS

The "sfx" field is metadata for audio assembly. It is NEVER spoken and must never replace, alter, summarize, or add words to the narrative text.

MANDATORY NEGATIVE CONSTRAINTS:
1. STRICT ANTI-CONSECUTIVE RULE: NEVER tag the same SFX key in consecutive rows or across continuous neighboring sentences. If a battle or movement spans several sentences, place the cue ONLY on the very first segment where the action begins, and leave subsequent segments as "".
2. NEVER TAG METAPHORS OR SIMILES: Do NOT tag figurative language, thoughts, memories, plans, or similes.
   - 'tears running down her cheeks' -> NEVER tag "run"!
   - 'crack in the egg was like lightning' -> NEVER tag "thunder"!
   - 'invest every coin earned' (thinking about money) -> NEVER tag "coin"!
   - 'the entire group stopped' -> NEVER tag "thud"!
   - 'he clenched his fists' -> NEVER tag "thud"!
3. LITERAL ACTIVE EVENTS ONLY:
   - "pain": Acute combat injury impact on living humanoid fighters. NEVER tag illness, disease (Cryosis), emotional grief, or dying monster speech.
   - "eating": Strictly chewing/eating solid food. NEVER tag drinking liquids, gulping water, or metaphorical consumption.
   - "dishes": Strictly setting down plates, bowls, or cutlery at a dining table. NEVER tag inspecting gems, handling loot, or tapping shop counters.
   - "cheer": Strictly stadium/arena mass crowd celebration. NEVER tag children giggling, mocking, or school laughter.
   - "whisper": Strictly eerie eldritch murmurs, phantom voices, or cursed artifacts in the mind. NEVER tag ordinary human whispers, quiet prayers, or private family comforting.
   - "blade": Strictly drawing or unsheathing a metal blade from its scabbard. NEVER tag dropping a weapon, holding a blade, or verbal threats.
   - "armor": Strictly heavy metallic plate armor clanking. NEVER tag cloth robes, dresses, or uniforms.

MATCHING TRIGGER DIRECTORY:
• "gasp": Explicit character audible gasp -> 'I gasp', 'she gasps', 'gasped in horror'.
• "heartbeat": Literal physical racing pulse in combat/terror -> 'heart thundered', 'badump! badump!', 'pounding heart'.
• "thud": Blunt landings, body collapses, heavy foot stomps -> 'stomped her foot', 'body collapsed to the ground'.
• "rustle": Fabric, robes, clothing adjusting, bowing, kneeling, foliage -> 'bowed low', 'kneels in unison', 'fidgeting with sleeves', 'outfit adjusts'.
• "armor": STRICTLY metallic plate armor clanking or metal gauntlets shifting.
• "creak": Doors, gates, or hinges physically creaking open/closed -> 'doors creak open', 'hinges groaned'.
• "hum": Magic activation, glowing aura, shimmers -> 'shimmer of deep blue light', 'runes flared with light'.
• "chime": Routine System status notification -> 'Ding!', 'System notification'. (Tag ONLY once per notification block).
• "footsteps": Movement down a path, approaching, stepping -> 'Step.', 'step forward', 'stepped toward'.
• "run": Sprints, rapid charging, fleeing -> 'sprinted', 'charged forward', 'fled at top speed'.
• "tiptoe": Slow, stealthy, cautious footsteps -> 'tiptoe', 'careful steps', 'light footing', 'sneaking'.
• "horseandcart": Carriages, carts, wagons rolling, trotting hooves -> 'carriage rolled', 'wheels rattled', 'wagon approached'.
• "market": Dense crowd chatter, bustling trade, bazaars -> 'bustling market', 'vendors shouting', 'bazaar'.
• "cheer": Crowd cheers, stadium applause, victory roars -> 'crowd cheered', 'stadium erupted in applause'.
• "disappointed": Crowd groans, collective letdown -> 'crowd groaned', 'collective sigh of letdown'.
• "wardrum": Heavy rhythmic war drums, army marching cadence -> 'war drums', 'drums beat', 'marching drums'.
• "gong": Resonant temple bell, cultivation breakthrough chime, bronze gong -> 'spiritual gong', 'bell of enlightenment', 'temple gong'.
• "pain": Sharp groans of pain, acute combat wounds -> 'groaned in agony', 'sharp gasp of pain', 'blade pierced his flesh'.
• "cooking": Sizzling skillets, frying, bubbling stew, boiling cauldron -> 'sizzled in the pan', 'pot bubbled over the hearth'.
• "dishes": Setting down plates, clattering bowls at a dining table -> 'set down the plates', 'dishes clattered on the table'.
• "eating": Chewing solid food, taking bites -> 'chewed hungrily', 'took a bite of the meat', 'devoured the meal'.
• "heartwarm": Romantic tenderness, gentle hand-holding, blushing -> 'fingers slipped through mine', 'laced our fingers', 'blushed softly'.
• "intimate": Deep romantic tension, sensual moments, close whispers, leans -> 'leaned in close', 'breath brushed her lips', 'quiet intimate embrace'.
• "sigh": Soft audible release of breath, relief, weary exhale -> 'let out a soft sigh', 'sighed in relief', 'weary exhale'.
• "whisper": Eerie phantom voices, occult murmurs, telepathic shadows -> 'phantom whispers', 'eerie murmurs', 'voices coiling in his mind'.
• "haunt": Sudden supernatural chill, eerie presence, dread -> 'unnatural chill', 'chilling presence', 'temperature dropped suddenly'.
• "howl": Distant nocturnal calls, wolf howl -> 'distant howl', 'howl tore through the night', 'wolf howling'.
• "bells": Cathedral bells, clocktower tolls, distant city bells -> 'bell chimed', 'bell tolled', 'clock tower struck'.
• "wind": Desolate drafts, howling gale, mountain breeze -> 'wind howled', 'chilling draft', 'howling gale'.
• "forest": Peaceful woodland canopy, rustling trees, chirping -> 'primeval forest', 'rustling canopy', 'woodland sounds'.
• "ocean": Crashing waves, surf, sea spray -> 'waves crashed', 'lapping waves', 'ocean surf'.
• "impact": High-velocity physical combat strike, heavy blunt collision -> 'hammer slammed', 'blunt collision'.
• "whoosh": Portals, teleportation, spatial gate, spatial tear -> 'portal opened', 'stepped through the spatial rift'.
• "blade": Drawing a metal sword, dagger, or blade from a scabbard/sheath -> 'unsheathed his blade', 'drew his dagger'.
• "slash": Cutting, hacking, slicing, or flesh-piercing strike -> 'blade sliced cleanly', 'sword severed'.
• "monster": Beast roaring, screeching, snarling, or howling -> 'beast roared furiously', 'growled savagely'.
• "alert": System danger warning or alarm -> '[Warning!]', 'threat detected'.
• "quest" / "levelup" / "achievement" / "reward" / "loot" / "coin" / "chest" / "equip": Specific LitRPG game mechanics occurring in the narrative.

AUTHORIZED SFX KEYS (EXACT LIST):
[footsteps, run, tiptoe, horseandcart, creak, crackle, thunder, drip, wind, forest, ocean, hum, whoosh, impact, thud, blade, armor, swish, slash, monster, wardrum, pain, chime, levelup, interface, quest, alert, achievement, reward, loot, coin, chest, equip, heartbeat, gasp, knock, rustle, splash, squeak, sigh, market, cheer, disappointed, dishes, eating, cooking, heartwarm, intimate, whisper, haunt, howl, bells, gong]

STRICT SFX RULES:
- Every segment MUST contain an "sfx" field. If no condition applies, use "". Never use null, "none", "N/A", or whitespace.
- Never repeat the same SFX on consecutive rows or adjacent actions.
- Never output multiple keys in one field, and never place SFX descriptions inside "text".
- Preserve all original narrative content and chronological order.
ACTIVE STAGED CHARACTERS:
{registered_manifest_str}
"""

    parts = split_text_into_logical_parts(raw_text, max_single_part_chars=5500, target_part_chars=4800, max_parts=5)
    all_staged = []

    if len(parts) > 1:
        print(f"     [Gemini Director] Partitioned chapter into {len(parts)} balanced logical parts...", flush=True)

    for p_idx, part in enumerate(parts, 1):
        if len(parts) > 1:
            print(f"     [Gemini Director] Processing Part {p_idx}/{len(parts)} ({len(part.split())} words)...", flush=True)

        part_staged = parse_single_chunk_via_gemini(
            client,
            title,
            part,
            system_instruction,
            refresh_legacy_cache_for_sfx=refresh_legacy_cache_for_sfx,
        )

        if part_staged and isinstance(part_staged, list) and len(part_staged) > 0:
            all_staged.extend(part_staged)
        else:
            print(f"     [Gemini Fallback] Using rule-based staging for Part {p_idx}...", flush=True)
            fallback_part = fallback_rule_based_staging(part, staged_chars, max_narr_merge)
            all_staged.extend(fallback_part)

    refined_staged = []
    for seg in all_staged:
        # Additive SFX normalization; invalid or missing keys become empty.
        seg["sfx"] = normalize_sfx_key(seg.get("sfx", ""))

        # Harmonize legacy schema aliases if Gemini outputs alternate field keys
        if "speaker_role" in seg and "speaker" not in seg:
            seg["speaker"] = seg.pop("speaker_role")
        if "edge_tts_voice" in seg and "voice" not in seg:
            seg["voice"] = seg.pop("edge_tts_voice")

        # Sanitize corrupted speaker names (strip quotes, reject entire dialogue phrases in speaker)
        sp = seg.get("speaker", "Narrator").strip()
        if sp.startswith('"') and sp.endswith('"'):
            sp = sp.strip('"').strip()
        if sp == seg.get("text", "").strip().strip('"') or len(sp) > 35 or any(p in sp for p in ['.', '!', '?', '...']):
            sp = "Narrator" if seg.get("line_type") == "Narration" else "mc"
        seg["speaker"] = sp

        # Fuzzy character voice lock & continuity enforcement
        sp = seg.get("speaker", "Narrator")
        current_voice = seg.get("voice", "en-US-ChristopherNeural")
        if seg.get("line_type") == "Narration" or sp.lower() == "narrator":
            # Hard-lock any narration row or Narrator speaker to Christopher
            seg["speaker"] = "Narrator"
            seg["voice"] = "en-US-ChristopherNeural"
        elif seg.get("line_type") == "Dialogue":
            seg["voice"] = resolve_character_voice(sp, staged_chars, default_voice=current_voice)
        elif seg.get("line_type") == "System":
            seg["voice"] = "en-US-ChristopherNeural"

        seg_text = seg.get("text", "")
        t_low = seg_text.lower()
        is_brief_event = len(seg_text.split()) < 22

        # =================================================================
        # TARGETED SEMANTIC VALIDATION & FALSE POSITIVE SUPPRESSION
        # =================================================================

        # Demote non-metallic outfit shifts tagged as 'armor' to 'rustle'
        if seg["sfx"] == "armor" and not re.search(r'\b(armor|plate|chainmail|cuirass|greaves?|helm)\b', seg_text, re.I):
            seg["sfx"] = "rustle"

        # Suppress 'blade' on dialogue threats or dropped weapons
        if seg["sfx"] == "blade":
            if seg.get("line_type") == "Dialogue" or not re.search(r'\b(drew|drawn|draw|unsheathed?|sheathed?|pulled\s+out\s+(?:his|her|their)\s+(?:sword|blade|dagger))\b', seg_text, re.I):
                seg["sfx"] = ""

        # Suppress 'cheer' on children giggling or school mockery
        if seg["sfx"] == "cheer":
            if re.search(r'\b(children|kids|giggled|mockery|laughter|laughed|snickered)\b', seg_text, re.I) and not re.search(r'\b(stadium|arena|crowd\s+cheered|erupted\s+in\s+cheers|applause)\b', seg_text, re.I):
                seg["sfx"] = ""

        # Suppress 'eating' on drinking liquids
        if seg["sfx"] == "eating" and re.search(r'\b(water|drink|drank|gulped\s+(?:it\s+)?down|bottle|tea|wine|ale|potion|elixir)\b', seg_text, re.I):
            seg["sfx"] = ""

        # Suppress 'dishes' on non-dining table contexts (inspecting items, tapping counters)
        if seg["sfx"] == "dishes" and not re.search(r'\b(plates?|dishes|bowls?|cups?|saucers?|tray|table|dinner|meal|feast|breakfast|lunch|supper)\b', seg_text, re.I):
            seg["sfx"] = ""

        # Suppress 'whisper' on normal human murmurs, prayers, or family comforting
        if seg["sfx"] == "whisper":
            if seg.get("line_type") == "Dialogue" or not re.search(r'\b(phantom|eldritch|eerie|shadows?|voices?\s+coiling|madness|curse|creeping\s+into\s+(?:his|her|their)\s+mind)\b', seg_text, re.I):
                seg["sfx"] = ""

        # Suppress 'pain' on dialogue, dying monster speech, or chronic illness
        if seg["sfx"] == "pain":
            if seg.get("line_type") == "Dialogue" or re.search(r'\b(illness|disease|cryosis|sickness|suffering|condition|fever|poisoning)\b', seg_text, re.I):
                seg["sfx"] = ""

        # Suppress 'run' on tears running or metaphorical sprints
        if seg["sfx"] == "run":
            if re.search(r'\b(tears?\s+running|running\s+down\s+(?:her|his|their)\s+cheeks?|wanted\s+to\s+sprint|thought\s+of\s+running)\b', seg_text, re.I):
                seg["sfx"] = ""

        # Suppress 'thunder' on similes (e.g. "like lightning")
        if seg["sfx"] == "thunder" and re.search(r'\b(like\s+lightning|as\s+if\s+lightning)\b', seg_text, re.I):
            seg["sfx"] = ""

        # Suppress 'coin' on financial contemplation without physical handling
        if seg["sfx"] == "coin" and not re.search(r'\b(coins?\s+(?:clinked|jingled|dropped|fell|poured)|pouch\s+of\s+coins?|gold\s+coins?\s+on\s+the)\b', seg_text, re.I):
            seg["sfx"] = ""

        # Suppress 'thud' on stopped walking or clenched fists
        if seg["sfx"] == "thud" and re.search(r'\b(stopped|clenched\s+(?:his|her|their)\s+fists?|fists?\s+tightened)\b', seg_text, re.I):
            seg["sfx"] = ""

        # Suppress 'splash' on blood/gore explosions
        if seg["sfx"] == "splash" and not re.search(r'\b(water|pool|river|lake|sea|ocean|puddle)\b', seg_text, re.I):
            seg["sfx"] = ""

        # Suppress 'gasp' on lines without literal gasp words
        if seg["sfx"] == "gasp" and not re.search(r'\b(gasp|gasps|gasped|sharp\s+intake\s+of\s+breath)\b', seg_text, re.I):
            seg["sfx"] = ""

        # =================================================================
        # HARDENED DETERMINISTIC FALLBACK PATTERNS (Literal Events Only)
        # =================================================================
        if not seg["sfx"]:
            if re.search(r'\b(gasp|gasps|gasped|sharp\s+intake\s+of\s+breath)\b', t_low) and is_brief_event:
                seg["sfx"] = "gasp"
            elif re.search(r'\b(badump|thump-thump|heart\s+is\s+thundering|heart\s+thundering|heartbeat\s+starts|pounding\s+heart)\b', t_low) and is_brief_event:
                seg["sfx"] = "heartbeat"
            elif re.search(r'\b(stomp|stomps|stomping|body\s+collapsed|collapsed\s+lifelessly|slammed\s+onto\s+the\s+ground)\b', t_low):
                seg["sfx"] = "thud"
            elif re.search(r'\b(fidgeting\s+with\s+(?:my|her|his)\s+sleeves|straightening\s+(?:his|her)\s+coat|bow(?:s|ed)?\s+low|bow(?:s|ed)?\s+in\s+(?:perfect\s+)?sync|kneel(?:s|ed|ing)?\b.*?\bunison\b|kneel(?:s|ed|ing)?\s+before|outfit\s+adjusts)\b', t_low):
                seg["sfx"] = "rustle"
            elif re.search(r'\b(sprint(?:s|ed|ing)?|dashes\s+forward|dashed\s+forward|fled\s+at\s+top\s+speed|charging\s+forward)\b', t_low):
                seg["sfx"] = "run"
            elif re.search(r'\b(tiptoe(?:d|ing)?|cautious\s+steps?|creeping|sneaks?|sneaking)\b', t_low):
                seg["sfx"] = "tiptoe"
            elif re.search(r'\b(carriage\s+rolled|wheels?\s+rattled|wagon\s+approached|horses?\s+trotted)\b', t_low):
                seg["sfx"] = "horseandcart"
            elif re.search(r'\b(laced\s+(?:her|his|our)\s+fingers|fingers\s+slipped\s+through\s+mine)\b', t_low):
                seg["sfx"] = "heartwarm"
            elif re.search(r'\b(sigh(?:ed|ing)?\s+in\s+relief|soft\s+sigh|weary\s+exhale)\b', t_low) and is_brief_event:
                seg["sfx"] = "sigh"
            elif re.search(r'\b(phantom\s+murmurs?|eldritch\s+whispers?|voices?\s+coiling\s+in\s+(?:his|her)\s+head)\b', t_low):
                seg["sfx"] = "whisper"
            elif re.search(r'\b(unnatural\s+chill|temperature\s+dropped|chilling\s+presence)\b', t_low):
                seg["sfx"] = "haunt"
            elif re.search(r'\b(distant\s+howl|howl\s+tore\s+through|wolf\s+howl(?:ed|ing)?)\b', t_low):
                seg["sfx"] = "howl"
            elif re.search(r'\b(bells?\s+(?:chimed|tolled|rang)|alarm\s+bells?|death\s+knell)\b', t_low):
                seg["sfx"] = "bells"
            elif re.search(r'\b(war\s+drums?\s+beat|marching\s+drums?\s+echoed)\b', t_low):
                seg["sfx"] = "wardrum"
            elif re.search(r'\b(spiritual\s+gong|temple\s+gong|gong\s+sounded)\b', t_low):
                seg["sfx"] = "gong"
            elif re.search(r'\b(groaned\s+in\s+agony|sharp\s+gasp\s+of\s+pain|clutched\s+(?:his|her)\s+bleeding\s+wound)\b', t_low) and is_brief_event and seg.get("line_type") != "Dialogue":
                seg["sfx"] = "pain"
            elif re.search(r'\b(sizzled\s+in\s+the\s+pan|pot\s+bubbled\s+over|seared\s+the\s+meat)\b', t_low):
                seg["sfx"] = "cooking"
            elif re.search(r'\b(set\s+down\s+the\s+plates?|plates?\s+clattered|dishes\s+clattered\s+on\s+the\s+table)\b', t_low):
                seg["sfx"] = "dishes"
            elif re.search(r'\b(chewed\s+hungrily|chewing\s+the\s+meat|took\s+a\s+bite\s+of\s+(?:the\s+)?food)\b', t_low):
                seg["sfx"] = "eating"
            elif re.search(r'\b(bustling\s+market|vendors\s+shouting\s+their\s+wares|noisy\s+bazaar)\b', t_low):
                seg["sfx"] = "market"
            elif re.search(r'\b(stadium\s+erupted|crowd\s+cheered|applause\s+echoed)\b', t_low):
                seg["sfx"] = "cheer"
            elif re.search(r'\b(crowd\s+groaned|disappointed\s+murmurs?)\b', t_low):
                seg["sfx"] = "disappointed"
            elif re.search(r'\b(wind\s+howled\s+across|howling\s+gale)\b', t_low):
                seg["sfx"] = "wind"
            elif re.search(r'\b(primeval\s+forest|rustling\s+canopy)\b', t_low):
                seg["sfx"] = "forest"
            elif re.search(r'\b(waves\s+crashed\s+against|ocean\s+surf)\b', t_low):
                seg["sfx"] = "ocean"

        # =================================================================
        # SLIDING-WINDOW DEDUPLICATION & COOLDOWN FILTER
        # =================================================================
        recent_sfx = [r["sfx"] for r in refined_staged[-3:] if r.get("sfx")]
        if seg["sfx"] and seg["sfx"] in recent_sfx:
            seg["sfx"] = ""

        # Narration block splitting threshold
        if seg.get("line_type") == "Narration" and len(seg_text) > max_narr_merge:
            narr_splits = split_by_sentence_threshold(seg_text, threshold=max_narr_merge)
            sfx_assigned_to_split = False
            for split_txt in narr_splits:
                if clean_and_normalize_text(split_txt):
                    sub_seg = dict(seg)
                    sub_seg["text"] = split_txt
                    if sfx_assigned_to_split:
                        sub_seg["sfx"] = ""
                    else:
                        sub_seg["sfx"] = seg["sfx"]
                        sfx_assigned_to_split = True
                    refined_staged.append(sub_seg)
        else:
            refined_staged.append(seg)

    # Renumber sequentially
    for idx, seg in enumerate(refined_staged, 1):
        seg["line_id"] = f"{idx:04d}"

    if refined_staged:
        try:
            sync_new_characters_to_staging(stage_file, refined_staged)
        except Exception as sync_err:
            print(f"     [Staging Warning] Character sync encountered an issue: {sync_err}", flush=True)
        return refined_staged

    return fallback_rule_based_staging(raw_text, staged_chars, max_narr_merge)


# =====================================================================
# FALLBACK RULE-BASED STAGING
# =====================================================================

def fallback_rule_based_staging(text: str, char_map: dict, max_narr_merge: int = 650) -> list:
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
    for token in raw_tokens:
        if not token["is_quote"]:
            line_type = "System" if RE_SYSTEM.search(token["text"]) else "Narration"
            rk = "system" if line_type == "System" else "narrator"
            staged_segments.append({"role_key": rk, "line_type": line_type, "text": token["text"]})
        else:
            staged_segments.append({"role_key": "mc", "line_type": "Dialogue", "text": token["text"]})

    consolidated = []
    current_narr_buffer = []

    for seg in staged_segments:
        if seg["role_key"] == "narrator":
            current_narr_buffer.append(seg["text"])
        else:
            if current_narr_buffer:
                full_narr = " ".join(current_narr_buffer)
                for chunk in split_by_sentence_threshold(full_narr, threshold=max_narr_merge):
                    consolidated.append({"role_key": "narrator", "line_type": "Narration", "text": chunk})
                current_narr_buffer = []
            consolidated.append(seg)

    if current_narr_buffer:
        full_narr = " ".join(current_narr_buffer)
        for chunk in split_by_sentence_threshold(full_narr, threshold=max_narr_merge):
            consolidated.append({"role_key": "narrator", "line_type": "Narration", "text": chunk})

    staged_records = []
    for idx, seg in enumerate(consolidated, 1):
        rk = seg["role_key"]
        role_meta = char_map.get(rk, char_map.get("mc", FALLBACK_BASE_CHARACTERS["mc"]))
        voice = resolve_character_voice(rk, char_map, default_voice=role_meta.get("voice", "en-US-Christopher"))
        tp = seg["text"].strip()
        if not re.search(r'[.!?…]$', tp):
            tp = tp + "."

        sfx_val = ""
        t_low = tp.lower()
        is_brief_event = len(tp.split()) < 22

        if re.search(r'\b(gasp|gasps|gasped|sharp\s+intake\s+of\s+breath)\b', t_low) and is_brief_event:
            sfx_val = "gasp"
        elif re.search(r'\b(badump|thump-thump|heart\s+is\s+thundering|heart\s+thundering|heartbeat\s+starts|pounding\s+heart)\b', t_low) and is_brief_event:
            sfx_val = "heartbeat"
        elif re.search(r'\b(stomp|stomps|stomping|body\s+collapsed|collapsed\s+lifelessly|slammed\s+onto\s+the\s+ground)\b', t_low):
            sfx_val = "thud"
        elif re.search(r'\b(fidgeting\s+with\s+(?:my|her|his)\s+sleeves|straightening\s+(?:his|her)\s+coat|bow(?:s|ed)?\s+low|bow(?:s|ed)?\s+in\s+(?:perfect\s+)?sync|kneel(?:s|ed|ing)?\b.*?\bunison\b|kneel(?:s|ed|ing)?\s+before|outfit\s+adjusts)\b', t_low):
            sfx_val = "rustle"
        elif re.search(r'\b(sprint(?:s|ed|ing)?|dashes\s+forward|dashed\s+forward|fled\s+at\s+top\s+speed)\b', t_low):
            sfx_val = "run"
        elif re.search(r'\b(tiptoe(?:d|ing)?|cautious\s+steps?|creeping|sneaks?|sneaking)\b', t_low):
            sfx_val = "tiptoe"
        elif re.search(r'\b(carriage\s+rolled|wheels?\s+rattled|wagon\s+approached|horses?\s+trotted)\b', t_low):
            sfx_val = "horseandcart"
        elif re.search(r'\b(laced\s+(?:her|his|our)\s+fingers|fingers\s+slipped\s+through\s+mine)\b', t_low):
            sfx_val = "heartwarm"
        elif re.search(r'\b(sigh(?:ed|ing)?\s+in\s+relief|soft\s+sigh|weary\s+exhale)\b', t_low) and is_brief_event:
            sfx_val = "sigh"
        elif re.search(r'\b(phantom\s+murmurs?|eldritch\s+whispers?|voices?\s+coiling\s+in\s+(?:his|her)\s+head)\b', t_low):
            sfx_val = "whisper"
        elif re.search(r'\b(unnatural\s+chill|temperature\s+dropped|chilling\s+presence)\b', t_low):
            sfx_val = "haunt"
        elif re.search(r'\b(distant\s+howl|howl\s+tore\s+through|wolf\s+howl(?:ed|ing)?)\b', t_low):
            sfx_val = "howl"
        elif re.search(r'\b(bells?\s+(?:chimed|tolled|rang)|alarm\s+bells?|death\s+knell)\b', t_low):
            sfx_val = "bells"
        elif re.search(r'\b(war\s+drums?\s+beat|marching\s+drums?\s+echoed)\b', t_low):
            sfx_val = "wardrum"
        elif re.search(r'\b(spiritual\s+gong|temple\s+gong|gong\s+sounded)\b', t_low):
            sfx_val = "gong"
        elif re.search(r'\b(groaned\s+in\s+agony|sharp\s+gasp\s+of\s+pain|clutched\s+(?:his|her)\s+bleeding\s+wound)\b', t_low) and is_brief_event and seg["line_type"] != "Dialogue":
            sfx_val = "pain"
        elif re.search(r'\b(sizzled\s+in\s+the\s+pan|pot\s+bubbled\s+over|seared\s+the\s+meat)\b', t_low):
            sfx_val = "cooking"
        elif re.search(r'\b(set\s+down\s+the\s+plates?|plates?\s+clattered|dishes\s+clattered\s+on\s+the\s+table)\b', t_low):
            sfx_val = "dishes"
        elif re.search(r'\b(chewed\s+hungrily|chewing\s+the\s+meat|took\s+a\s+bite\s+of\s+(?:the\s+)?food)\b', t_low):
            sfx_val = "eating"
        elif re.search(r'\b(bustling\s+market|vendors\s+shouting\s+their\s+wares|noisy\s+bazaar)\b', t_low):
            sfx_val = "market"
        elif re.search(r'\b(stadium\s+erupted|crowd\s+cheered|applause\s+echoed)\b', t_low):
            sfx_val = "cheer"
        elif re.search(r'\b(crowd\s+groaned|disappointed\s+murmurs?)\b', t_low):
            sfx_val = "disappointed"
        elif re.search(r'\b(wind\s+howled\s+across|howling\s+gale)\b', t_low):
            sfx_val = "wind"
        elif re.search(r'\b(primeval\s+forest|rustling\s+canopy)\b', t_low):
            sfx_val = "forest"
        elif re.search(r'\b(waves\s+crashed\s+against|ocean\s+surf)\b', t_low):
            sfx_val = "ocean"

        # Sliding window deduplication
        recent_sfx = [r["sfx"] for r in staged_records[-3:] if r.get("sfx")]
        if sfx_val and sfx_val in recent_sfx:
            sfx_val = ""

        staged_records.append({
            "line_id": f"{idx:04d}",
            "speaker": role_meta.get("display_name", rk.title()),
            "gender": role_meta.get("gender", "Male"),
            "line_type": seg["line_type"],
            "text": tp,
            "voice": voice,
            "pitch": role_meta.get("pitch", "+0Hz"),
            "rate": role_meta.get("rate", "+5%"),
            "sfx": sfx_val
        })
    return staged_records


# =====================================================================
# ASYNC I/O WRAPPERS (aiofiles Integration)
# =====================================================================

async def save_staged_json_async(filepath: str, data: Dict[str, Any]) -> None:
    if ORJSON_AVAILABLE:
        raw_bytes = orjson.dumps(data, option=orjson.OPT_INDENT_2)
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(raw_bytes)
        else:
            with open(filepath, "wb") as f:
                f.write(raw_bytes)
    else:
        text_data = json.dumps(data, indent=2, ensure_ascii=False)
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(text_data)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text_data)


async def load_staged_json_async(filepath: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return None
    try:
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                content = await f.read()
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        return clean_and_parse_json(content)
    except Exception:
        return None