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

# ==================== PIPELINE CONFIGURATION ====================
START_CHAPTER = 1
END_CHAPTER = 50
START_CHAPTER_URL = "https://mtl-novel.com/novel/game-descends-from-vampire-bat-to-loli-tyrant/chapter-1-reborn-as-a-vampire-bat/"
NOVEL_SLUG = "game-descends-from-vampire-bat-to-loli-tyrant"

BUILD_DIR = "build_bat_001_050"
FINAL_AUDIO = "output_bat_001_050.mp3"
TIMESTAMPS_FILE = "youtube_timestamps_bat_001_050.txt"
SUBTITLES_FILE = "subtitles_bat_001_050.srt"
FINAL_VIDEO = "final_bat_001_050.mp4"
COVER_IMAGE = "cover_bat_001_050.jpg"
UPLOAD_PAYLOAD_FILE = "youtube_upload_payload_001_050.json"

NOVEL_TITLE_DISPLAY = [
    "REBORN AS A VAMPIRE BAT",
    "THE RISE OF THE BLOOD TYRANT",
    "Chapters 1 – 50 [Complete Marathon]"
]

# ==================== BEING A BONG MASTER SPEC CONSTANTS ====================
CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"

STYLE_ANCHOR = (
    "Masterpiece 2D Japanese anime key visual, crisp cel-shaded illustration, "
    "official light novel cover art, ultra-sharp clean black lineart, "
    "razor-sharp anime eyes with detailed glowing pupils, high micro-contrast, "
    "vibrant saturated colors, 8k resolution, trending on Pixiv."
)
HERO_PLACEMENT = "waist-up view, stands bold and confident front-center"
DAYLIGHT_BG = (
    "bright daytime azure-blue sky with blazing sun rays, white cumulus clouds, "
    "floating mountain peaks, and glowing celestial architecture"
)

FORBIDDEN_TERMS = [
    re.compile(r"\bblack hole orb\b", re.I),
    re.compile(r"\bvoid rift\b", re.I),
    re.compile(r"\bvortex\b", re.I),
    re.compile(r"\bgiant circular halo\b", re.I),
]

GRADIENT_PALETTES = [
    ((255, 255, 180), (255, 175, 40)),  # Champagne Gold -> Amber Gold
    ((255, 215, 70), (245, 95, 25)),    # Imperial Gold -> Flame Orange
    ((255, 170, 60), (220, 50, 30)),    # Amber Flame -> Deep Crimson
]

# CR-11: 5 Widescreen Dynamic Visual Blocks (10 Chapters Each)
BLOCK_CONFIGS = [
    {
        "index": 1,
        "range": (1, 10),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_001_010.jpg"),
        "hero_desc": "a petite crimson-eyed anime vampire girl with glossy black twin-tails and gothic bat wings folding over obsidian shoulder plates",
        "action": "holding a glowing crimson blood-essence crystal with sharp glowing fangs visible in a sly smirk",
        "title": ["REBORN AS A VAMPIRE BAT", "THE BLOODLINE EXTRACTION CHEAT", "Chapters 1 – 10"],
        "fallback_color": (160, 20, 40)
    },
    {
        "index": 2,
        "range": (11, 20),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_011_020.jpg"),
        "hero_desc": "a formidable anime vampire tyrant girl surrounded by thousands of glowing crimson phantom bats obeying her gestures",
        "action": "effortlessly commanding an overwhelming wave of supersonic blood blades against dungeon beasts",
        "title": ["BLOOD SWARM SOVEREIGN", "DEVOURING CAVERN MONARCHS", "Chapters 11 – 20"],
        "fallback_color": (180, 40, 60)
    },
    {
        "index": 3,
        "range": (21, 30),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_021_030.jpg"),
        "hero_desc": "a sinister cute anime loli tyrant holding a massive ornate scythe sculpted from solidified ruby blood plasma",
        "action": "standing atop a shattered dungeon monolith overlooking fleeing high-tier human hunter squads",
        "title": ["THE GAME MERGES WITH REALITY", "TERRORIZING HUMAN GUILDS", "Chapters 21 – 30"],
        "fallback_color": (210, 50, 30)
    },
    {
        "index": 4,
        "range": (31, 40),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_031_040.jpg"),
        "hero_desc": "an apex anime blood empress draped in sovereign crimson-and-gold royal robes with glowing blood law runes etched along her porcelain arms",
        "action": "raising a slender hand as high-order divine player enforcers fall to their knees under crushing gravity",
        "title": ["CRIMSON METAMORPHOSIS", "SHATTERING ELITE S-RANK PLAYERS", "Chapters 31 – 40"],
        "fallback_color": (245, 120, 35)
    },
    {
        "index": 5,
        "range": (41, 50),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_041_050.jpg"),
        "hero_desc": "the supreme vampire loli tyrant seated majestically upon a throne of floating obsidian stone and radiant ruby crystals",
        "action": "surveying an entire conquered city domain with sovereign crimson eyes as golden daylight crests over mountain citadels",
        "title": ["DOMAIN OF THE NIGHT TYRANT", "UNSTOPPABLE MONSTER REIGN", "Chapters 41 – 50"],
        "fallback_color": (255, 215, 60)
    }
]

