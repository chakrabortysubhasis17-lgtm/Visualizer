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
from PIL import Image, ImageDraw, ImageFont

# ==================== PIPELINE CONFIGURATION ====================
START_CHAPTER = 201
END_CHAPTER = 250
START_CHAPTER_URL = "https://mtl-novel.com/novel/one-evolution-point-per-second-i-slay-gods-with-a-single-arrow/chapter-201-destruction-force/"
NOVEL_SLUG = "one-evolution-point-per-second-i-slay-gods-with-a-single-arrow"

BUILD_DIR = "build_arrow_201_250"
FINAL_AUDIO = "output_arrow_201_250.mp3"
TIMESTAMPS_FILE = "youtube_timestamps_arrow_201_250.txt"
SUBTITLES_FILE = "subtitles_arrow_201_250.srt"
FINAL_VIDEO = "final_arrow_201_250.mp4"
COVER_IMAGE = "cover_arrow_201_250.jpg"
UPLOAD_PAYLOAD_FILE = "youtube_upload_payload.json"

NOVEL_TITLE_DISPLAY = [
    "SUN DIVINE FURNACE AWAKENS",
    "THE POWER OF DESTRUCTION",
    "Chapters 201 – 250 [Full Marathon]"
]

# CR-11: 5 Widescreen Single-Scene Visual Blocks (1 per 10 Chapters)
BLOCK_CONFIGS = [
    {
        "index": 1,
        "range": (201, 210),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_201_210.jpg"),
        "prompt": "A breathtaking cinematic 16:9 movie still of handsome 20-year-old Asian celestial archer Ye Chen in radiant white-and-gold immortal robes, standing atop a celestial palace platform under brilliant sunlight. In his palm hovers a radiant golden Sun Divine Furnace blazing with solar plasma flames, while his other hand draws a divine golden bow crackling with crimson Destruction Force energy. High saturation, volumetric daylight, photorealistic, 8k resolution, cinematic.",
        "title": ["SUN DIVINE FURNACE AWAKENS", "THE POWER OF DESTRUCTION", "Chapters 201 – 210"],
        "fallback_color": (245, 185, 45)
    },
    {
        "index": 2,
        "range": (211, 220),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_211_220.jpg"),
        "prompt": "A vibrant high-saturation fantasy action movie still, 16:9 widescreen, handsome Asian celestial archer Ye Chen in golden-white robes unleashing a storm of golden solar plasma arrows shattering floating jade palaces, terrified astral sect prodigies fleeing in terror, daylight celestial skies, 8k resolution, cinematic.",
        "title": ["SHATTERING THE ASTRAL SECT", "WRATH OF THE SOLAR ARROW", "Chapters 211 – 220"],
        "fallback_color": (150, 60, 210)
    },
    {
        "index": 3,
        "range": (221, 230),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_221_230.jpg"),
        "prompt": "A vibrant cinematic fantasy battle scene, 16:9 widescreen, youthful celestial archer facing off against a massive scarred ancient Demigod commander in crimson dragon armor, divine stars and crimson plasma colliding, golden hour sunbeams, photorealistic, 8k resolution.",
        "title": ["DEMIGOD CONFRONTATION", "TIER 11 LOWER GOD DOMAIN", "Chapters 221 – 230"],
        "fallback_color": (225, 60, 40)
    },
    {
        "index": 4,
        "range": (231, 240),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_231_240.jpg"),
        "prompt": "A vibrant cinematic fantasy movie still, 16:9 widescreen, celestial archer firing a massive golden destruction beam into a swirling spatial void rift, colossal demonic beast monarchs disintegrating into glowing crimson embers, vivid daylight, 8k resolution.",
        "title": ["VOID INCURSION CRUSHED", "ERASING THE BEAST MONARCHS", "Chapters 231 – 240"],
        "fallback_color": (30, 180, 170)
    },
    {
        "index": 5,
        "range": (241, 250),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_241_250.jpg"),
        "prompt": "A vibrant cinematic fantasy movie still, 16:9 widescreen, handsome celestial archer Ye Chen standing atop an altar of radiant golden crystalline stars, manifesting a blazing solar core domain, awe-struck cultivators kneeling, bright daylight, 8k resolution.",
        "title": ["PERFECT DIVINE STAR", "SUPREME DOMAIN ASCENSION", "Chapters 241 – 250"],
        "fallback_color": (245, 190, 40)
    }
]

