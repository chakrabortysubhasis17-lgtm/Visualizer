import os
import re
import json
import time
import random
import shutil
import asyncio
import subprocess
import urllib.parse
import requests
from bs4 import BeautifulSoup
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from entity_manager import EntityManager

# ==================== ARCHITECTURAL TUNING ====================
START_CHAPTER = 101
END_CHAPTER = 150
BATCH_SIZE = 5
PARALLEL_CHAPTERS = 2
GLOBAL_MAX_CONCURRENT_TTS = 3
MAX_NARRATION_MERGE_WORDS = 210
TARGET_DIALOGUE_CHUNK_WORDS = 65

CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"

FORBIDDEN_TERMS = [
    re.compile(r"\bchest\b", re.I),
    re.compile(r"\btattoos?\b", re.I),
    re.compile(r"\bbloodshed\b", re.I),
    re.compile(r"\bdeformed\b", re.I),
    re.compile(r"\bporcelain\b", re.I),
    re.compile(r"\bethereal\b", re.I),
    re.compile(r"\bmutilated\b", re.I)
]

GRADIENT_PALETTES = [
    ((255, 245, 220), (255, 180, 90)),   # Radiant Gold -> Warm Amber
    ((230, 255, 235), (120, 220, 160)),  # Ethereal Emerald -> Jade Glow
    ((255, 255, 255), (200, 225, 255)),  # Pure White -> Celestial Azure
]

NOVEL_SLUG = "national-fate-marriage-the-elf-queen-is-pregnant-at-the-start"
START_URL = "https://mtl-novel.com/novel/national-fate-marriage-the-elf-queen-is-pregnant-at-the-start/chapter-101-perfect-score-in-theory-zero-in-practice/"
BUILD_DIR = "build_marriage_101_150"
FINAL_AUDIO = "output_marriage_101_150.mp3"
FINAL_VIDEO = "final_marriage_101_150.mp4"
COVER_IMAGE = "cover_marriage_101_150.jpg"
TIMESTAMPS_FILE = "youtube_timestamps_marriage_101_150.txt"
SUBTITLES_FILE = "subtitles_marriage_101_150.srt"
PAYLOAD_FILE = "youtube_upload_payload_marriage_101_150.json"

VIDEO_TITLE = "Trial of the Moon Goddess & S+ Hanging Gardens! National Fate Audiobook Marathon [Ch 101-150]"
TAGS = [
    "National Fate Audiobook", "National Fate Marriage the Elf Queen is Pregnant at the Start",
    "Xiao Haoyan", "Hecate", "Moon Goddess", "Dragon Kingdom", "Elf Queen",
    "Progression Fantasy", "Unabridged Audiobook", "Audiobook Marathon", "Being A Bong"
]

DESC_HEADER = (
    "While foreign competitors struggle with flawed theoretical survival guides, Xiao Haoyan shatters "
    "the National Fate Game with unmatched divine marriages and god-tier territory expansions!\n\n"
    "Reuniting with Hecate, conquering petrifying demon eye trials, and unlocking the celestial S+ Hanging Gardens, "
    "Xiao Haoyan extends the Dragon Kingdom's prosperity while foreign rivals like Tojo Kotaro face crushing humiliation!\n\n"
    "Welcome to Chapters 101 to 150 of 'National Fate: Marriage, the Elf Queen is Pregnant at the Start' "
    "(国运婚配：开局精灵女王怀孕) in unabridged multi-voice narration!\n\n"
    "🎧 AUDIO MASTER: Mobile-Engineered Speech Standard (-14 LUFS, Broadcast Clarity).\n"
    "📖 CLOSED CAPTIONS: English Soft Subtitles (CC Enabled for dialogue and system announcements).\n"
    "🎨 VISUAL ENGINE: 10 Progressive High-Fantasy Transitions + 15s Channel Outro Slate.\n\n"
    "══════════════════════════════════════════════\nTIMESTAMPS:\n"
)

DESC_FOOTER = (
    "\n══════════════════════════════════════════════\n\n"
    "🌟 ARC HIGHLIGHTS:\n"
    "• 00:00:00 - Chapter 101: Perfect Score in Theory, Zero in Practice?\n"
    "• Chapter 103: Hecate's Affectionate Welcome & Sanctuary Return\n"
    "• Chapter 110: Petrifying Demon Eyes Confrontation\n"
    "• Chapter 115: S+ Rank Hanging Gardens Homestead Unlocked\n"
    "• Chapter 129: Moon Goddess Trial & The Lunar Shrine Conquest\n"
    "• Chapter 150: The Insect Pyramid Ambush Annihilated!\n\n"
    "══════════════════════════════════════════════\n"
    "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for storytelling, entertainment, "
    "and fantasy literature commentary. All original story concepts belong to the original author. Subscribe for more!\n\n"
    "#NationalFate #XiaoHaoyan #ElfQueen #Audiobook #ProgressionFantasy #LitRPG #FullAudiobook #AudiobookMarathon"
)