YOUTUBE_CONFIG = {
    "title": "REBORN AS A VAMPIRE BAT: Awakening the Bloodline Devour System | Full Audiobook [Ch. 1-50]",
    "categoryId": "24",
    "defaultLanguage": "en",
    "privacyStatus": "unlisted",
    "tags": [
        "Game Descends From Vampire Bat to Loli Tyrant",
        "reborn as a vampire bat audiobook",
        "monster evolution audiobook",
        "litrpg audiobook",
        "progression fantasy",
        "blood tyrant",
        "vampire evolution novel",
        "system apocalypse",
        "overpowered mc",
        "bloodline extraction",
        "full marathon audiobook",
        "chapters 1 to 50",
        "multi-voice audiobook",
        "web novel audio drama"
    ],
    "description_header": (
        "Welcome to Chapters 1 through 50 of 'Game Descends: From Vampire Bat to Loli Tyrant'!\n\n"
        "When the dimensional apocalypse merges an unforgiving game reality with the mortal world, humanity scrambles to awaken "
        "combat classes. But our protagonist reincarnates as the lowest-tier dungeon nuisance: a fragile, blind Vampire Bat.\n\n"
        "Armed with an innate Bloodline Devour Talent, every drop of enemy blood triggers exponential physical evolution. "
        "From feasting on dungeon vermin to slaughtering cavern monarchs, she shatters racial ceilings—evolving into the "
        "fabled Blood Clan Progenitor and dominating human player guilds as an unstoppable, cute yet merciless Blood Tyrant.\n\n"
        "Experience Chapters 1 to 50 in this definitive multi-voice marathon edition.\n\n"
        "🎧 Audio Master: Mobile-Engineered Pure Speech Master (-14 LUFS, Voice-Enhanced EQ, Brian Narrator).\n"
        "📖 Closed Captions: English Soft Subtitles (CC Enabled).\n"
        "🎨 Visual Engine: 'Being a Bong' Standard (Flux Native 1080p, 3D Metallic Flame Typography).\n\n"
        "══════════════════════════════════════════════\n"
        "TIMESTAMPS:\n"
    ),
    "description_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🔥 MARATHON HIGHLIGHTS:\n"
        "• 00:00:00 - Chapter 1: Reborn as a Vampire Bat\n"
        "• Awakening the Bloodline Extraction & Devour System\n"
        "• First Dungeon Cavern Kill & Sucking Essence\n"
        "• Racial Breakthrough: Supersonic Waves & Blood Mist Form\n"
        "• The Reality Merge: First Encounter with Arrogant Player Parties\n"
        "• Chapter 50: The Rise of the True Loli Blood Tyrant\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited adaptation produced for audio drama, storytelling, and entertainment purposes. "
        "All original intellectual property rights belong to the author. Subscribe to follow the journey!\n\n"
        "#WebNovelAudiobook #LitRPG #MonsterEvolution #VampireBat #BloodTyrant #ProgressionFantasy #AudiobookMarathon"
    )
}

# ==================== ARCHITECTURAL TUNING ====================
BATCH_SIZE = 10
PARALLEL_CHAPTERS = 3
GLOBAL_MAX_CONCURRENT_TTS = 12
MAX_NARRATION_MERGE_WORDS = 230
TARGET_DIALOGUE_CHUNK_WORDS = 70

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def calculate_chunk_timeout(text: str) -> float:
    words = len(text.split())
    return max(35.0, 25.0 + (words * 0.40))