YOUTUBE_CONFIG = {
    "title": "100,000 DESTRUCTION FORCE: Condensing the Sun Divine Furnace to Slay Demigods | Full Audiobook [Ch. 201-250]",
    "categoryId": "24",
    "defaultLanguage": "en",
    "privacyStatus": "unlisted",
    "tags": [
        "One Evolution Point Per Second",
        "I Slay Gods with a Single Arrow",
        "web novel audiobook",
        "litrpg audiobook",
        "infinite evolution",
        "overpowered main character",
        "system apocalypse",
        "progression fantasy",
        "cultivation novel",
        "sun divine furnace",
        "destruction force",
        "full marathon audiobook",
        "chapters 201 to 250"
    ],
    "description_header": (
        "Ye Chen unseals the Immortal-grade Sun Scripture, opening the golden Divine Sea within his body "
        "and condensing the legendary Sun Divine Furnace. By transmuting divine power directly into "
        "the terrifying Power of Destruction and Power of Immortality, his celestial arrows transcend mortal physics, "
        "erasing astral scions, fortress lords, and Tier 11 Demigods.\n\n"
        "Experience Chapters 201 to 250 in a complete multi-voice marathon edition.\n\n"
        "🎧 Audio Master: Mobile-Engineered Pure Speech Master (-14 LUFS, Voice-Enhanced EQ, Brian Narrator).\n"
        "📖 Closed Captions: English Soft Subtitles (CC Enabled).\n"
        "📚 Original Novel: One Evolution Point Per Second: I Slay Gods with a Single Arrow (每秒一个进化点，我一箭弑神)\n\n"
        "══════════════════════════════════════════════\n"
        "TIMESTAMPS:\n"
    ),
    "description_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🔥 ARC HIGHLIGHTS:\n"
        "• 00:00:00 - Chapter 201: Destruction Force & The Sun Divine Furnace\n"
        "• Awakening the Divine Sea & Immortality Power\n"
        "• Condensing the Perfect Divine Star\n"
        "• Tier 11 Lower God Domain Execution\n"
        "• Shattering the Astral Sect Prodigies\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited adaptation produced for storytelling and entertainment purposes. "
        "All original novel rights belong to the original author. Please support the official release!\n\n"
        "#WebNovelAudiobook #LitRPG #InfiniteEvolution #OverpoweredMC #SystemApocalypse #HighMartial #AudiobookMarathon"
    )
}

# ==================== ARCHITECTURAL TUNING ====================
BATCH_SIZE = 10                  # Execute in strict blocks of 10 chapters
PARALLEL_CHAPTERS = 3            # Synthesize exactly 3 chapters concurrently per batch
GLOBAL_MAX_CONCURRENT_TTS = 12   # Prevents Azure IP socket throttling
MAX_NARRATION_MERGE_WORDS = 230  # Merges 3-4 narration paragraphs comfortably
TARGET_DIALOGUE_CHUNK_WORDS = 70

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# Dynamic Word-Scaled Timeout: Short lines resolve fast; large narrative passages get up to 130s buffer
def calculate_chunk_timeout(text: str) -> float:
    words = len(text.split())
    return max(35.0, 25.0 + (words * 0.40))


