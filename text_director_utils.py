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

# Fixed: Clean UTF-8 brackets and standard regex '|' alternates
RE_SYSTEM = re.compile(
    r"(?:\[\vert{}【\vert{}〖\vert{}『\vert{}《\vert{}［\vert{}\{)(Ding!\vert{}System\vert{}Notice\vert{}Warning\vert{}Announcement\vert{}Prompt\vert{}Quest\vert{}Stat\vert{}Skill\vert{}Level\vert{}Lv\.\vert{}Inventory\vert{}Reward).*?(?:\]|】|〗|』|》|］|\})",
    re.I
)
RE_SCENE_DIVIDER = re.compile(r"^(\s*[*~=_#-]\s*){3,}$", re.MULTILINE)

WATERMARK_PATTERNS = [
    re.compile(r"(?:free\s*web\s*novel|freewebnovel)\s*\.?\s*c[o0]m", re.I),
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
    re.compile(r"[\U0001D400-\U0001D7FF]+", re.UNICODE),
]

FULLWIDTH_TO_ASCII = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '「': '"', '」': '"',
    '，': ', ', '。': '. ', '！': '! ', '？': '? ',
    '：': ': ', '；': '; ', '（': '(', '）': ')'
})
RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')

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
        # Find last completed segment object
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
    default_voice: str = "en-US-GuyNeural",
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
# SCRAPING ENGINE (With DiskCache & Retries)
# =====================================================================

def scrape_chapter_content(session, url: str, ch_num: int, default_topic: str = "Arc") -> tuple[str, str, Optional[str]]:
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
    p_tags = sort_paragraphs_by_order_index(p_tags);

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


def parse_single_chunk_via_gemini(client, title: str, chunk_text: str, system_instruction: str, max_retries: int = 3) -> list:
    chunk_cache_key = make_cache_key("gemini_chunk", chunk_text)
    cached_segments = cache_get(chunk_cache_key)
    if cached_segments and isinstance(cached_segments, list) and len(cached_segments) > 0:
        return cached_segments

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
                        "rate": rate
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


def parse_chapter_via_gemini_director(client, title: str, raw_text: str, stage_file: str, max_narr_merge: int = 650) -> list:
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

    # Tightened director system instruction with phonetic, prosodic, and schema constraints
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
   - If an alias, title, or epithet is used, map it to the canonical character display name.
   - For unlisted characters, infer name and gender ('Male', 'Female', or 'Neutral') from surrounding context and assign an appropriate Edge-TTS neural voice.
   - Mark general narration and descriptive actions with speaker "Narrator", gender "Neutral", and line_type "Narration".
3. System & Interface Blocks: Screen prompts, level-up banners, and robotic notifications must be marked with speaker "System", gender "Neutral", and line_type "System".

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
  "voice": "en-US-GuyNeural"
}}

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

        part_staged = parse_single_chunk_via_gemini(client, title, part, system_instruction)

        # Directly trust Gemini output if it returned a valid parsed list
        if part_staged and isinstance(part_staged, list) and len(part_staged) > 0:
            all_staged.extend(part_staged)
        else:
            print(f"     [Gemini Fallback] Using rule-based staging for Part {p_idx}...", flush=True)
            fallback_part = fallback_rule_based_staging(part, staged_chars, max_narr_merge)
            all_staged.extend(fallback_part)

    refined_staged = []
    for seg in all_staged:
        # Harmonize legacy schema aliases if Gemini outputs alternate field keys
        if "speaker_role" in seg and "speaker" not in seg:
            seg["speaker"] = seg.pop("speaker_role")
        if "edge_tts_voice" in seg and "voice" not in seg:
            seg["voice"] = seg.pop("edge_tts_voice")

        # Fuzzy character voice lock & continuity enforcement
        sp = seg.get("speaker", "Narrator")
        current_voice = seg.get("voice", "en-US-GuyNeural")

        if seg.get("line_type") == "Dialogue":
            seg["voice"] = resolve_character_voice(sp, staged_chars, default_voice=current_voice)
        elif seg.get("line_type") == "System":
            seg["voice"] = "en-US-ChristopherNeural"
        elif seg.get("line_type") == "Narration" and not seg.get("voice"):
            seg["voice"] = staged_chars.get("Narrator", {}).get("voice", "en-US-GuyNeural")

        # Sentence-length management for narration blocks exceeding the merge threshold
        seg_text = seg.get("text", "")
        if seg.get("line_type") == "Narration" and len(seg_text) > max_narr_merge:
            narr_splits = split_by_sentence_threshold(seg_text, threshold=max_narr_merge)
            for split_txt in narr_splits:
                if clean_and_normalize_text(split_txt):
                    sub_seg = dict(seg)
                    sub_seg["text"] = split_txt
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
        voice = resolve_character_voice(rk, char_map, default_voice=role_meta.get("voice", "en-US-GuyNeural"))
        tp = seg["text"].strip()
        if not re.search(r'[.!?…]$', tp):
            tp = tp + "."
        staged_records.append({
            "line_id": f"{idx:04d}",
            "speaker": role_meta.get("display_name", rk.title()),
            "gender": role_meta.get("gender", "Male"),
            "line_type": seg["line_type"],
            "text": tp,
            "voice": voice,
            "pitch": role_meta.get("pitch", "+0Hz"),
            "rate": role_meta.get("rate", "+5%")
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