# ==================== 100% FREE-TIER EDGE TTS REGISTRY ====================
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
        "display_name": "Evolution System",
        "gender": "Synthetic",
        "line_type": "System",
        "voice": "en-US-SteffanNeural",
        "pitch": "-18Hz",
        "rate": "-6%",
        "patterns": []
    },
    "mc_tyrant": {
        "display_name": "Blood Tyrant",
        "gender": "Female",
        "line_type": "Dialogue",
        "voice": "en-US-JennyNeural",
        "pitch": "-2Hz",
        "rate": "+6%",
        "patterns": [
            r"\b(she said|she sneered|she thought|thought the bat|she giggled|I muttered|I thought|she licked her fangs)\b"
        ]
    },
    "guild_leader": {
        "display_name": "Guild Commander",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-RogerNeural",
        "pitch": "-6Hz",
        "rate": "+2%",
        "patterns": [
            r"\b(Captain|Guild Leader|Commander|Veteran|old hunter shouted|Tank hold the line)\b"
        ]
    },
    "arrogant_player": {
        "display_name": "Arrogant Player",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-EricNeural",
        "pitch": "+5Hz",
        "rate": "+10%",
        "patterns": [
            r"\b(just a bat|trash monster|easy exp|free loot|die beast|sneered|courting death)\b"
        ]
    },
    "female_mage": {
        "display_name": "Female Mage",
        "gender": "Female",
        "line_type": "Dialogue",
        "voice": "en-US-EmmaNeural",
        "pitch": "+3Hz",
        "rate": "+8%",
        "patterns": [
            r"\b(Mage screamed|Priestess cried|she screamed|girl gasped|Healer run)\b"
        ]
    },
    "beast_boss": {
        "display_name": "Dungeon Boss",
        "gender": "Synthetic",
        "line_type": "Dialogue",
        "voice": "en-US-SteffanNeural",
        "pitch": "-15Hz",
        "rate": "+4%",
        "patterns": [
            r"\b(Monarch roared|Boss bellowed|King roared|Beast howled|serpent hissed)\b"
        ]
    }
}

COMPILED_SPEAKER_PATTERNS = []
for role_key, meta in CHARACTER_REGISTRY.items():
    for pat in meta["patterns"]:
        COMPILED_SPEAKER_PATTERNS.append((re.compile(pat, re.IGNORECASE), role_key))

PHONETIC_LEXICON = [
    (re.compile(r"\bLoli\b", re.I), "Low-lee"),
    (re.compile(r"\bQi\b"), "Chee"),
    (re.compile(r"\bDantian\b", re.I), "Dahn-tyen"),
    (re.compile(r"\bProgenitor\b", re.I), "Pro-jen-i-tor"),
    (re.compile(r"\bBloodline\b", re.I), "Blood-line")
]

RE_SYSTEM = re.compile(
    r"(?:\[|【|〔|『|〖|［)"
    r"(Ding!|System|Evolution|Bloodline|Devour|Exp|Level|Unlocked|Acquired|Host|Notice|Talent|Tier|HP|MP)"
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

os.makedirs(BUILD_DIR, exist_ok=True)


def clean_and_normalize_text(text: str) -> str:
    cleaned = text.translate(FULLWIDTH_TO_ASCII)
    cleaned = RE_SCENE_DIVIDER.sub("", cleaned)
    for pat in WATERMARK_PATTERNS:
        cleaned = pat.sub("", cleaned)
    for regex, phoneme in PHONETIC_LEXICON:
        cleaned = regex.sub(phoneme, cleaned)

    cleaned = re.sub(r"\bTier-(\d+)\b", r"Tier \1", cleaned, flags=re.I)
    cleaned = re.sub(r"\bLv\.?\s*(\d+)", r"Level \1", cleaned, flags=re.I)
    cleaned = re.sub(r"\bHP\b", "Health Points", cleaned)
    cleaned = re.sub(r"\bMP\b", "Mana Points", cleaned)
    cleaned = re.sub(r"\bEXP\b", "Experience", cleaned)
    cleaned = re.sub(r"\bSSS-rank\b", "Triple S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSS-rank\b", "Double S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bS-rank\b", "S rank", cleaned, flags=re.I)
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
    resp = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
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
                    if any(w in surrounding for w in ["she said", "i muttered", "she laughed", "she sneered"]):
                        assigned_role = "mc_tyrant"
                    elif any(w in surrounding for w in ["captain", "leader", "tank", "retreat"]):
                        assigned_role = "guild_leader"
                    elif any(w in surrounding for w in ["just a bat", "trash", "courting death", "die"]):
                        assigned_role = "arrogant_player"
                    elif any(w in surrounding for w in ["screamed", "healer", "help me"]):
                        assigned_role = "female_mage"
                    else:
                        assigned_role = "mc_tyrant"

                raw_segments.append({"role_key": assigned_role, "line_type": line_type, "text": chunk})

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


# ==================== "BEING A BONG" MASTER VISUAL ENGINE ====================
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


def construct_dynamic_scene_prompt(hero_desc: str, dynamic_action: str) -> str:
    cleaned = dynamic_action
    for forbidden in FORBIDDEN_TERMS:
        cleaned = forbidden.sub("radiant crimson aura", cleaned)
    return f"{STYLE_ANCHOR} {hero_desc}, {HERO_PLACEMENT}, {cleaned}, {DAYLIGHT_BG}."


def fetch_flux_native_1080p(prompt: str, out_path: str) -> bool:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return True

    encoded = urllib.parse.quote(prompt)
    seed = random.randint(10000, 9999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1920&height=1080&seed={seed}&model=flux&nologo=true"

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=35)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"     [Flux Fetch Alert] {e}")
    return False