CHARACTER_REGISTRY = {
    "narrator": {
        "display_name": "Narrator",
        "gender": "Male",
        "line_type": "Narration",
        "voice": "en-US-BrianNeural",
        "pitch": "+0Hz",
        "rate": "+4%",
        "patterns": []
    },
    "system": {
        "display_name": "System",
        "gender": "Synthetic",
        "line_type": "System",
        "voice": "en-US-SteffanNeural",
        "pitch": "-18Hz",
        "rate": "-6%",
        "patterns": []
    },
    "ye_chen": {
        "display_name": "Ye Chen",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-AndrewNeural",
        "pitch": "+0Hz",
        "rate": "+10%",
        "patterns": [
            r"\b(Ye Chen said|Ye Chen replied|Ye Chen smiled|Ye Chen asked|thought Ye Chen|Ye Chen thought|Ye Chen sneered)\b"
        ]
    },
    "fang_xue": {
        "display_name": "Fang Xue",
        "gender": "Female",
        "line_type": "Dialogue",
        "voice": "en-US-JennyNeural",
        "pitch": "+2Hz",
        "rate": "+8%",
        "patterns": [
            r"\b(Fang Xue|Miss Fang|Xue'er|Fang Xue said|Fang Xue whispered)\b"
        ]
    },
    "lin_qingxue": {
        "display_name": "Captain Lin",
        "gender": "Female",
        "line_type": "Dialogue",
        "voice": "en-US-AriaNeural",
        "pitch": "+0Hz",
        "rate": "+10%",
        "patterns": [
            r"\b(Captain Lin|Lin Qingxue|female officer|Vice Commander Lin)\b"
        ]
    },
    "star_saintess": {
        "display_name": "Star Realm Saintess",
        "gender": "Female",
        "line_type": "Dialogue",
        "voice": "en-US-EmmaNeural",
        "pitch": "+3Hz",
        "rate": "+9%",
        "patterns": [
            r"\b(Saintess|Holy Maiden|Fairy|Goddess|senior sister gasping|girl gasped)\b"
        ]
    },
    "qin_tian": {
        "display_name": "Commander Qin",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-RogerNeural",
        "pitch": "-4Hz",
        "rate": "+3%",
        "patterns": [
            r"\b(Commander Qin|Qin Tian|General Qin|Fortress Supreme|Supreme Commander)\b"
        ]
    },
    "old_ancestor": {
        "display_name": "Demigod Ancestor",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-DavisNeural",
        "pitch": "-10Hz",
        "rate": "-2%",
        "patterns": [
            r"\b(Old Ancestor|Patriarch|Demigod Elder|Elder Wang|Ancestor Wang|Grandmaster)\b"
        ]
    },
    "holy_son": {
        "display_name": "Astral Holy Son",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-TonyNeural",
        "pitch": "+3Hz",
        "rate": "+10%",
        "patterns": [
            r"\b(Holy Son|Astral Scion|Nangong|Supreme Prodigy|Divine Son scoffed)\b"
        ]
    },
    "arrogant_scion": {
        "display_name": "Arrogant Scion",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-EricNeural",
        "pitch": "+5Hz",
        "rate": "+12%",
        "patterns": [
            r"\b(sneered|barked|courting death|fool|insolent|audacious|bastard)\b"
        ]
    },
    "void_assassin": {
        "display_name": "Void Assassin",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-ChristopherNeural",
        "pitch": "-6Hz",
        "rate": "+4%",
        "patterns": [
            r"\b(assassin|Shadow Pavilion|man in black|infiltrator whispered|spy)\b"
        ]
    },
    "demon_general": {
        "display_name": "Beast King",
        "gender": "Synthetic",
        "line_type": "Dialogue",
        "voice": "en-US-JasonNeural",
        "pitch": "-12Hz",
        "rate": "+3%",
        "patterns": [
            r"\b(Demon General|Beast Monarch|Demon Commander|Vanguard roared|Beast King)\b"
        ]
    },
    "abyssal_sovereign": {
        "display_name": "Destruction Sovereign",
        "gender": "Synthetic",
        "line_type": "Dialogue",
        "voice": "en-US-DavisNeural",
        "pitch": "-22Hz",
        "rate": "-8%",
        "patterns": [
            r"\b(Destruction God|Abyssal Sovereign|Demon God|Cosmic Entity|Demon Wolf roared|Ancient Sovereign)\b"
        ]
    }
}

COMPILED_SPEAKER_PATTERNS = []
for role_key, meta in CHARACTER_REGISTRY.items():
    for pat in meta["patterns"]:
        COMPILED_SPEAKER_PATTERNS.append((re.compile(pat, re.IGNORECASE), role_key))

PHONETIC_LEXICON = [
    (re.compile(r"\bYe Chen\b", re.I), "Yeh Chen"),
    (re.compile(r"\bQi\b"), "Chee"),
    (re.compile(r"\bDantian\b", re.I), "Dahn-tyen"),
    (re.compile(r"\bXianxia\b", re.I), "Shee-ahn-shyah"),
    (re.compile(r"\bWuxia\b", re.I), "Woo-shyah"),
    (re.compile(r"\bQigong\b", re.I), "Chee-gong"),
    (re.compile(r"\bFang Xue\b", re.I), "Fahng Shwair")
]

