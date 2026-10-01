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
START_CHAPTER = 401
END_CHAPTER = 450
START_CHAPTER_URL = "https://mtl-novel.com/novel/all-gods-starting-with-sss-level-talent/chapter-401-the-fairest-currency/"
NOVEL_SLUG = "all-gods-starting-with-sss-level-talent"

BUILD_DIR = "build_gods_401_450"
FINAL_AUDIO = "output_gods_401_450.mp3"
TIMESTAMPS_FILE = "youtube_timestamps_gods_401_450.txt"
SUBTITLES_FILE = "subtitles_gods_401_450.srt"
FINAL_VIDEO = "final_gods_401_450.mp4"
COVER_IMAGE = "cover_gods_401_450.jpg"
UPLOAD_PAYLOAD_FILE = "youtube_upload_payload_401_450.json"

NOVEL_TITLE_DISPLAY = [
    "THE FAIREST CURRENCY",
    "DIVINE COMMERCE & BILLION BELIEVERS",
    "Chapters 401 – 450 [Full Marathon]"
]

# CR-11: 5 Widescreen Visual Blocks (10 Chapters Each)
BLOCK_CONFIGS = [
    {
        "index": 1,
        "range": (401, 410),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_401_410.jpg"),
        "prompt": "A breathtaking cinematic 16:9 movie still of handsome 20-year-old Asian god Yang Fan dressed in radiant divine imperial robes standing inside an interstellar pantheon exchange pavilion. Floating crystalline divine power coins, pure faith origin orbs, and planetary market tickers hover in the air, divine merchants and elder appraisers looking on in deep astonishment, photorealistic, 8k resolution, cinematic lighting.",
        "title": ["THE FAIREST CURRENCY", "DIVINE MARKET MONOPOLY", "Chapters 401 – 410"],
        "fallback_color": (245, 195, 45)   # Divine Currency Gold
    },
    {
        "index": 2,
        "range": (411, 420),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_411_420.jpg"),
        "prompt": "A vibrant high-saturation fantasy scene, 16:9 widescreen, massive floating divine domain observed from orbit, millions of armored evolved believers organized into disciplined legions chanting prayers, high apostle Yang Da kneeling in reverence before a titanic golden phantom of Yang Fan manifested in the clouds, 8k resolution.",
        "title": ["DIVINE REALM MOBILIZATION", "YANG DA'S IRON LEGIONS", "Chapters 411 – 420"],
        "fallback_color": (35, 120, 220)   # Divine Domain Azure
    },
    {
        "index": 3,
        "range": (421, 430),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_421_430.jpg"),
        "prompt": "A cinematic fantasy movie still, 16:9 widescreen, handsome young deity standing before the high arbitration altar of the pantheon, crushing the arrogance of entitled divine clan scions, cascading pillars of radiant golden faith shockwaves leveling opposing pressure, high drama, cinematic masterpiece, 8k.",
        "title": ["CRUSHING DIVINE SCIONS", "UNCHECKED FAITH ADVANTAGE", "Chapters 421 – 430"],
        "fallback_color": (225, 60, 40)    # War & Retribution Red
    },
    {
        "index": 4,
        "range": (431, 440),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_431_440.jpg"),
        "prompt": "A vibrant cinematic fantasy scene, 16:9 widescreen, massive cosmic frontline where divine battleships and armored celestial apostles charge across void nebulae, tearing through enemy pantheon barriers under golden rain of divine decrees, photorealistic, volumetric god rays, 8k resolution.",
        "title": ["FRONTLINE VOID EXPEDITION", "BILLIONS IN FAITH EXTRACTION", "Chapters 431 – 440"],
        "fallback_color": (150, 60, 210)  # Sovereign Imperial Violet
    },
    {
        "index": 5,
        "range": (441, 450),
        "cover_file": os.path.join(BUILD_DIR, "cover_block_441_450.jpg"),
        "prompt": "A breathtaking cinematic 16:9 movie still, Yang Fan ascending to high-order godhood, his inner divine domain radiating multiple star systems, an immaculate golden halo encircling his brow as billions of believers ascend concurrently, photorealistic, 8k resolution, celestial grandeur.",
        "title": ["HIGH-ORDER GODHOOD", "THE SUPREME EVOLUTION DOMAIN", "Chapters 441 – 450"],
        "fallback_color": (255, 215, 60)  # Ascendant Supreme Gold
    }
]