def apply_lower_third_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(overlay)
    vig_start = int(height * 0.58)

    for y in range(vig_start, height):
        alpha = int(190 * (((y - vig_start) / (height - vig_start)) ** 1.5))
        v_draw.line([(0, y), (width, y)], fill=(10, 6, 12, alpha))

    return Image.alpha_composite(base.convert("RGBA"), overlay)


def stamp_channel_watermark(base: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(base)
    wx, wy = 55, 45
    crest_r = 22

    # Teal circle with warm gold trim
    draw.ellipse(
        [(wx - crest_r, wy - crest_r), (wx + crest_r, wy + crest_r)],
        fill=(25, 195, 170, 255),
        outline=(255, 235, 130, 255),
        width=2
    )

    # Centered white star
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

    # Brand fonts
    name_fp = "C:/Windows/Fonts/arialbd.ttf"
    if not os.path.exists(name_fp):
        name_fp = ensure_cinzel_font()

    name_font = ImageFont.truetype(name_fp, 36)
    handle_font = ImageFont.truetype(name_fp, 22)

    tx = wx + 36
    draw.text((tx + 2, wy - 18 + 2), "Being a Bong", fill=(0, 0, 0, 255), font=name_font)
    draw.text((tx, wy - 18), "Being a Bong", fill=(255, 255, 255, 255), font=name_font)

    draw.text((tx + 1, wy + 20 + 1), "@beingabong", fill=(0, 0, 0, 220), font=handle_font)
    draw.text((tx, wy + 20), "@beingabong", fill=(250, 205, 75, 255), font=handle_font)

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

    line_spacing = 78
    total_text_h = (len(lines) - 1) * line_spacing + 60
    start_y = int(height * 0.68) - (total_text_h // 2)

    draw = ImageDraw.Draw(base)

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else title_font
        bbox = draw.textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)

        # Layer 1: Drop Shadow (+4, +5) with 9px near-black stroke
        draw.text(
            (x + 4, y + 5), line,
            font=active_font,
            fill=(10, 4, 6, 255),
            stroke_width=9,
            stroke_fill=(10, 4, 6, 255)
        )

        # Layer 2: Inner Shadow with 6px deep burgundy stroke
        draw.text(
            (x, y), line,
            font=active_font,
            fill=(42, 8, 12, 255),
            stroke_width=6,
            stroke_fill=(42, 8, 12, 255)
        )

        # Layer 3: Vertical Metallic Gradient Fill
        palette = GRADIENT_PALETTES[min(i, len(GRADIENT_PALETTES) - 1)]
        grad_layer = create_vertical_gradient_text_mask(
            text_w + 20, text_h + 20, line, active_font, palette[0], palette[1]
        )
        base.paste(grad_layer, (x, y), grad_layer)

    return base


def ensure_block_cover_jit(cfg: dict):
    out_file = cfg["cover_file"]
    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        return

    raw_art = os.path.join(BUILD_DIR, f"raw_block_{cfg['index']}.jpg")
    dynamic_prompt = construct_dynamic_scene_prompt(cfg["hero_desc"], cfg["action"])

    print(f"  [CR-11 JIT] Generating Flux 1080p Cover for Block {cfg['index']} (Ch. {cfg['range'][0]}–{cfg['range'][1]})...")
    fetch_flux_native_1080p(dynamic_prompt, raw_art)

    if os.path.exists(raw_art) and os.path.getsize(raw_art) > 10000:
        base = Image.open(raw_art).convert("RGBA")
        if base.size != (1920, 1080):
            base = base.resize((1920, 1080), Image.Resampling.LANCZOS)
    else:
        base = Image.new("RGBA", (1920, 1080), (*cfg["fallback_color"], 255))

    # PIL UnsharpMask Filter
    base = base.filter(ImageFilter.UnsharpMask(radius=2.4, percent=180, threshold=2))
    # 58% Lower-Third Vignette
    base = apply_lower_third_vignette(base)
    # Channel Crest Watermark
    base = stamp_channel_watermark(base)
    # 3D Metallic Flame Typography
    base = stamp_3d_metallic_flame_typography(base, cfg["title"])

    base.convert("RGB").save(out_file, "JPEG", quality=98)
    print(f"  [Being a Bong Standard] Stamped Block {cfg['index']} Cover Ready: '{out_file}'")

    if cfg.get("index") == 1:
        shutil.copy2(out_file, COVER_IMAGE)
        print(f"  [Master Thumbnail] Channel Cover Saved: '{COVER_IMAGE}'")


# ==================== AUDIO SYNTHESIS ENGINE ====================
async def synthesize_line_record(row: dict, out_file: str, sem: asyncio.Semaphore, max_retries: int = 3):
    voice, pitch, rate, text = row["voice"], row["pitch"], row["rate"], row["text"]
    chunk_timeout = calculate_chunk_timeout(text)

    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                active_voice = voice
                if attempt == 3:
                    active_voice = "en-US-JennyNeural" if row.get("gender") == "Female" else "en-US-GuyNeural"
                    print(f"     [TTS Shield] Voice '{voice}' rejected twice. Forcing safe fallback '{active_voice}' for Line {row['line_id']}.")

                comm = edge_tts.Communicate(text, active_voice, pitch=pitch, rate=rate)
                await asyncio.wait_for(comm.save(out_file), timeout=chunk_timeout)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
                    return
            except asyncio.TimeoutError:
                print(f"     [TTS Timeout] Line {row['line_id']} exceeded {chunk_timeout:.1f}s (Attempt {attempt}/{max_retries}).")
            except Exception as e:
                print(f"     [TTS Error] Line {row['line_id']} ({active_voice}): {e} (Attempt {attempt}/{max_retries}).")

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


# ==================== LIGHTWEIGHT 1 FPS MULTI-IMAGE VIDEO ASSEMBLY ====================
def assemble_multi_image_video(block_durations: dict, final_audio_path: str, output_video_path: str):
    print("\n[*] Assembling CR-11 Multi-Image Video (1 FPS Stillimage Mux - Under 850 MB Total)...")
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
    print(f"=== Production Pipeline: Chapters {START_CHAPTER} to {END_CHAPTER} [Vampire Bat Evolution] ===")
    print("[*] Engine: Being a Bong Master Visual Standard | 1 FPS Switch | Brian Narrator")

    # PHASE 1: Pre-Scraping
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

                print(f"  [Scraped Fresh Ch.{ch_num:03d}] {title} ({len(rows)} staged blocks)")

            staged_chapters.append((ch_num, rows, title))
            curr_url = next_url

    # PHASE 2: Parallel TTS Synthesis
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

    # PHASE 5: Fast Multi-Image Video Assembly (< 45s)
    assemble_multi_image_video(block_durations, FINAL_AUDIO, FINAL_VIDEO)

    print(f"\n[Completed] Video Ready: {FINAL_VIDEO} (~750MB)")
    print(f"[Completed] Channel Standard Master Cover: {COVER_IMAGE}")
    print(f"[Completed] Closed Captions Track: {SUBTITLES_FILE}")
    print(f"[Completed] YouTube Upload Config: {UPLOAD_PAYLOAD_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