RE_SYSTEM = re.compile(
    r"(?:\[|【|〔|『|〖|［)"
    r"(Ding!|System Prompt|Evolution Point|Acquired|Unlocked|Upgraded|Host|Congratulations|Skill|Prompt|Notice|System|Destruction Force|Sun Scripture|Sun Divine Furnace)"
    r".*?"
    r"(?:\]|】|〕|』|〗|］)",
    re.IGNORECASE
)

RE_SCENE_DIVIDER = re.compile(r"^(\s*[*~=_#-]\s*){3,}$", re.MULTILINE)

WATERMARK_PATTERNS = [
    re.compile(r"\(End of this chapter\)", re.I),
    re.compile(r"Please visit mtl-novel\.com.*", re.I),
    re.compile(r"Check out our latest novel.*", re.I),
    re.compile(r"\[TL Note:.*?\]", re.I),
    re.compile(r"https?://\S+", re.I),
]

FULLWIDTH_TO_ASCII = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '「': '"', '」': '"',
    '，': ', ', '。': '. ', '！': '! ', '？': '? ',
    '：': ': ', '；': '; ', '（': '(', '）': ')'
})

RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')
RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

os.makedirs(BUILD_DIR, exist_ok=True)


def clean_and_normalize_text(text: str) -> str:
    cleaned = text.translate(FULLWIDTH_TO_ASCII)
    cleaned = RE_SCENE_DIVIDER.sub("", cleaned)
    for pat in WATERMARK_PATTERNS:
        cleaned = pat.sub("", cleaned)
    for regex, phoneme in PHONETIC_LEXICON:
        cleaned = regex.sub(phoneme, cleaned)

    cleaned = re.sub(r"\bLv\.?\s*(\d+)", r"Level \1", cleaned, flags=re.I)
    cleaned = re.sub(r"\bHP\b", "Health Points", cleaned)
    cleaned = re.sub(r"\bMP\b", "Mana Points", cleaned)
    cleaned = re.sub(r"\bF-rank\b", "F rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSSS-rank\b", "Triple S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSS-rank\b", "Double S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bS-rank\b", "S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSTR\b", "Strength", cleaned)
    cleaned = re.sub(r"\bAGI\b", "Agility", cleaned)
    cleaned = re.sub(r"\bINT\b", "Intelligence", cleaned)
    return re.sub(r"[ \t]+", " ", cleaned).strip()


def balance_paragraph_quotes(paragraph: str) -> str:
    count = paragraph.count('"')
    if count % 2 != 0:
        if re.search(r'\b(said|replied|shouted|asked|roared|sneered)\b', paragraph, re.I):
            paragraph = paragraph + '"'
        else:
            paragraph = '"' + paragraph
    return paragraph


# ==================== WEB NOVEL SCRAPING ====================
def scrape_chapter_content(session: requests.Session, url: str):
    resp = session.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "Untitled Chapter"

    article = soup.find("article")
    if not article:
        raise ValueError(f"Target article missing at: {url}")

    paragraphs = [clean_and_normalize_text(p.get_text(strip=True)) for p in article.find_all("p")]
    paragraphs = [p for p in paragraphs if p and RE_ALPHANUM.search(p)]
    full_text = f"{title}.\n\n" + "\n\n".join(paragraphs)

    next_url = None
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True).lower()
        if "next" in t or "»" in t or "next chapter" in t:
            if NOVEL_SLUG in a["href"]:
                next_url = urllib.parse.urljoin(url, a["href"])
                break

    return title, full_text, next_url