YOUTUBE_CONFIG = {
    "title": "THE FAIREST CURRENCY: Flooding the Divine Market with SSS-Grade Resources | Full Audiobook [Ch. 401-450]",
    "categoryId": "24",
    "defaultLanguage": "en",
    "privacyStatus": "unlisted",
    "tags": [
        "All Gods Starting with SSS-level Talent",
        "all gods sss talent audiobook",
        "the fairest currency",
        "yang fan godhood",
        "divine kingdom evolution",
        "litrpg audiobook",
        "progression fantasy",
        "system apocalypse",
        "overpowered mc",
        "faith points",
        "divine domain",
        "tier 6 god",
        "full marathon audiobook",
        "chapters 401 to 450",
        "multi-voice audiobook"
    ],
    "description_header": (
        "Welcome to Chapters 401 through 450 of 'All Gods, Starting with SSS-level Talent' (全民神祇：开局觉醒SSS级天赋)!\n\n"
        "Stepping beyond regional academy trials into the vast macro-economy of the divine pantheon, Yang Fan arrives at the "
        "inter-deity market front. In an immortal realm where material trinkets mean nothing, what is the single 'fairest currency'? "
        "Pure, unadulterated divine power and sovereign faith origin.\n\n"
        "Armed with his SSS-grade Evolution Talent—allowing his inner kingdom to experience 10 years of accelerated civilization "
        "for every single day outside—Yang Fan leverages billions of fanatical believers, out-produces ancient god clans, "
        "and shatters the financial and military monopoly of the Upper Pantheon.\n\n"
        "Experience Chapters 401 to 450 in this definitive multi-voice marathon edition.\n\n"
        "🎧 Audio Master: Mobile-Engineered Pure Speech Master (-14 LUFS, Voice-Enhanced EQ, Brian Narrator).\n"
        "📖 Closed Captions: English Soft Subtitles (CC Enabled).\n"
        "📚 Original Novel: All Gods, Starting with SSS-level Talent (全民神祇：开局觉醒SSS级天赋)\n\n"
        "══════════════════════════════════════════════\n"
        "TIMESTAMPS:\n"
    ),
    "description_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🔥 ARC HIGHLIGHTS:\n"
        "• 00:00:00 - Chapter 401: The Fairest Currency\n"
        "• Liquidating Surplus Believer Produce at the Divine Exchange\n"
        "• High Apostle Yang Da's New Mobilization Directives\n"
        "• Crushing Arrogant Clan Scions in Divine Power Bidding\n"
        "• Mobilizing Multi-Billion Believer Legions Across the Void Front\n"
        "• Chapter 450: Consolidating High-Tier Godhood & Domain Monopoly\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited adaptation produced for storytelling and entertainment purposes. "
        "All original novel rights belong to the original author. Subscribe to follow Yang Fan's ascension!\n\n"
        "#WebNovelAudiobook #LitRPG #AllGods #SSSTalent #DivineKingdom #OverpoweredMC #AudiobookMarathon #FullAudiobook"
    )
}

# ==================== ARCHITECTURAL TUNING ====================
BATCH_SIZE = 10                  # Execute in strict blocks of 10 chapters
PARALLEL_CHAPTERS = 3            # Synthesize 3 chapters concurrently per batch
GLOBAL_MAX_CONCURRENT_TTS = 12   # Prevents IP throttling on Edge-TTS WebSocket
MAX_NARRATION_MERGE_WORDS = 230  # Merges narration paragraphs naturally
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
        "display_name": "Divine System",
        "gender": "Synthetic",
        "line_type": "System",
        "voice": "en-US-SteffanNeural",
        "pitch": "-18Hz",
        "rate": "-6%",
        "patterns": []
    },
    "yang_fan": {
        "display_name": "Yang Fan",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-GuyNeural",
        "pitch": "+0Hz",
        "rate": "+6%",
        "patterns": [
            r"\b(Yang Fan said|Yang Fan replied|Yang Fan smiled|Yang Fan asked|thought Yang Fan|Yang Fan thought|Yang Fan sneered|Yang Fan muttered|Yang Fan nodded|Yang Fan commanded)\b"
        ]
    },
    "yang_da": {
        "display_name": "Yang Da",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-ChristopherNeural",
        "pitch": "-4Hz",
        "rate": "+2%",
        "patterns": [
            r"\b(Yang Da|First Apostle|Chief Believer|Yang Da bowed|Yang Da replied solemnly|disciple Yang Da)\b"
        ]
    },
    "elder_god": {
        "display_name": "Elder God / Appraiser",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-RogerNeural",
        "pitch": "-12Hz",
        "rate": "-2%",
        "patterns": [
            r"\b(Elder|High God|Pavilion Master|Appraiser|Commander Gu|Patriarch|old god|General|Grandmaster)\b"
        ]
    },
    "arrogant_scion": {
        "display_name": "Arrogant Scion",
        "gender": "Male",
        "line_type": "Dialogue",
        "voice": "en-US-EricNeural",
        "pitch": "+6Hz",
        "rate": "+10%",
        "patterns": [
            r"\b(sneered|barked|courting death|fool|insolent|audacious|bastard|how dare you|coldly snorted|scoffed|Divine Child)\b"
        ]
    },
    "goddess_peer": {
        "display_name": "Goddess / Peer",
        "gender": "Female",
        "line_type": "Dialogue",
        "voice": "en-US-JennyNeural",
        "pitch": "+2Hz",
        "rate": "+8%",
        "patterns": [
            r"\b(Goddess|Miss Gu|young lady|Senior Sister|female deity|maiden exclaimed|girl whispered)\b"
        ]
    },
    "believer_mass": {
        "display_name": "Believer Commander",
        "gender": "Synthetic",
        "line_type": "Dialogue",
        "voice": "en-US-SteffanNeural",
        "pitch": "-15Hz",
        "rate": "+4%",
        "patterns": [
            r"\b(Believers roared|Legion shouted|Legion Commander|warrior yelled|Priest chanted)\b"
        ]
    }
}