BASE_CHARACTERS = {
    "narrator": {"display_name": "Narrator", "gender": "Female", "line_type": "Narration", "voice": "en-US-JennyNeural", "pitch": "+1Hz", "rate": "+4%"},
    "mc": {"display_name": "Xiao Haoyan", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+6%"},
    "hecate": {"display_name": "Hecate", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-AriaNeural", "pitch": "+1Hz", "rate": "+5%"},
    "elf_queen": {"display_name": "Elf Queen", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-EmmaNeural", "pitch": "+2Hz", "rate": "+5%"},
    "moon_goddess": {"display_name": "Moon Goddess", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-JennyNeural", "pitch": "+3Hz", "rate": "+4%"},
    "tojo_kotaro": {"display_name": "Tojo Kotaro", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-EricNeural", "pitch": "+6Hz", "rate": "+10%"},
    "foreign_rival": {"display_name": "Foreign Competitor", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-EricNeural", "pitch": "+5Hz", "rate": "+10%"},
    "command_general": {"display_name": "General", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-RogerNeural", "pitch": "-6Hz", "rate": "+2%"},
    "system": {"display_name": "National Fate System", "gender": "Synthetic", "line_type": "System", "voice": "en-US-SteffanNeural", "pitch": "-18Hz", "rate": "-6%"}
}

BLOCKS = [
    {
        "index": 1, "range": (101, 105),
        "hero_desc": "handsome Chinese youth Xiao Haoyan wearing starry sky embroidered robes sitting on a jade couch",
        "action": "welcoming the affectionate goddess Hecate in dark purple silk robes smiling warmly as she holds his hand",
        "scene_bg": "luxurious celestial bridal sanctuary chamber, floating golden lanterns, soft ethereal glow",
        "search_query": "anime fantasy male hero goddess purple silk robes sanctuary",
        "title": ["HECATE'S DEVOTION", "THEORY VS REALITY", "Chapters 101 – 105"],
        "fallback_color": (40, 25, 45)
    },
    {
        "index": 2, "range": (106, 110),
        "hero_desc": "Xiao Haoyan standing fearless with glowing golden pupils gazing straight into a terrifying giant petrifying demon eye",
        "action": "raising his hand surrounded by golden divine flames that shatter the stone petrification curse in mid-air",
        "scene_bg": "ancient dark stone dungeon chamber, glowing cursed purple runes, shattered stone debris",
        "search_query": "anime swordsman golden aura shattering purple magic eye curse",
        "title": ["PETRIFYING DEMON EYE", "SHATTERING THE CURSE", "Chapters 106 – 110"],
        "fallback_color": (35, 20, 45)
    },
    {
        "index": 3, "range": (111, 115),
        "hero_desc": "breathtaking celestial S+ rank Hanging Gardens floating gracefully above the white clouds",
        "action": "cascading crystal waterfalls pouring into rainbow mist with rare immortal spirit herbs blooming across terraces",
        "scene_bg": "floating fantasy palace terraces, rainbow waterfalls, lush blooming magical flowers under golden sun",
        "search_query": "anime hanging gardens floating palace waterfalls fantasy",
        "title": ["S+ HANGING GARDENS", "TERRITORY EXPANSION", "Chapters 111 – 115"],
        "fallback_color": (30, 45, 35)
    },
    {
        "index": 4, "range": (116, 120),
        "hero_desc": "sleek futuristic silver-haired mecha girl with glowing cyan energy joints and metallic armor plates",
        "action": "kneeling respectfully on one knee before Xiao Haoyan presenting a glowing holographic data core",
        "scene_bg": "high-tech docking bay inside celestial palace, holographic blue interface rings floating in the air",
        "search_query": "anime mecha girl knight kneeling sci-fi fantasy",
        "title": ["MECHA MAIDEN", "CORE PROTOCOL BIND", "Chapters 116 – 120"],
        "fallback_color": (25, 40, 50)
    },
    {
        "index": 5, "range": (121, 125),
        "hero_desc": "rival explorer Tojo in gray tactical armor running anxiously through a foggy ancient stone corridor",
        "action": "looking back wide-eyed as massive glowing red holographic warning screens flash across the sky",
        "scene_bg": "dark mist-shrouded citadel ruins, glowing crimson phantom lights in the shadows, crumbling stone arches",
        "search_query": "anime soldier running ruined dark fantasy mist city",
        "title": ["FOREIGN HUMILIATION", "SANCTUARY COLLAPSE", "Chapters 121 – 125"],
        "fallback_color": (35, 30, 25)
    },
    {
        "index": 6, "range": (126, 130),
        "hero_desc": "ethereal Moon Goddess with long flowing silver hair and crescent moon headdress floating in silver moonlight",
        "action": "gazing down with serene majesty from an ornate crescent moon throne floating inside a sacred lunar pavilion",
        "scene_bg": "lunar shrine courtyard, pure white marble pillars, glowing silver lotus pond, starry cosmos night sky",
        "search_query": "anime moon goddess silver hair crescent throne starry sky",
        "title": ["LUNAR SHRINE CONQUEST", "THE MOON GODDESS", "Chapters 126 – 130"],
        "fallback_color": (30, 35, 55)
    },
    {
        "index": 7, "range": (131, 135),
        "hero_desc": "Xiao Haoyan drawing a radiant solar longsword glowing with brilliant golden celestial dawn flames",
        "action": "channeling radiant golden solar energy into his sword to illuminate the night sky with divine aura",
        "scene_bg": "crystalline lunar temple platform, pure silver moonbeams, floating golden embers, starry cosmos sky",
        "search_query": "anime swordsman golden fire solar blade starry night",
        "title": ["TRIAL OF THE MOON", "SOLAR SWORD STRIKE", "Chapters 131 – 135"],
        "fallback_color": (45, 35, 20)
    },
    {
        "index": 8, "range": (136, 140),
        "hero_desc": "divine celestial azure dragon ascending majestically through golden clouds at peak grandeur",
        "action": "soaring across the sky as concentric golden blessing halos descend over a thriving modern metropolis",
        "scene_bg": "golden sunrise skies over modern futuristic skyline, divine dragon coiling gracefully, sparkling light",
        "search_query": "anime eastern divine dragon golden clouds modern city blessing",
        "title": ["DRAGON ASCENSION", "NATIONWIDE LONGEVITY", "Chapters 136 – 140"],
        "fallback_color": (45, 40, 25)
    },
    {
        "index": 9, "range": (141, 145),
        "hero_desc": "Xiao Haoyan standing in royal robes alongside the radiant Elf Queen Luan Ying and the Moon Goddess",
        "action": "overlooking a vast flourishing empire as the ancient World Tree releases emerald waves of life aura",
        "scene_bg": "grand palace marble terrace, giant glowing World Tree on the horizon, blooming gardens, warm sunlight",
        "search_query": "anime emperor with elf queen and moon goddess fantasy terrace",
        "title": ["DIVINE CONSORTS", "HARMONY OF THE REALM", "Chapters 141 – 145"],
        "fallback_color": (35, 45, 30)
    },
    {
        "index": 10, "range": (146, 150),
        "hero_desc": "Xiao Haoyan drawing a massive celestial golden bow surrounded by spinning stellar constellations",
        "action": "releasing a supreme astral arrow that creates a towering golden pillar of starlight across the canyon",
        "scene_bg": "vast rocky desert canyon under twilight sky, immense vertical pillar of golden stellar light",
        "search_query": "anime archer golden celestial arrow beam canyon landscape",
        "title": ["DIVINE STAR ARROW", "SUPREME CELESTIAL STRIKE", "Chapters 146 – 150"],
        "fallback_color": (50, 35, 20)
    }
]

RE_SYSTEM = re.compile(r"(?:\[|【|〔|『|〖|［)(Ding!|System|Notice|Warning|Announcement|National Fate).*?(?:\]|】|〕|』|〗|］)", re.I)
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
RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def load_characters_and_vocatives(slug: str, base_defaults: dict) -> tuple:
    char_map = dict(base_defaults)
    voc_map = {}
    reg_file = "novel_entities_registry.json"
    if os.path.exists(reg_file):
        try:
            with open(reg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if slug in data:
                reg_chars = data[slug].get("characters", {})
                voc_map = data[slug].get("vocatives", {})
                print(f"[{slug}] Linked {reg_file}: {len(reg_chars)} characters, {len(voc_map)} vocatives indexed.", flush=True)
                for name, cinfo in reg_chars.items():
                    entry = {
                        "display_name": name.title(),
                        "gender": cinfo.get("gender", "Male"),
                        "line_type": "Dialogue" if cinfo.get("role") != "system" else "System",
                        "voice": cinfo.get("voice", "en-US-GuyNeural"),
                        "pitch": cinfo.get("pitch", "+0Hz"),
                        "rate": cinfo.get("rate", "+6%"),
                        "aliases": cinfo.get("aliases", [])
                    }
                    char_map[name.lower()] = entry
                    char_map[cinfo.get("role", name)] = entry
                    for alias in entry["aliases"]:
                        char_map[alias.lower()] = entry
        except Exception as e:
            print(f"[{slug}] Warning: Registry sync failed: {e}", flush=True)
    return char_map, voc_map


def calculate_chunk_timeout(text: str) -> float:
    return max(35.0, 25.0 + (len(text.split()) * 0.40))


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
    title = h1.get_text(strip=True) if h1 else f"Chapter {ch_num}"

    container = soup.find("article") or \
                soup.find("div", class_=re.compile(r"(chapter-content|entry-content|epcontent|post-content|reading-content)", re.I)) or \
                soup.find("div", id=re.compile(r"(chapter-content|content|article)", re.I)) or \
                soup.find("body")

    paragraphs = [clean_and_normalize_text(p.get_text(strip=True)) for p in container.find_all("p")]
    paragraphs = [p for p in paragraphs if p and RE_ALPHANUM.search(p)]

    if not paragraphs:
        paragraphs = [f"Chapter {ch_num}. The national fate sanctuary expands peacefully."]

    full_text = f"{title}.\n\n" + "\n\n".join(paragraphs)

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

    return title, full_text, next_url


def classify_marriage_dialogue(chunk: str, prev_narr: str, next_narr: str) -> str:
    chunk_lower = chunk.lower()
    prev_lower = prev_narr.lower()
    next_lower = next_narr.lower()

    # 1. System Prompt Announcements
    if any(k in chunk_lower or k in prev_lower for k in [
        "national fate prompt", "worldwide announcement", "reward has been issued",
        "congratulations to dragon kingdom", "bind marriage successfully", "divine blessing", "ding!"
    ]):
        return "system"

    # 2. Hecate
    if any(k in prev_lower for k in ["hecate whispered", "hecate smiled", "mistress of magic", "goddess hecate"]):
        return "hecate"
    if any(k in chunk_lower for k in ["husband! you're finally back", "hecate has been waiting", "my magic is yours"]):
        return "hecate"

    # 3. Moon Goddess
    if any(k in prev_lower for k in ["moon goddess spoke", "lunar maiden murmured", "goddess of the moon"]):
        return "moon_goddess"
    if any(k in chunk_lower for k in ["lunar shrine", "moonlight blessing", "mortal who conquered the lunar trial"]):
        return "moon_goddess"

    # 4. Elf Queen (Luan Ying)
    if re.search(r"\b(queen\s+(?:whispered|smiled|murmured|sighed|asked|blushed)|elf\s+queen|luan\s+ying)\b", prev_lower):
        return "elf_queen"

    # 5. Tojo Kotaro & Foreign Rivals
    if any(k in prev_lower for k in ["tojo kotaro roared", "sakura player cursed", "tojo screamed", "foreign player sneered"]):
        return "tojo_kotaro"
    if any(k in chunk_lower for k in ["impossible! why is dragon kingdom so lucky", "damn xiao haoyan", "how did he get s+ gardens"]):
        return "tojo_kotaro"

    # 6. Command Headquarters General
    if any(k in prev_lower for k in ["general instructed", "headquarters commander", "veteran general said", "command center ordered"]):
        return "command_general"

    # 7. Post-Context Tags
    if re.search(r"\b(hecate\s+said|hecate\s+smiled)\b", next_lower):
        return "hecate"
    if re.search(r"\b(xiao\s+haoyan\s+smiled|xiao\s+haoyan\s+replied|he\s+said|he\s+chuckled)\b", next_lower):
        return "mc"
    if re.search(r"\b(tojo\s+kotaro\s+cursed|tojo\s+screamed)\b", next_lower):
        return "tojo_kotaro"

    # 8. Addressee Detection inside Quote
    if re.search(r"\b(husband|my\s+king)\b", chunk_lower):
        return "elf_queen"

    # 9. Protagonist Phrasing (Xiao Haoyan / Su Chen)
    if any(k in chunk_lower for k in [
        "open the system reward", "claim reward", "don't worry", "hanging gardens", "activate celestial barrier"
    ]):
        return "mc"

    return "mc"


def parse_chapter_to_staged_json(text: str, entity_mgr: EntityManager, char_map: dict, voc_map: dict) -> list:
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
            if i % 2 == 0:
                raw_tokens.append({"is_quote": False, "text": chunk})
            else:
                raw_tokens.append({"is_quote": True, "text": chunk})

    staged_segments = []

    for idx, token in enumerate(raw_tokens):
        if not token["is_quote"]:
            line_type = "System" if RE_SYSTEM.search(token["text"]) else "Narration"
            role_key = "system" if line_type == "System" else "narrator"
            staged_segments.append({"role_key": role_key, "line_type": line_type, "text": token["text"]})
        else:
            prev_narr = ""
            for back_idx in range(idx - 1, -1, -1):
                if not raw_tokens[back_idx]["is_quote"]:
                    prev_narr = raw_tokens[back_idx]["text"][-75:]
                    break

            next_narr = ""
            for fwd_idx in range(idx + 1, len(raw_tokens)):
                if not raw_tokens[fwd_idx]["is_quote"]:
                    next_narr = raw_tokens[fwd_idx]["text"][:75]
                    break

            role_key = classify_marriage_dialogue(token["text"], prev_narr, next_narr)

            if role_key == "system":
                staged_segments.append({"role_key": "system", "line_type": "System", "text": token["text"]})
            elif role_key == "narrator":
                staged_segments.append({"role_key": "narrator", "line_type": "Narration", "text": token["text"]})
            else:
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
        role_meta = char_map.get(rk, char_map.get(rk.replace(" ", "_"), char_map.get("mc", char_map["narrator"])))
        words = seg["text"].split()
        sub_chunks = []
        chunk_ceiling = MAX_NARRATION_MERGE_WORDS if seg["line_type"] == "Narration" else TARGET_DIALOGUE_CHUNK_WORDS
        if len(words) <= chunk_ceiling:
            sub_chunks.append(seg["text"])
        else:
            sentences = RE_SENTENCE_SPLIT.split(seg["text"])
            curr_words = []
            for s in sentences:
                s_words = s.split()
                if len(curr_words) + len(s_words) > chunk_ceiling and curr_words:
                    sub_chunks.append(" ".join(curr_words))
                    curr_words = s_words
                else:
                    curr_words.extend(s_words)
            if curr_words:
                sub_chunks.append(" ".join(curr_words))

        for text_piece in sub_chunks:
            tp = text_piece.strip()
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


def construct_dynamic_scene_prompt(hero_desc: str, dynamic_action: str, scene_bg: str) -> str:
    cleaned_action = dynamic_action
    for forbidden in FORBIDDEN_TERMS:
        cleaned_action = forbidden.sub("glorious aura", cleaned_action)
    return (
        f"{hero_desc}, {cleaned_action}. "
        f"Background: {scene_bg}. "
        f"Detailed expressive anime face, sharp detailed eyes, distinct facial features, "
        f"official manhwa cover art, vibrant colors, clean sharp lineart, 8k resolution, cinematic lighting."
    )


def fit_and_crop_1080p(img: Image.Image) -> Image.Image:
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

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def fetch_flux_native_1080p(prompt: str, out_path: str, search_query: str = "") -> bool:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return True

    encoded = urllib.parse.quote(prompt)
    seed = random.randint(10000, 9999999)

    pollinations_urls = [
        (f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed}", "Pollinations Auto 720p", 40),
        (f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed+1}&model=flux", "Pollinations Flux 720p", 50),
        (f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576&seed={seed+2}&model=turbo", "Pollinations Turbo 576p", 35)
    ]

    for attempt, (url, label, req_timeout) in enumerate(pollinations_urls, 1):
        try:
            print(f"     [Image Engine] Requesting {label} (Attempt {attempt}/{len(pollinations_urls)})...", flush=True)
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=req_timeout)
            if resp.status_code == 200 and len(resp.content) > 15000:
                raw_temp = out_path + ".tmp.jpg"
                with open(raw_temp, "wb") as f:
                    f.write(resp.content)
                img = Image.open(raw_temp).convert("RGBA")
                w, h = img.size
                img = img.crop((0, 0, w, h - int(h * 0.055)))
                img.convert("RGB").save(out_path, "JPEG", quality=98)
                try: os.remove(raw_temp)
                except OSError: pass
                print(f"     [Image Engine] {label} successfully synthesized ({len(resp.content)} bytes).", flush=True)
                return True
        except Exception as e:
            print(f"     [Image Engine] {label} attempt failed: {e}", flush=True)
        time.sleep(2)

    return False


def apply_lower_third_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(overlay)
    vig_start = int(height * 0.82)
    for y in range(vig_start, height):
        alpha = int(80 * (((y - vig_start) / (height - vig_start)) ** 1.3))
        v_draw.line([(0, y), (width, y)], fill=(15, 25, 20, alpha))
    return Image.alpha_composite(base.convert("RGBA"), overlay)


def stamp_channel_watermark(base: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(base)
    wx, wy = 55, 45
    crest_r = 22
    draw.ellipse([(wx - crest_r, wy - crest_r), (wx + crest_r, wy + crest_r)], fill=(210, 160, 50, 255), outline=(255, 245, 220, 255), width=2)
    star_font = None
    for fp in ["C:/Windows/Fonts/seguisym.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(fp):
            try:
                star_font = ImageFont.truetype(fp, 24)
                break
            except Exception:
                pass
    if not star_font:
        star_font = ImageFont.load_default()
    bbox_star = draw.textbbox((0, 0), "✦", font=star_font)
    sw = bbox_star[2] - bbox_star[0]
    sh = bbox_star[3] - bbox_star[1]
    draw.text((wx - (sw // 2), wy - (sh // 2) - 2), "✦", fill=(255, 255, 255, 255), font=star_font)
    name_fp = "C:/Windows/Fonts/arialbd.ttf"
    if not os.path.exists(name_fp):
        name_fp = ensure_cinzel_font()
    name_font = ImageFont.truetype(name_fp, 36)
    handle_font = ImageFont.truetype(name_fp, 22)
    tx = wx + 36
    draw.text((tx + 2, wy - 18 + 2), "Being a Bong", fill=(25, 20, 10, 255), font=name_font)
    draw.text((tx, wy - 18), "Being a Bong", fill=(255, 255, 255, 255), font=name_font)
    draw.text((tx + 1, wy + 20 + 1), "@beingabong", fill=(20, 15, 10, 220), font=handle_font)
    draw.text((tx, wy + 20), "@beingabong", fill=(255, 220, 120, 255), font=handle_font)
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
    draw = ImageDraw.Draw(base)

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else title_font
        bbox = draw.textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)
        draw.text((x + 3, y + 4), line, font=active_font, fill=(20, 30, 20, 255), stroke_width=5, stroke_fill=(20, 30, 20, 255))
        draw.text((x, y), line, font=active_font, fill=(35, 55, 35, 255), stroke_width=3, stroke_fill=(35, 55, 35, 255))
        palette = GRADIENT_PALETTES[min(i, len(GRADIENT_PALETTES) - 1)]
        grad_layer = create_vertical_gradient_text_mask(text_w + 20, text_h + 20, line, active_font, palette[0], palette[1])
        base.paste(grad_layer, (x, y), grad_layer)
    return base


def ensure_block_cover_jit(cfg: dict, build_dir: str):
    out_file = cfg["cover_file"]
    raw_art = os.path.join(build_dir, f"raw_block_{cfg['index']}.jpg")

    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        print(f"[{NOVEL_SLUG}] [Cached Image] Block {cfg['index']} Cover ready: '{out_file}'", flush=True)
        return

    dynamic_prompt = construct_dynamic_scene_prompt(cfg["hero_desc"], cfg["action"], cfg["scene_bg"])
    search_kw = cfg.get("search_query", "anime fantasy male hero goddess")
    fetch_flux_native_1080p(dynamic_prompt, raw_art, search_query=search_kw)

    if os.path.exists(raw_art) and os.path.getsize(raw_art) > 10000:
        raw_img = Image.open(raw_art).convert("RGBA")
        base = fit_and_crop_1080p(raw_img)
    else:
        print(f"[{NOVEL_SLUG}] [Image Engine] Generation fallback applied for Block {cfg['index']}.", flush=True)
        base = Image.new("RGBA", (1920, 1080), (*cfg["fallback_color"], 255))

    base = base.filter(ImageFilter.UnsharpMask(radius=2.4, percent=180, threshold=2))
    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base)
    base = stamp_3d_metallic_flame_typography(base, cfg["title"])
    base.convert("RGB").save(out_file, "JPEG", quality=98)
    print(f"[{NOVEL_SLUG}] [Saved Image] Block {cfg['index']} Cover: '{out_file}'", flush=True)


def create_dynamic_outro_slate(out_path: str):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return
    base = Image.new("RGB", (1920, 1080), (20, 28, 24))
    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base)
    draw = ImageDraw.Draw(base)
    font_path = ensure_cinzel_font()
    head_font = ImageFont.truetype(font_path, 54)
    cta_font = ImageFont.truetype(font_path, 42)
    line1 = "NEXT CHAPTERS COMING SOON"
    line2 = "SUBSCRIBE FOR THE NEXT MARATHON"
    for i, txt in enumerate([line1, line2]):
        font = head_font if i == 0 else cta_font
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        x = (1920 - tw) // 2
        y = 480 + (i * 80)
        draw.text((x + 3, y + 4), txt, font=font, fill=(10, 15, 12, 255))
        draw.text((x, y), txt, font=font, fill=(255, 230, 140, 255) if i == 0 else (255, 255, 255, 255))
    base.convert("RGB").save(out_path, "JPEG", quality=95)
    print(f"[{NOVEL_SLUG}] [Outro Slate] Generated 15s outro card: '{out_path}'", flush=True)


def generate_50ch_ensemble_cover(slug: str, build_dir: str, master_cover_path: str, entity_mgr: EntityManager, char_map: dict):
    print(f"\n[{slug}] [Phase 5] Synthesizing Multi-Character Master Cover from 50-Chapter Registry...", flush=True)

    ensemble_prompt = (
        "Grand fantasy anime ensemble composition, waist-up view. Handsome Chinese sovereign hero Xiao Haoyan with starry robes "
        "stands confident in imperial attire. Beside him is the beautiful smiling Elf Queen Luan Ying and the graceful Moon Goddess in lunar headdress, "
        "holding his arms lovingly. In the background rises the celestial S-rank Hanging Gardens palace terraces under a radiant golden sunrise, "
        "falling flower petals, clean sharp lines, official manhwa cover art, vibrant colors, 8k resolution."
    )

    raw_ensemble = os.path.join(build_dir, "raw_master_cover_ensemble.jpg")
    fetch_flux_native_1080p(ensemble_prompt, raw_ensemble, search_query="anime fantasy emperor elf queen moon goddess palace")

    if os.path.exists(raw_ensemble) and os.path.getsize(raw_ensemble) > 10000:
        raw_img = Image.open(raw_ensemble).convert("RGBA")
        base = fit_and_crop_1080p(raw_img)
    else:
        print(f"[{slug}] [Cover Warning] Fallback applied for ensemble cover.", flush=True)
        base = Image.new("RGBA", (1920, 1080), (35, 45, 30, 255))

    base = base.filter(ImageFilter.UnsharpMask(radius=2.4, percent=180, threshold=2))
    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base)

    master_title_lines = [
        "NATIONAL FATE MARRIAGE",
        "THE ELF QUEEN IS PREGNANT",
        "Complete Marathon • Ch. 101–150"
    ]
    base = stamp_3d_metallic_flame_typography(base, master_title_lines)
    base.convert("RGB").save(master_cover_path, "JPEG", quality=98)
    print(f"[{slug}] [Master Thumbnail Complete] Saved Multi-Character Cover to '{master_cover_path}'", flush=True)


async def synthesize_line_record(row: dict, out_file: str, sem: asyncio.Semaphore, max_retries: int = 5):
    voice, pitch, rate, text = row["voice"], row["pitch"], row["rate"], row["text"]
    chunk_timeout = calculate_chunk_timeout(text)
    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                active_voice = voice
                if attempt >= 4:
                    active_voice = "en-US-GuyNeural" if row.get("gender") == "Male" else "en-US-EmmaNeural"
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
        with open(chapter_meta, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("duration", 0) > 60:
            print(f"[{NOVEL_SLUG}] [Cached Audio] Ch.{ch_num:03d} ({format_timestamp(meta['duration'])})", flush=True)
            return ch_num, chapter_mp3, meta["duration"], meta["title"], meta["relative_subtitles"]

    temp_dir = os.path.join(build_dir, f"temp_ch_{ch_num:03d}")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files, tasks = [], []
    for row in rows:
        c_path = os.path.join(temp_dir, f"seg_{row['line_id']}.mp3")
        chunk_files.append(c_path)
        tasks.append(synthesize_line_record(row, c_path, global_sem))

    await asyncio.gather(*tasks)
    manifest_path = os.path.join(temp_dir, "manifest.txt")
    valid_chunks = [cf for cf in chunk_files if os.path.exists(cf) and os.path.getsize(cf) > 100]
    with open(manifest_path, "w", encoding="utf-8") as f:
        for cf in valid_chunks:
            f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest_path, "-c", "copy", chapter_mp3],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    rel_subtitles, rel_time = [], 0.0
    for cf, row in zip(valid_chunks, rows):
        dur = get_audio_duration(cf)
        sub_text = f"[{row['speaker']}]: {row['text']}" if row['line_type'] == "Dialogue" else row['text']
        rel_subtitles.append((rel_time, rel_time + dur, sub_text))
        rel_time += dur

    final_dur = get_audio_duration(chapter_mp3)
    with open(chapter_meta, "w", encoding="utf-8") as f:
        json.dump({"title": title, "duration": final_dur, "relative_subtitles": rel_subtitles}, f)

    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    try: os.remove(manifest_path)
    except OSError: pass
    try: os.rmdir(temp_dir)
    except OSError: pass

    print(f"[{NOVEL_SLUG}] [Synthesized Audio] Ch.{ch_num:03d}: '{title}' ({format_timestamp(final_dur)})", flush=True)
    return ch_num, chapter_mp3, final_dur, title, rel_subtitles


def assemble_multi_image_video(block_durations: dict, final_audio_path: str, output_video_path: str):
    print(f"\n[{NOVEL_SLUG}] [Phase 4] Assembling 10 Visual Transitions + 15s Dynamic Outro Card...", flush=True)
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
    create_dynamic_outro_slate(outro_slate)
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


async def main():
    os.makedirs(BUILD_DIR, exist_ok=True)
    print(f"=== Starting National Fate Marriage Pipeline: Ch.{START_CHAPTER}–{END_CHAPTER} ===", flush=True)

    char_map, voc_map = load_characters_and_vocatives(NOVEL_SLUG, BASE_CHARACTERS)
    entity_mgr = EntityManager(novel_slug=NOVEL_SLUG, build_dir=BUILD_DIR)

    print(f"\n[{NOVEL_SLUG}] [Phase 1/4] Checking and Staging Chapters {START_CHAPTER} to {END_CHAPTER}...", flush=True)
    staged_chapters = []
    with requests.Session() as session:
        curr_url = START_URL
        for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
            if not curr_url:
                print(f"[{NOVEL_SLUG}] Pagination exhausted early at Ch.{ch_num}.", flush=True)
                break
            ch_json = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}_staged.json")

            if os.path.exists(ch_json):
                with open(ch_json, "r", encoding="utf-8") as f:
                    rows = json.load(f)
                title, _, next_url = scrape_chapter_content(session, curr_url, ch_num)
                print(f"[{NOVEL_SLUG}] [Cached Ch.{ch_num:03d}] {title} ({len(rows)} lines)", flush=True)
            else:
                title, text, next_url = scrape_chapter_content(session, curr_url, ch_num)
                entity_mgr.scan_chapter_for_entities(text, default_female_role="elf_queen", default_male_role="mc")
                rows = parse_chapter_to_staged_json(text, entity_mgr, char_map, voc_map)
                with open(ch_json, "w", encoding="utf-8") as f:
                    json.dump(rows, f, indent=2, ensure_ascii=False)
                print(f"[{NOVEL_SLUG}] [Staged Ch.{ch_num:03d}] {title} ({len(rows)} blocks)", flush=True)

            staged_chapters.append((ch_num, rows, title))
            curr_url = next_url

    create_dynamic_outro_slate(os.path.join(BUILD_DIR, "outro_slate_card.jpg"))

    print(f"\n[{NOVEL_SLUG}] [Phase 2/4] Synthesizing Audio (Batches of {BATCH_SIZE})...", flush=True)
    global_sem = asyncio.Semaphore(GLOBAL_MAX_CONCURRENT_TTS)
    chapter_semaphore = asyncio.Semaphore(PARALLEL_CHAPTERS)

    async def run_chapter_bounded(cn, rw, tt):
        async with chapter_semaphore:
            return await synthesize_chapter_task(cn, rw, tt, BUILD_DIR, global_sem)

    all_results = []
    for b_idx in range(0, len(staged_chapters), BATCH_SIZE):
        batch = staged_chapters[b_idx:b_idx + BATCH_SIZE]
        batch_start_ch = batch[0][0]
        batch_end_ch = batch[-1][0]
        block_num = (b_idx // BATCH_SIZE) + 1

        print(f"\n{'='*25} STARTING BATCH {block_num}: Chapters {batch_start_ch} to {batch_end_ch} {'='*25}", flush=True)

        if block_num <= len(BLOCKS):
            b_cfg = BLOCKS[block_num - 1]
            b_cfg["cover_file"] = os.path.join(BUILD_DIR, f"cover_block_{b_cfg['range'][0]}_{b_cfg['range'][1]}.jpg")
            ensure_block_cover_jit(b_cfg, BUILD_DIR)

        batch_results = await asyncio.gather(*[run_chapter_bounded(cn, rw, tt) for cn, rw, tt in batch])
        all_results.extend(batch_results)
        print(f"{'='*25} BATCH {block_num} COMPLETE: Chapters {batch_start_ch} to {batch_end_ch} {'='*25}\n", flush=True)

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

    print(f"\n[{NOVEL_SLUG}] [Phase 3/4] Audio Mastering (-14 LUFS) & 15s Outro Pad...", flush=True)
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
    if os.path.exists(raw_master_audio):
        os.remove(raw_master_audio)

    assemble_multi_image_video(block_durations, FINAL_AUDIO, FINAL_VIDEO)
    entity_mgr.finalize_and_merge()

    generate_50ch_ensemble_cover(NOVEL_SLUG, BUILD_DIR, COVER_IMAGE, entity_mgr, char_map)

    payload = {
        "snippet": {"title": VIDEO_TITLE, "description": f"{DESC_HEADER}{chr(10).join(timestamps)}{DESC_FOOTER}", "tags": TAGS, "categoryId": "24", "defaultLanguage": "en-US"},
        "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
        "assets": {"video_file": os.path.abspath(FINAL_VIDEO), "thumbnail_file": os.path.abspath(COVER_IMAGE), "subtitles_file": os.path.abspath(SUBTITLES_FILE), "timestamps_file": os.path.abspath(TIMESTAMPS_FILE)}
    }
    with open(PAYLOAD_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[{NOVEL_SLUG}] Execution Complete! Output: {FINAL_VIDEO}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