# ==================== BALANCED PARSER & STAGING ====================
def parse_chapter_to_staged_json(text: str) -> list:
    paragraphs = text.split("\n\n")
    raw_segments = []

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
                line_type = "System" if RE_SYSTEM.search(chunk) else "Narration"
                role_key = "system" if line_type == "System" else "narrator"
                raw_segments.append({"role_key": role_key, "line_type": line_type, "text": chunk})
            else:
                line_type = "Dialogue"
                prev_ctx = parts[i - 1][-120:].lower() if i > 0 else ""
                next_ctx = parts[i + 1][:120].lower() if i + 1 < len(parts) else ""
                surrounding = prev_ctx + " " + next_ctx

                assigned_role = None
                for pattern, r_key in COMPILED_SPEAKER_PATTERNS:
                    if pattern.search(surrounding):
                        assigned_role = r_key
                        break

                if not assigned_role:
                    if any(w in surrounding for w in ["i said", "i replied", "ye chen", "i muttered"]):
                        assigned_role = "ye_chen"
                    elif any(w in surrounding for w in ["she said", "she whispered", "miss fang"]):
                        assigned_role = "fang_xue"
                    elif any(w in surrounding for w in ["roared", "shouted", "bastard", "courting death"]):
                        assigned_role = "arrogant_scion"
                    else:
                        assigned_role = "ye_chen"

                raw_segments.append({"role_key": assigned_role, "line_type": line_type, "text": chunk})

    # Merge consecutive narration paragraphs up to MAX_NARRATION_MERGE_WORDS
    consolidated = []
    for seg in raw_segments:
        if (
            consolidated
            and consolidated[-1]["role_key"] == "narrator"
            and seg["role_key"] == "narrator"
        ):
            prev_len = len(consolidated[-1]["text"].split())
            new_len = len(seg["text"].split())
            if prev_len + new_len <= MAX_NARRATION_MERGE_WORDS:
                consolidated[-1]["text"] += " " + seg["text"]
                continue

        consolidated.append(seg)

    staged_records = []
    line_seq = 1

    for seg in consolidated:
        role_meta = CHARACTER_REGISTRY[seg["role_key"]]
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
            staged_records.append({
                "line_id": f"{line_seq:04d}",
                "speaker": role_meta["display_name"],
                "gender": role_meta["gender"],
                "line_type": seg["line_type"],
                "text": text_piece,
                "voice": role_meta["voice"],
                "pitch": role_meta["pitch"],
                "rate": role_meta["rate"]
            })
            line_seq += 1

    return staged_records


# ==================== VISUAL ENGINE ====================
def fetch_image_safe(prompt: str, out_path: str, width: int = 1280, height: int = 720) -> bool:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 3000:
        return True
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1000, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 3000:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False


def build_celestial_atmosphere_canvas(width: int, height: int, tint_color: tuple) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (14, 10, 20, 255))
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
        d_over.line([(0, y), (width, y)], fill=(10, 8, 12, min(140, int(dist * 1.8))))

    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    draw.rectangle([(50, 50), (width - 50, height - 50)], outline=(60, 45, 25, 220), width=2)
    draw.rectangle([(64, 64), (width - 64, height - 64)], outline=(180, 140, 50, 180), width=1)

    c = 40
    corners = [
        ((64, 64), (64 + c, 64), (64, 64 + c)),
        ((width - 64, 64), (width - 64 - c, 64), (width - 64, 64 + c)),
        ((64, height - 64), (64 + c, height - 64), (64, height - 64 - c)),
        ((width - 64, height - 64), (width - 64 - c, height - 64), (width - 64, height - 64 - c))
    ]
    for orig, h_pt, v_pt in corners:
        draw.line([orig, h_pt], fill=(255, 215, 90, 255), width=3)
        draw.line([orig, v_pt], fill=(255, 215, 90, 255), width=3)

    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 58)
                sub_font = ImageFont.truetype(fp, 42)
                break
            except Exception:
                pass
    if not font:
        font = ImageFont.load_default()
        sub_font = font

    line_spacing = 96
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


def ensure_block_cover_jit(cfg: dict):
    out_file = cfg["cover_file"]
    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        return

    width, height = 1920, 1080
    raw_art = os.path.join(BUILD_DIR, f"raw_block_{cfg['index']}.jpg")

    print(f"  [CR-11 JIT] Generating Widescreen Scene for Block {cfg['index']} (Ch. {cfg['range'][0]}–{cfg['range'][1]})...")
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
    stamped.convert("RGB").save(out_file, "JPEG", quality=98)
    print(f"  [CR-11 JIT] Cover Ready: '{out_file}'")

    if cfg.get("index") == 1:
        shutil.copy2(out_file, COVER_IMAGE)
        print(f"  [Master Thumbnail] Saved: '{COVER_IMAGE}'")


