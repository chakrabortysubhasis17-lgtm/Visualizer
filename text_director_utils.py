import os
import re
import time
import math
import unicodedata
import urllib.parse
import orjson
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from registry_utils import sync_new_characters_to_staging, FALLBACK_BASE_CHARACTERS

# Optional ftfy integration for deep text/mojibake fixing
try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    FTFY_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

CONTAINER_SELECTORS = [
    ("div", {"id": "chr-content"}),
    ("div", {"id": "chapter-content"}),
    ("div", {"class": re.compile(r"(chapter-content|entry-content|epcontent|reading-content)", re.I)}),
    ("div", {"class": "txt"}),
    ("div", {"class": "m-read"}),
    ("div", {"id": "arrticle"}),
    ("article", {}),
]

RE_SYSTEM = re.compile(r"(?:\[|【|〖|『|《|［|\{)(Ding!|System|Notice|Warning|Announcement|Prompt|Quest|Stat|Skill|Level|Lv\.|Inventory|Reward).*?(?:\]|】|〗|』|》|］|\})", re.I)
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
        base_pitch = 0
        base_rate = 5

    return f"{base_pitch:+d}Hz", f"{base_rate:+d}%"

def clean_chapter_title_for_seo(raw_title: str, ch_num: int, default_topic: str = "Arc") -> str:
    cleaned = unicodedata.normalize('NFKC', raw_title)
    cleaned = re.sub(r'^(?:chapter|ch\.?)\s*\d+[\s:\-–—]+(?:chapter|ch\.?)\s*\d+[\s:\-–—]*', '', cleaned, flags=re.I)
    cleaned = re.sub(r'^(?:chapter|ch\.?)\s*\d+[\s:\-–—]*', '', cleaned, flags=re.I).strip()
    if not cleaned:
        cleaned = f"{default_topic} Phase {ch_num}"
    return f"Ch {ch_num:03d}: {cleaned.title()}"

def clean_and_normalize_text(text: str) -> str:
    # Use ftfy if present to repair encoding defects prior to regex cleaning
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

def scrape_chapter_content(session, url: str, ch_num: int, default_topic: str = "Arc"):
    print(f"[Scraper] Connecting to Ch.{ch_num:03d}: {url}", flush=True)

    try:
        if isinstance(session, httpx.Client):
            resp = session.get(url, headers=HEADERS, timeout=25.0, follow_redirects=True)
        else:
            resp = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    except TypeError:
        resp = session.get(url, headers=HEADERS, timeout=25)

    resp.raise_for_status()

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
    if len(p_tags) >= 3:
        for p in p_tags:
            ptxt = clean_and_normalize_text(p.get_text(strip=True))
            if ptxt and RE_ALPHANUM.search(ptxt):
                if re.search(r"^(?:freewebnovel|novelbin|mtl-novel|read novel)\b", ptxt, re.I):
                    continue
                paragraphs.append(ptxt)
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
        pattern_curr = re.compile(rf"(chapter[-_/]){ch_num}([/-]|$)", re.I)
        if pattern_curr.search(url):
            next_url = pattern_curr.sub(rf"\g<1>{ch_num + 1}\g<2>", url)

    return clean_title, full_text, next_url

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
                data = orjson.loads(raw_json)
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
                staged_chars = orjson.loads(f.read()).get("characters", {})
        except Exception:
            pass

    if not staged_chars:
        staged_chars = FALLBACK_BASE_CHARACTERS

    if not client or not GENAI_AVAILABLE:
        return fallback_rule_based_staging(raw_text, staged_chars, max_narr_merge)

    char_manifest = []
    for c_key, c_val in staged_chars.items():
        disp = c_val.get("display_name", c_key.title())
        gender = c_val.get("gender", "Male")
        voice = c_val.get("voice", "en-US-GuyNeural")
        aliases = ", ".join(c_val.get("aliases", [c_key]))
        char_manifest.append(f"• {disp} | GENDER: {gender} | VOICE: {voice} | ALIASES: [{aliases}]")

    registered_manifest_str = "\n".join(char_manifest)

    system_instruction = f"""
You are an expert audio drama script director and phonetic supervisor.
Analyze the chapter text, cleanly separating narration, dialogue, and system prompts.

STRICT CONTINUITY DIRECTIVES:
1. COMPLETE ADAPTATION: Every line of the text must appear in the final manifest. Do not omit exposition, internal thoughts, or stat lines.
2. GENDER LOCK: A female speaker must NEVER become male, and a male speaker must NEVER become female.
3. CAST IDENTIFICATION: Match speakers against the staged character registry below. If an alias or epithet is used, map it to the canonical character.
4. NEW CHARACTER DISCOVERY: If a new character speaks who is NOT in this registry, identify their name, determine their gender ('Male', 'Female', or 'Neutral'), and assign an appropriate Edge-TTS neural voice.
5. FORMAT: Return a JSON object with a single key "segments" containing an array of objects with keys: line_id, speaker_role, gender, age_category, emotion, line_type, edge_tts_voice, text.

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
        if part_staged:
            all_staged.extend(part_staged)
        else:
            print(f"     [Gemini Fallback] Using rule-based staging for Part {p_idx}...", flush=True)
            fallback_part = fallback_rule_based_staging(part, staged_chars, max_narr_merge)
            all_staged.extend(fallback_part)

    refined_staged = []
    for seg in all_staged:
        if seg.get("line_type") == "Narration" and len(seg.get("text", "")) > max_narr_merge:
            narr_splits = split_by_sentence_threshold(seg["text"], threshold=max_narr_merge)
            for split_txt in narr_splits:
                sub_seg = dict(seg)
                sub_seg["text"] = split_txt
                refined_staged.append(sub_seg)
        else:
            refined_staged.append(seg)

    for idx, seg in enumerate(refined_staged, 1):
        seg["line_id"] = f"{idx:04d}"

    if refined_staged:
        sync_new_characters_to_staging(stage_file, refined_staged)
        return refined_staged

    return fallback_rule_based_staging(raw_text, staged_chars, max_narr_merge)

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
        tp = seg["text"].strip()
        if not re.search(r'[.!?…]$', tp):
            tp = tp + "."
        staged_records.append({
            "line_id": f"{idx:04d}",
            "speaker": role_meta.get("display_name", rk.title()),
            "gender": role_meta.get("gender", "Male"),
            "line_type": seg["line_type"],
            "text": tp,
            "voice": role_meta.get("voice", "en-US-GuyNeural"),
            "pitch": role_meta.get("pitch", "+0Hz"),
            "rate": role_meta.get("rate", "+5%")
        })
    return staged_records