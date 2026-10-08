import os
import re
import json
import unicodedata
import urllib.parse
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from registry_utils import sync_new_characters_to_staging, FALLBACK_BASE_CHARACTERS

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

CONTAINER_SELECTORS = [
    ("div", {"id": "chr-content"}),                                                           # NovelBin
    ("div", {"id": "chapter-content"}),                                                       # NovelFull / MTL-Novel
    ("div", {"class": re.compile(r"(chapter-content|entry-content|epcontent|reading-content)", re.I)}), # MTL & WordPress
    ("div", {"class": "txt"}),                                                                # FreeWebNovel
    ("div", {"class": "m-read"}),                                                             # FreeWebNovel Reader
    ("div", {"id": "arrticle"}),                                                              # Ranobes
    ("article", {}),
]

RE_SYSTEM = re.compile(r"(?:\[|【|〔|『|〖|［)(Ding!|System|Notice|Warning|Announcement|Prompt|Quest|Stat|Skill|Level|Inventory|Reward).*?(?:\]|】|〕|』|〗|］)", re.I)
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
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
    # 1. Normalize Unicode symbols (turns mathematical bold/italic into standard ASCII)
    text = unicodedata.normalize('NFKC', text)
    text = text.translate(FULLWIDTH_TO_ASCII)
    text = RE_SCENE_DIVIDER.sub("", text)

    # 2. Strip watermarks
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

def scrape_chapter_content(session: requests.Session, url: str, ch_num: int, default_topic: str = "Arc"):
    print(f"[Scraper] Connecting to Ch.{ch_num:03d}: {url}", flush=True)
    resp = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Title Resolution (Works across MTL-Novel and FreeWebNovel)
    h1 = soup.find("h1") or soup.find("h2", class_=re.compile(r"(title|chapter-title)", re.I))
    raw_title = h1.get_text(strip=True) if h1 else f"Chapter {ch_num}"
    clean_title = clean_chapter_title_for_seo(raw_title, ch_num, default_topic)

    # Universal Container Detection
    container = None
    for tag, attrs in CONTAINER_SELECTORS:
        found = soup.find(tag, attrs)
        if found:
            container = found
            break
    if not container:
        container = soup.find("body")

    paragraphs = []
    for p in container.find_all("p"):
        ptxt = clean_and_normalize_text(p.get_text(strip=True))
        if ptxt and RE_ALPHANUM.search(ptxt):
            if re.search(r"^(?:freewebnovel|novelbin|mtl-novel|read novel)\b", ptxt, re.I):
                continue
            paragraphs.append(ptxt)

    if not paragraphs:
        paragraphs = [f"Chapter {ch_num}. Exposition details continue."]

    full_text = f"{clean_title}.\n\n" + "\n\n".join(paragraphs)

    # Universal Next Chapter Resolution
    next_url = None
    
    # 1. Target dedicated next buttons (FreeWebNovel / NovelBin / NovelFull)
    next_btn = soup.find("a", id=re.compile(r"next_chap", re.I)) or soup.find("a", class_=re.compile(r"next-chap", re.I))
    if next_btn and next_btn.get("href"):
        full_next = urllib.parse.urljoin(url, next_btn["href"].strip())
        if full_next != url:
            next_url = full_next

    # 2. Target general next links
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

    # 3. Target next chapter index regex pattern
    if not next_url:
        target_pattern = re.compile(rf"/chapter-{ch_num + 1}(?:[/-]|$)", re.I)
        for a in soup.find_all("a", href=True):
            if target_pattern.search(a["href"]):
                next_url = urllib.parse.urljoin(url, a["href"])
                break

    # 4. Deterministic URL substitution fallback (Works for both mtl-novel and freewebnovel)
    if not next_url:
        pattern_curr = re.compile(rf"(chapter[-_/]){ch_num}([/-]|$)", re.I)
        if pattern_curr.search(url):
            next_url = pattern_curr.sub(rf"\g<1>{ch_num + 1}\g<2>", url)

    return clean_title, full_text, next_url

def parse_chapter_via_gemini_director(client, title: str, raw_text: str, stage_file: str, max_narr_merge: int = 210) -> list:
    staged_chars = {}
    if os.path.exists(stage_file):
        try:
            with open(stage_file, "r", encoding="utf-8") as f:
                staged_chars = json.load(f).get("characters", {})
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

STRICT CHARACTER CONTINUITY DIRECTIVES:
1. GENDER LOCK: A female speaker must NEVER become male, and a male speaker must NEVER become female. Gender consistency is absolute.
2. CAST IDENTIFICATION: Match speakers against the staged character registry below. If an alias or epithet is used, map it to the canonical character.
3. NEW CHARACTER DISCOVERY: If a new character speaks who is NOT in this registry, clearly identify their exact name or title, determine their correct gender ('Male', 'Female', or 'Neutral'), and select an appropriate Edge-TTS neural voice.

ACTIVE STAGED CHARACTERS:
{registered_manifest_str}
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
                sync_new_characters_to_staging(stage_file, staged)
                return staged
    except Exception as e:
        print(f"     [Gemini Director Notice] {e}. Using fallback staging...", flush=True)

    return fallback_rule_based_staging(raw_text, staged_chars, max_narr_merge)

def fallback_rule_based_staging(text: str, char_map: dict, max_narr_merge: int = 210) -> list:
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
            rk = "player_system" if "player_system" in char_map and line_type == "System" else ("system" if line_type == "System" else "narrator")
            staged_segments.append({"role_key": rk, "line_type": line_type, "text": token["text"]})
        else:
            staged_segments.append({"role_key": "mc", "line_type": "Dialogue", "text": token["text"]})

    consolidated = []
    for seg in staged_segments:
        if consolidated and consolidated[-1]["role_key"] == "narrator" and seg["role_key"] == "narrator":
            if len(consolidated[-1]["text"].split()) + len(seg["text"].split()) <= max_narr_merge:
                consolidated[-1]["text"] += " " + seg["text"]
                continue
        consolidated.append(seg)

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