# ==================== AUDIO SYNTHESIS ENGINE (DYNAMIC TIMEOUT) ====================
async def synthesize_line_record(row: dict, out_file: str, sem: asyncio.Semaphore, max_retries: int = 3):
    voice, pitch, rate, text = row["voice"], row["pitch"], row["rate"], row["text"]
    chunk_timeout = calculate_chunk_timeout(text)

    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                active_voice = voice if attempt < 3 else ("en-US-GuyNeural" if voice == "en-US-BrianNeural" else voice)
                comm = edge_tts.Communicate(text, active_voice, pitch=pitch, rate=rate)
                await asyncio.wait_for(comm.save(out_file), timeout=chunk_timeout)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
                    return
            except asyncio.TimeoutError:
                print(f"     [TTS Timeout] Line {row['line_id']} ({len(text.split())} words) exceeded {chunk_timeout:.1f}s (Attempt {attempt}/{max_retries}). Retrying...")
            except Exception as e:
                print(f"     [TTS Error] Line {row['line_id']} ({voice}): {e} (Attempt {attempt}/{max_retries}). Retrying...")

            if attempt == max_retries:
                print(f"     [FATAL TTS] Line {row['line_id']} failed completely. Writing fallback silence.")
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", out_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            await asyncio.sleep(attempt * 0.5)