COMPILED_SPEAKER_PATTERNS = []
for role_key, meta in CHARACTER_REGISTRY.items():
    for pat in meta["patterns"]:
        COMPILED_SPEAKER_PATTERNS.append((re.compile(pat, re.IGNORECASE), role_key))

PHONETIC_LEXICON = [
    (re.compile(r"\bYang Fan\b", re.I), "Yahng Fahn"),
    (re.compile(r"\bYang Da\b", re.I), "Yahng Dah"),
    (re.compile(r"\bQi\b"), "Chee"),
    (re.compile(r"\bDantian\b", re.I), "Dahn-tyen"),
    (re.compile(r"\bGodhead\b", re.I), "God-head"),
    (re.compile(r"\bGodhood\b", re.I), "God-hood"),
    (re.compile(r"\bFaith Points?\b", re.I), "Faith Points"),
    (re.compile(r"\bDivine Power\b", re.I), "Divine Power"),
    (re.compile(r"\bDivine Domain\b", re.I), "Divine Domain")
]

RE_SYSTEM = re.compile(
    r"(?:\[|【|〔|『|〖|［)"
    r"(Ding!|System|Talent|Evolution|Divine Domain|Divine Power|Faith|Believer|Godhood|Godhead|Currency|Tier|Notice|Host|Unlocked|Acquired|Prompt)"
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
    cleaned = re.sub(r"\bSSS-grade\b", "Triple S grade", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSSS-rank\b", "Triple S rank", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSS-grade\b", "Double S grade", cleaned, flags=re.I)
    cleaned = re.sub(r"\bS-grade\b", "S grade", cleaned, flags=re.I)
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
        raise ValueError(f"Target article container missing at: {url}")

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
                    if any(w in surrounding for w in ["i said", "i replied", "yang fan", "i commanded", "i muttered"]):
                        assigned_role = "yang_fan"
                    elif any(w in surrounding for w in ["yang da", "apostle", "my lord", "your divine will"]):
                        assigned_role = "yang_da"
                    elif any(w in surrounding for w in ["she said", "she gasped", "miss gu", "goddess"]):
                        assigned_role = "goddess_peer"
                    elif any(w in surrounding for w in ["roared", "shouted", "bastard", "courting death", "insolent"]):
                        assigned_role = "arrogant_scion"
                    elif any(w in surrounding for w in ["elder", "appraiser", "old god", "pavilion master"]):
                        assigned_role = "elder_god"
                    else:
                        assigned_role = "yang_fan"

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
    canvas = Image.new("RGBA", (width, height), (12, 10, 22, 255))
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
        d_over.line([(0, y), (width, y)], fill=(8, 10, 16, min(140, int(dist * 1.8))))

    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    draw.rectangle([(50, 50), (width - 50, height - 50)], outline=(50, 40, 25, 220), width=2)
    draw.rectangle([(64, 64), (width - 64, height - 64)], outline=(190, 150, 50, 180), width=1)

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
                print(f"     [TTS Timeout] Line {row['line_id']} ({len(text.split())} words) exceeded {chunk_timeout:.1f}s (Attempt {attempt}/{max_retries}).")
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
    print(f"=== Production Pipeline: Chapters {START_CHAPTER} to {END_CHAPTER} [All Gods Pantheon Marathon] ===")
    print("[*] Engine: Lightweight 1 FPS Visual Switch | Batches of 10 | Guy/Jenny Safe Voices | Brian Narrator")

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
    print(f"[Completed] Standalone Master Thumbnail: {COVER_IMAGE}")
    print(f"[Completed] Closed Captions Track: {SUBTITLES_FILE}")
    print(f"[Completed] YouTube Upload Config: {UPLOAD_PAYLOAD_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