def get_audio_duration(file_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 0.5


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


async def synthesize_chapter_task(ch_num: int, rows: list, title: str, global_sem: asyncio.Semaphore):
    chapter_mp3 = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}.mp3")
    chapter_meta = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}_meta.json")

    # Sanity guard: ensures cached file has realistic length (> 60s)
    if os.path.exists(chapter_mp3) and os.path.exists(chapter_meta):
        with open(chapter_meta, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("duration", 0) > 60:
            print(f"[Cached] Chapter {ch_num:02d} valid ({format_timestamp(meta['duration'])})")
            return ch_num, chapter_mp3, meta["duration"], meta["title"], meta["relative_subtitles"]

    temp_dir = os.path.join(BUILD_DIR, f"temp_ch_{ch_num:03d}")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files = []
    tasks = []

    for row in rows:
        c_path = os.path.join(temp_dir, f"seg_{row['line_id']}.mp3")
        chunk_files.append(c_path)
        tasks.append(synthesize_line_record(row, c_path, global_sem))

    await asyncio.gather(*tasks)

    manifest_path = os.path.join(temp_dir, "manifest.txt")
    valid_chunks = [cf for cf in chunk_files if os.path.exists(cf) and os.path.getsize(cf) > 100]

    with open(manifest_path, "w", encoding="utf-8") as f:
        for cf in valid_chunks:
            safe = os.path.abspath(cf).replace(os.sep, "/")
            f.write(f"file '{safe}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", manifest_path, "-c", "copy", chapter_mp3
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    rel_subtitles = []
    rel_time = 0.0
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

    print(f"  [Synthesized] Chapter {ch_num:02d}: '{title}' ({format_timestamp(final_dur)}) - {len(valid_chunks)} chunks")
    return ch_num, chapter_mp3, final_dur, title, rel_subtitles


# ==================== VIDEO ASSEMBLY ====================
def assemble_multi_image_video(block_durations: dict, final_audio_path: str, output_video_path: str):
    print("\n[*] Assembling CR-11 Multi-Image Video (Swapping visuals every 10 chapters)...")
    video_segments = []

    for cfg in BLOCK_CONFIGS:
        b_idx = cfg["index"]
        dur = block_durations.get(b_idx, 0.0)
        if dur <= 0.1:
            continue

        ensure_block_cover_jit(cfg)
        cover_img = cfg["cover_file"]
        segment_video = os.path.join(BUILD_DIR, f"v_seg_block_{b_idx}.mp4")

        cmd_seg = [
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1",
            "-t", f"{dur:.3f}", "-i", cover_img,
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", segment_video
        ]
        subprocess.run(cmd_seg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        video_segments.append(segment_video)
        print(f"  [CR-11 Segment {b_idx}] Chapters {cfg['range'][0]}–{cfg['range'][1]} ({format_timestamp(dur)}) ready.")

    v_manifest = os.path.join(BUILD_DIR, "v_segments_list.txt")
    with open(v_manifest, "w", encoding="utf-8") as f:
        for vs in video_segments:
            safe = os.path.abspath(vs).replace(os.sep, "/")
            f.write(f"file '{safe}'\n")

    full_video_track = os.path.join(BUILD_DIR, "full_video_track.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", v_manifest, "-c", "copy", full_video_track
    ], check=True)

    print(f"Losslessly muxing video track and mastered audio to {output_video_path}...")
    subprocess.run([
        "ffmpeg", "-y", "-i", full_video_track, "-i", final_audio_path,
        "-c", "copy", "-movflags", "+faststart", "-shortest", output_video_path
    ], check=True)

    for vs in video_segments:
        try: os.remove(vs)
        except OSError: pass
    try: os.remove(v_manifest)
    except OSError: pass
    try: os.remove(full_video_track)
    except OSError: pass


# ==================== MAIN COMPILATION ENGINE ====================
async def main():
    print(f"=== Production Pipeline: Chapters {START_CHAPTER} to {END_CHAPTER} ===")
    print("[*] Engine: Multi-Chapter Async Pipelining | Batches of 10 (3 Parallel) | Scaled Dynamic Timeout | Brian Narrator")

    # PHASE 1: Pre-Scraping & Logging
    print("\n[Phase 1] Pre-scraping & staging chapter texts...")
    staged_chapters = []
    with requests.Session() as session:
        curr_url = START_CHAPTER_URL
        for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
            if not curr_url:
                print(f"[Warning] Pagination exhausted at chapter {ch_num}. Halting scrape.")
                break

            ch_json = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}_staged.json")
            if os.path.exists(ch_json):
                with open(ch_json, "r", encoding="utf-8") as f:
                    rows = json.load(f)
                title, _, next_url = scrape_chapter_content(session, curr_url)
                print(f"  [Scraped & Cached Ch.{ch_num:03d}] {title} ({len(rows)} lines)")
            else:
                title, text, next_url = scrape_chapter_content(session, curr_url)
                rows = parse_chapter_to_staged_json(text)
                with open(ch_json, "w", encoding="utf-8") as f:
                    json.dump(rows, f, indent=2, ensure_ascii=False)

                narration_count = sum(1 for r in rows if r['line_type'] == 'Narration')
                dialogue_count = sum(1 for r in rows if r['line_type'] == 'Dialogue')
                system_count = sum(1 for r in rows if r['line_type'] == 'System')
                total_words = len(text.split())

                print(f"  [Scraped Fresh Ch.{ch_num:03d}] {title}")
                print(f"     -> Words: {total_words} | Staged Lines: {len(rows)} (Narr: {narration_count}, Dial: {dialogue_count}, Sys: {system_count})")
                print(f"     -> First Line: \"{rows[0]['text'][:85]}...\"")

            staged_chapters.append((ch_num, rows, title))
            curr_url = next_url

    # PHASE 2: Parallel TTS Synthesis in Batches of 10
    print(f"\n[Phase 2] Synthesizing audio in batches of {BATCH_SIZE} chapters ({PARALLEL_CHAPTERS} parallel per batch)...")
    global_sem = asyncio.Semaphore(GLOBAL_MAX_CONCURRENT_TTS)
    chapter_semaphore = asyncio.Semaphore(PARALLEL_CHAPTERS)

    async def run_chapter_bounded(ch_num, rows, title):
        async with chapter_semaphore:
            return await synthesize_chapter_task(ch_num, rows, title, global_sem)

    all_results = []
    for b_idx in range(0, len(staged_chapters), BATCH_SIZE):
        batch = staged_chapters[b_idx:b_idx + BATCH_SIZE]
        batch_start_ch = batch[0][0]
        batch_end_ch = batch[-1][0]
        block_num = (b_idx // BATCH_SIZE) + 1

        print(f"\n{'='*25} STARTING BATCH {block_num}: Chapters {batch_start_ch} to {batch_end_ch} {'='*25}")
        
        if block_num <= len(BLOCK_CONFIGS):
            ensure_block_cover_jit(BLOCK_CONFIGS[block_num - 1])

        batch_tasks = [run_chapter_bounded(cn, rw, tt) for cn, rw, tt in batch]
        batch_results = await asyncio.gather(*batch_tasks)
        all_results.extend(batch_results)

        print(f"{'='*25} BATCH {block_num} COMPLETE: Chapters {batch_start_ch} to {batch_end_ch} {'='*25}\n")

    all_results.sort(key=lambda x: x[0])

    # PHASE 3: Global Offset & Timestamp Assembly
    print("\n[Phase 3] Offset calculation & subtitle generation...")
    chapter_files = []
    chapter_durations = {}
    timestamps = []
    all_subtitles = []
    global_offset = 0.0

    for ch_num, mp3_path, dur, title, rel_subs in all_results:
        chapter_files.append(mp3_path)
        chapter_durations[ch_num] = dur
        timestamps.append(f"{format_timestamp(global_offset)} - {title}")

        for s_rel, e_rel, text in rel_subs:
            s_abs = format_srt_time(global_offset + s_rel)
            e_abs = format_srt_time(global_offset + e_rel)
            all_subtitles.append((s_abs, e_abs, text))

        global_offset += dur

    block_durations = {}
    for cfg in BLOCK_CONFIGS:
        start_c, end_c = cfg["range"]
        b_dur = sum(chapter_durations.get(c, 0.0) for c in range(start_c, end_c + 1))
        block_durations[cfg["index"]] = b_dur

    timestamps_text = "\n".join(timestamps)
    with open(TIMESTAMPS_FILE, "w", encoding="utf-8") as f:
        f.write(timestamps_text)
    print(f"[Saved] Timestamps saved to: {TIMESTAMPS_FILE}")

    with open(SUBTITLES_FILE, "w", encoding="utf-8") as f:
        for idx, (s_time, e_time, text) in enumerate(all_subtitles, 1):
            f.write(f"{idx}\n{s_time} --> {e_time}\n{text}\n\n")
    print(f"[Saved] Soft subtitles exported to: {SUBTITLES_FILE}")

    full_description = f"{YOUTUBE_CONFIG['description_header']}{timestamps_text}{YOUTUBE_CONFIG['description_footer']}"
    payload = {
        "snippet": {
            "title": YOUTUBE_CONFIG["title"],
            "description": full_description,
            "tags": YOUTUBE_CONFIG["tags"],
            "categoryId": YOUTUBE_CONFIG["categoryId"],
            "defaultLanguage": YOUTUBE_CONFIG["defaultLanguage"]
        },
        "status": {
            "privacyStatus": YOUTUBE_CONFIG["privacyStatus"],
            "selfDeclaredMadeForKids": False
        },
        "assets": {
            "video_file": os.path.abspath(FINAL_VIDEO),
            "thumbnail_file": os.path.abspath(COVER_IMAGE),
            "subtitles_file": os.path.abspath(SUBTITLES_FILE),
            "timestamps_file": os.path.abspath(TIMESTAMPS_FILE)
        }
    }
    with open(UPLOAD_PAYLOAD_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[Saved] YouTube Upload Payload written to: {UPLOAD_PAYLOAD_FILE}")

    # PHASE 4: Master Concat & DSP Mastering
    raw_master_audio = os.path.join(BUILD_DIR, "raw_master.mp3")
    master_manifest = os.path.join(BUILD_DIR, "master_list.txt")
    with open(master_manifest, "w", encoding="utf-8") as f:
        for cf in chapter_files:
            safe = os.path.abspath(cf).replace(os.sep, "/")
            f.write(f"file '{safe}'\n")

    print("\nLosslessly joining chapters for mastering...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", master_manifest, "-c", "copy", raw_master_audio
    ], check=True)

    print(f"\nApplying Mobile Audio Mastering DSP (-14 LUFS) to {FINAL_AUDIO}...")
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_master_audio,
        "-af", "highpass=f=85,equalizer=f=3200:t=q:w=1.5:g=2.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50,loudnorm=I=-14:TP=-1.5:LRA=7",
        "-c:a", "libmp3lame", "-b:a", "192k", FINAL_AUDIO
    ], check=True)

    if os.path.exists(raw_master_audio):
        os.remove(raw_master_audio)

    # PHASE 5: Multi-Image Video Assembly
    assemble_multi_image_video(block_durations, FINAL_AUDIO, FINAL_VIDEO)

    print(f"\n[Completed] Video Ready: {FINAL_VIDEO}")
    print(f"[Completed] Standalone Master Thumbnail: {COVER_IMAGE}")
    print(f"[Completed] Closed Captions Track: {SUBTITLES_FILE}")
    print(f"[Completed] YouTube Upload Config: {UPLOAD_PAYLOAD_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
