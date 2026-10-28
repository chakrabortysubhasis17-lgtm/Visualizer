import os
import re
import sys
import json
import math
import time
import shutil
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

# =====================================================================
# OPTIONAL PERFORMANCE & UI LIBRARIES (Graceful Fallbacks)
# =====================================================================

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.theme import Theme
    RICH_AVAILABLE = True
    custom_theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "highlight": "bold magenta"
    })
    console = Console(theme=custom_theme)
except ImportError:
    RICH_AVAILABLE = False
    console = None

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    import json as orjson
    ORJSON_AVAILABLE = False

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

# Local Pipeline Modules
from registry_utils import (
    init_session_registry,
    finalize_and_merge_master_registry,
    sync_new_characters_to_staging
)
from text_director_utils import (
    scrape_chapter_content,
    parse_chapter_via_gemini_director,
    clean_and_parse_json,
    save_staged_json_async,
    load_staged_json_async
)
from visual_utils import ensure_block_cover_jit, create_dynamic_outro_slate
from media_utils import (
    synthesize_chapter_task,
    master_final_audio,
    assemble_multi_image_video,
    format_timestamp,
    format_srt_time,
    prepare_sfx_assets,
    normalize_sfx_key,
)
from subtitle_utils import generate_subtitles_bundle, build_srt_subtitles


# =====================================================================
# AUDIOBOOK TEXT & TTS PHONETIC SANITIZER (* & # DE-CENSORING)
# =====================================================================

def sanitize_chapter_title(title: str) -> str:
    """
    Normalizes chapter titles for natural neural narration:
    - Expands 'CH 012', 'Ch. 012', 'ch012', 'Chapter 012' -> 'Chapter 12'
    - Normalizes gaming/tier rank indicators in titles.
    """
    if not title:
        return title

    # Convert 'CH 012', 'Ch. 005', 'ch12' -> 'Chapter 12', 'Chapter 5' (strips leading zeroes)
    def _expand_chapter(match):
        num_str = match.group(1)
        clean_num = str(int(num_str)) if num_str.isdigit() else num_str
        return f"Chapter {clean_num}"

    # Matches "CH 012", "CH.012", "Chapter 012", "Ch 012"
    clean_title = re.sub(r'\b(?:CH|Ch|ch|Chapter|CHAPTER)\.?\s*0*(\d+)', _expand_chapter, title)
    
    # Expand rank tiers
    clean_title = re.sub(r'\bSSS-rank\b', 'Triple-S rank', clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'\bSS-rank\b', 'Double-S rank', clean_title, flags=re.IGNORECASE)
    
    return clean_title.strip()


def is_author_note_or_meta(text: str) -> bool:
    """
    Detects author's notes, chapter commentary, and website scraping leaks
    so they are not read aloud by the audiobook narrator.
    """
    if not text:
        return False
    clean = text.strip()
    patterns = [
        r"^(?:author['’\u2019]?s?\s*notes?|a/n)\s*:",
        r"^(?:author['’\u2019]?s?\s*notes?|a/n)\b",
        r"^note\s*from\s*(?:the\s*)?author",
        r"^translator['’\u2019]?s?\s*notes?",
        r"^editor['’\u2019]?s?\s*notes?"
    ]
    for pat in patterns:
        if re.search(pat, clean, flags=re.IGNORECASE):
            return True
    return False


def _preserve_case_replacement(pattern: re.Pattern, replacement_template: str, text: str) -> str:
    """
    Replaces regex matches while preserving original capitalization
    (ALL CAPS, Title Case, or lower case).
    """
    def _cb(match: re.Match) -> str:
        res = match.expand(replacement_template)
        orig = match.group(0)
        if orig.isupper():
            return res.upper()
        if orig[0].isupper():
            return res.capitalize()
        return res.lower()
    return pattern.sub(_cb, text)


def sanitize_audiobook_text(text: str) -> str:
    """
    Phonetic text sanitizer targeting aggregator symbols (*, #, @, $, !)
    and reading artifacts while preserving raw narrative integrity.
    """
    if not text:
        return text

    # 1. Strip trailing author notes if joined onto narrative lines
    text = re.sub(r'(?i)\n*(?:author[\'’\u2019]?s?\s*notes?|a/n)\s*:.*$', '', text)

    # 2. Purge aggregator scene divider symbol rows (e.g. "* * *", "###", "---", "***")
    text = re.sub(r'^\s*[\*#\-_=\s]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 3. De-censor aggregator profanity masks (*, #, @, $, !) into spoken English words
    censored_patterns = [
        # Fuck stems (f*ck, f***, f***ing, mothaf**ka)
        (re.compile(r'\b(mothaf|motherf)[\*#@!$]+ck?(ing|ed|er|s)?(?!\w)', re.I), r'\1uck\2'),
        (re.compile(r'\bf[\*#@!$]+ck(ing|ed|er|s)?(?!\w)', re.I), r'fuck\1'),
        (re.compile(r'\bf[\*#]{2,}(ing|ed|er|s)?(?!\w)', re.I), r'fuck\1'),
        (re.compile(r'\bf\*k(?!\w)', re.I), r'fuck'),
        (re.compile(r'\bwt[fF]\b'), r'what the fuck'),

        # Shit stems (sh*t, sh*tty, bullsh*t)
        (re.compile(r'\b(bull|horse|dip)?sh[\*#@!$]+tt?y(?!\w)', re.I), r'\1shitty'),
        (re.compile(r'\b(bull|horse|dip)?sh[\*#@!$]+t(s)?(?!\w)', re.I), r'\1shit\2'),
        (re.compile(r'\b(bull|horse|dip)?s[\*#]{2,}t(s)?(?!\w)', re.I), r'\1shit\2'),
        (re.compile(r'\b(bull|horse|dip)?s[\*#]{3,}y(?!\w)', re.I), r'\1shitty'),

        # Bitch stems (b*tch, b****)
        (re.compile(r'\bb[\*#@!$]+tch(es|ing)?(?!\w)', re.I), r'bitch\1'),
        (re.compile(r'\bb[\*#]{3,}(es)?(?!\w)', re.I), r'bitch\1'),

        # Ass / Asshole stems (a*s, a**s, a**hole, @sshole, bad*ss)
        (re.compile(r'\b(dumb|bad|jack)?[a@][\*#@!$]+s+(es)?(?!\w)', re.I), r'\1ass\2'),
        (re.compile(r'\b(dumb|bad|jack)?[a@][\*#@!$]{2,}(?!\w)', re.I), r'\1ass'),
        (re.compile(r'\b(dumb|bad|jack)?@ss(es|hole)?(?!\w)', re.I), r'\1ass\2'),
        (re.compile(r'\b[a@][\*#@!$]*ss?hole(s)?(?!\w)', re.I), r'asshole\1'),
        (re.compile(r'\b[a@][\*#@!$]+hole(s)?(?!\w)', re.I), r'asshole\1'),

        # Damn stems (d*mn, d#mn, god-d*mn)
        (re.compile(r'\b(god-?)?d[\*#@!$]+mn?(ed|ing)?(?!\w)', re.I), r'\1damn\2'),
        (re.compile(r'\b(god-?)?d[\*#]{2,}n?(?!\w)', re.I), r'\1damn'),

        # Bastard stems
        (re.compile(r'\bb[\*#@!$]+stard(s)?(?!\w)', re.I), r'bastard\1'),
        (re.compile(r'\bb[\*#]{4,}d(s)?(?!\w)', re.I), r'bastard\1'),

        # Dick / Cock / Prick
        (re.compile(r'\bd[\*#@!$]+ck(s|head)?(?!\w)', re.I), r'dick\1'),
        (re.compile(r'\bc[\*#@!$]+ck(s)?(?!\w)', re.I), r'cock\1'),
        (re.compile(r'\bpr[\*#@!$]+ck(s)?(?!\w)', re.I), r'prick\1'),

        # Pussy / Cunt
        (re.compile(r'\bp[\*#@!$]+ssy(ies)?(?!\w)', re.I), r'pussy\1'),
        (re.compile(r'\bc[\*#@!$]+nt(s)?(?!\w)', re.I), r'cunt\1'),

        # Whore / Slut
        (re.compile(r'\bwh[\*#@!$]+re(s)?(?!\w)', re.I), r'whore\1'),
        (re.compile(r'\bsl[\*#@!$]+t(s)?(?!\w)', re.I), r'slut\1'),
    ]

    for pat, template in censored_patterns:
        text = _preserve_case_replacement(pat, template, text)

    # 4. Remove standalone and intra-word hashtag leaks (# 1 -> Number 1, stray # stripped)
    text = re.sub(r'#\s*(\d+)', r'Number \1', text)
    text = re.sub(r'(?<=\w)[#@$](?=\w)', '', text)
    text = re.sub(r'\s+#+\s+', ' ', text)

    # 5. Trailing Dash Breath Falloff (Prevents unnatural hanging high pitch)
    text = re.sub(r'(?<=[a-zA-Z0-9])[\u2014\u2013-]{1,2}(?=\s*["\'\u201d\u2019]|\s*$)', '...', text)
    text = re.sub(r'\s+[\u2014\u2013]+\s+', ', ', text)

    # 6. LitRPG / Gaming Multipliers & Terms
    text = re.sub(r'\bSSS-rank\b', 'Triple-S rank', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSS-rank\b', 'Double-S rank', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(\d+)x\s+(stat|speed|strength|buff|boost|multiplier)', r'\1-times \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\b1v1\b', 'one-on-one', text, flags=re.IGNORECASE)
    text = re.sub(r'\bso much DA\b', 'so much damage', text)

    # 7. Japanese Loanwords that Edge-TTS flattens
    text = re.sub(r'\bKitsune\b', 'Kit-soo-nay', text)
    text = re.sub(r'\bkitsune\b', 'kit-soo-nay', text)

    # 8. The "World Wide Web" Stutter Trap
    text = re.sub(r'(?i)\b[wW]-[wW]-[wW]\s+what\b', 'Wh-what', text)
    text = re.sub(r'(?i)\b[wW]-[wW]-[wW]\b', 'W... w... w...', text)

    # 9. Targeted Dialogue Stutters (Preserves compound hyphenated words like 'C-rank')
    def _stutter_sub(match):
        prefix = match.group(1)
        word = match.group(2)
        if prefix.lower() == word[0].lower():
            return f"{prefix}... {word}"
        return match.group(0)

    text = re.sub(r'\b([A-Za-z])-([A-Za-z]+)\b', _stutter_sub, text)
    text = re.sub(r'\bI-I\b', 'I... I', text)
    text = re.sub(r'\bi-i\b', 'i... i', text)

    # 10. Combat Gasps, Chokes & Novel Sound Effects
    text = re.sub(r'\bGHK-?\b', '*gasp-*', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTCH\b', 'Tsk', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTch\b', 'Tsk', text)
    text = re.sub(r'\bPFT+T*\b', 'Pff', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpfft+\b', 'pff', text, flags=re.IGNORECASE)
    text = re.sub(r'\bFu,\s*(so\s+complicated)', r'Whew, \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:THWIP\s*){2,}', 'Thwip! Thwip! ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCRK\.?\b', 'Crack!', text, flags=re.IGNORECASE)
    text = re.sub(r'\bKABAG\b', 'Kabam!', text, flags=re.IGNORECASE)

    # 11. Elongated Screams & Hyphenated Explosions
    text = re.sub(r'\bBO+BO+BO+M+\b', 'Kaboom!', text, flags=re.IGNORECASE)
    text = re.sub(r'\bB[oO]{2,}(?:-[oO]+)*-?m+\b', 'Boom!', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[rR]{2,}-[oO]+-[aA]+-[rR]+\b', 'Roar!', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDE-BOOM\b', 'Boom!', text, flags=re.IGNORECASE)

    # 12. Punctuation Punch on Standalone Action Words
    text = re.sub(
        r'\b(Chomp|Glug|Splat|Thud|Bang|Boom|Clang|Swish|Fwoosh|Fwush|Jingle|Whack|Thwack)\.',
        r'\1!',
        text
    )

    return text.strip()


# =====================================================================
# LOGGING & TERMINAL FORMATTING HELPERS
# =====================================================================

def log_info(msg: str):
    if RICH_AVAILABLE and console:
        console.print(f"[info][INFO][/info] {msg}")
    else:
        print(f"[INFO] {msg}", flush=True)


def log_success(msg: str):
    if RICH_AVAILABLE and console:
        console.print(f"[success][OK][/success] {msg}")
    else:
        print(f"[OK] {msg}", flush=True)


def log_warning(msg: str):
    if RICH_AVAILABLE and console:
        console.print(f"[warning][!][/warning] {msg}")
    else:
        print(f"[!] {msg}", flush=True)


def log_error(msg: str):
    if RICH_AVAILABLE and console:
        console.print(f"[error][X][/error] {msg}")
    else:
        print(f"[X] {msg}", flush=True)


def log_banner(title: str, subtitle: str = ""):
    if RICH_AVAILABLE and console:
        content = Text(f"{title}\n", style="bold cyan")
        if subtitle:
            content.append(f"{subtitle}", style="dim white")
        console.print(Panel(content, border_style="cyan", expand=False))
    else:
        print("\n" + "=" * 78)
        print(f"{title.upper()} - {subtitle}")
        print("=" * 78 + "\n", flush=True)


# =====================================================================
# DYNAMIC CHANNEL INTRO SEGMENTS
# =====================================================================

def get_channel_intro_segments(
    start_chapter: int = 1,
    intro_hook: str = "",
    narrator_voice: str = "en-US-ChristopherNeural"
) -> list:
    chapter_status_text = (
        "Welcome to the opening episode of this series. A brand-new adventure awaits, and we are glad to have you with us."
        if start_chapter == 1
        else "In this episode, we step right back into the series, continuing exactly where we left off in our previous episode."
    )

    segments = [
        {
            "line_id": "intro_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Welcome back to Being a Bong! We narrate the unreal worlds to life.",
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "-1%",
            "sfx": "intro"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.6,
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        },
        {
            "line_id": "intro_02_status",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": chapter_status_text,
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        },
        {
            "line_id": "intro_pause_02",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.6,
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        }
    ]

    if intro_hook and intro_hook.strip():
        segments.extend([
            {
                "line_id": "intro_03_hook",
                "speaker": "Narrator",
                "gender": "Male",
                "line_type": "Narration",
                "text": intro_hook.strip(),
                "voice": narrator_voice,
                "pitch": "+0Hz",
                "rate": "-1%"
            },
            {
                "line_id": "intro_pause_03",
                "speaker": "Narrator",
                "gender": "Male",
                "line_type": "Narration",
                "text": "",
                "pause_duration": 0.8,
                "voice": narrator_voice,
                "pitch": "+0Hz",
                "rate": "+0%"
            }
        ])

    segments.extend([
        {
            "line_id": "intro_04_cta",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": ".. but before the world unfolds, do me a quick favor: hit that like button, and if you're new here, subscribe to the channel and drop a comment below.",
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        },
        {
            "line_id": "intro_pause_04",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.8,
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        },
        {
            "line_id": "intro_05_closer",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Adjust your volume, settle in, and let's begin today's episode.",
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "-1%"
        },
        {
            "line_id": "intro_lead_in_pause",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 1.6,
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        }
    ])

    return segments


# =====================================================================
# IMAGE INTEGRITY CHECK
# =====================================================================

def verify_cover_integrity(image_path: str) -> bool:
    if not os.path.exists(image_path) or os.path.getsize(image_path) < 5000:
        return False

    if CV2_AVAILABLE:
        try:
            mat = cv2.imread(image_path)
            if mat is not None and mat.shape[0] >= 400 and mat.shape[1] >= 400:
                return True
        except Exception:
            pass

    if PILLOW_AVAILABLE:
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    return os.path.getsize(image_path) > 10000


# =====================================================================
# MAIN PIPELINE ORCHESTRATOR
# =====================================================================

async def run_audiobook_pipeline(config: dict) -> dict:
    build_dir = config["build_dir"]
    os.makedirs(build_dir, exist_ok=True)

    # SFX assets are copied up front so the build directory is self-contained.
    # synthesize_chapter_task also calls this helper defensively; the helper is idempotent.
    sfx_dir = prepare_sfx_assets(build_dir)
    log_info(f"SFX asset directory ready: '{sfx_dir}'")

    novel_slug = config.get("novel_slug", "novel")
    start_ch = config["start_chapter"]
    end_ch = config["end_chapter"]
    branding = config.get("branding_assets", {})

    log_banner(
        f"AUDIOBOOK PRODUCTION PIPELINE: {novel_slug.upper()}",
        f"Chapters {start_ch} to {end_ch} | Build Dir: '{build_dir}'"
    )

    # 1. Sync Branding Assets
    for _, fname in branding.items():
        if fname and os.path.exists(fname):
            dst = os.path.join(build_dir, os.path.basename(fname))
            shutil.copy2(fname, dst)
            log_success(f"Branding Asset Synced: '{fname}' -> '{build_dir}'")

    # 2. Session Registry Isolation
    stage_file = os.path.join(build_dir, "session_entities_staged.json")
    init_session_registry(novel_slug, stage_file)
    log_success(f"Session character registry initialized: '{stage_file}'")

    # 3. Initialize Gemini Client
    gemini_client = None
    gemini_key = config.get("gemini_api_key", "")
    if GENAI_AVAILABLE and genai and gemini_key:
        try:
            gemini_client = genai.Client(api_key=gemini_key)
            log_success("Gemini Director client initialized successfully.")
        except Exception as e:
            log_warning(f"Gemini client initialization skipped: {e}. Rule-based fallback active.")
    else:
        log_info("Gemini API key not supplied or SDK missing. Rule-based staging active.")

    # ---------------------------------------------------------
    # STEP 2: Visual Engine (Background Task)
    # ---------------------------------------------------------
    blocks = config.get("blocks", [])
    if not blocks:
        single_cover = config.get("cover_image", os.path.join(build_dir, "cover.jpg"))
        blocks = [{"index": 0, "range": (start_ch, end_ch), "cover_file": single_cover}]

    primary_thumb = config.get("cover_image", os.path.join(build_dir, "cover.jpg"))

    def _execute_visuals_sync():
        log_info(f"[{novel_slug}] [Step 2: Visual Engine] Spawning background cover and outro slate generation...")
        for cfg in blocks:
            r_start, r_end = cfg["range"]
            cfg["cover_file"] = os.path.join(build_dir, f"cover_block_{r_start}_{r_end}.jpg")
            ensure_block_cover_jit(
                cfg,
                build_dir,
                branding,
                config.get("cf_account_id"),
                config.get("cf_api_token")
            )
            if verify_cover_integrity(cfg["cover_file"]):
                log_success(f"Block {cfg.get('index', 1):02d} Cover verified: '{os.path.basename(cfg['cover_file'])}'")

        outro_slate = os.path.join(build_dir, "outro_slate_card.jpg")
        create_dynamic_outro_slate(outro_slate, build_dir, branding, next_ch_num=end_ch + 1)
        if verify_cover_integrity(outro_slate):
            log_success("Outro slate card verified.")

        if blocks and os.path.exists(blocks[0]["cover_file"]) and not os.path.exists(primary_thumb):
            shutil.copy2(blocks[0]["cover_file"], primary_thumb)
            log_success(f"Primary thumbnail created: '{primary_thumb}'")

    visuals_background_task = asyncio.create_task(asyncio.to_thread(_execute_visuals_sync))

    # ---------------------------------------------------------
    # STEPS 1 & 3: STREAMING PIPELINE (Producer -> Consumer via Queue)
    # ---------------------------------------------------------
    parallel_chapters = config.get("parallel_chapters", 3)
    global_max_tts = config.get("global_max_tts", 6)
    tts_workers_per_chapter = max(1, global_max_tts // parallel_chapters)
    narration_threshold = config.get("max_narration_merge", 650)
    narrator_voice = config.get("narrator_voice", "en-US-ChristopherNeural")

    chapter_queue: asyncio.Queue = asyncio.Queue(maxsize=parallel_chapters * 2)
    synthesized_results: List[Tuple[int, str, float, str, list]] = []
    results_lock = asyncio.Lock()

    # Step 3 Consumer Worker
    async def tts_consumer_worker(worker_id: int):
        while True:
            item = await chapter_queue.get()
            if item is None:
                chapter_queue.task_done()
                break
            ch_num, rows, title = item
            ch_sem = asyncio.Semaphore(tts_workers_per_chapter)
            log_info(f"[TTS Worker {worker_id}] Spawning Chapter {ch_num:03d} execution ({len(rows)} segments)...")
            res = await synthesize_chapter_task(ch_num, rows, title, build_dir, ch_sem)
            async with results_lock:
                synthesized_results.append(res)
            chapter_queue.task_done()

    consumer_tasks = [
        asyncio.create_task(tts_consumer_worker(i + 1))
        for i in range(parallel_chapters)
    ]

    # Step 1 Producer
    def _parse_single_chapter_sync(session, ch_num, curr_url):
        ch_json = os.path.join(build_dir, f"ch_{ch_num:03d}_staged.json")
        if os.path.exists(ch_json):
            try:
                with open(ch_json, "r", encoding="utf-8") as f:
                    cached = clean_and_parse_json(f.read())

                rows = cached.get("rows", [])
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
                    raise ValueError(f"Corrupt or placeholder manifest in Ch {ch_num}")

                # Old staged manifests predate SFX. Preserve their existing narration by
                # default and fill only the additive metadata field. Explicitly enable
                # refresh_legacy_cache_for_sfx in config to re-scrape/re-parse these rows.
                # That opt-in may regenerate narration, so it is never done silently.
                parsed_rows = [
                    r for r in rows
                    if not str(r.get("line_id", "")).startswith("intro_")
                ]
                if any("sfx" not in r for r in parsed_rows):
                    refresh_legacy_sfx = bool(config.get("refresh_legacy_cache_for_sfx", False))
                    if curr_url and refresh_legacy_sfx:
                        raise ValueError(f"Legacy staged manifest missing SFX field in Ch {ch_num}")
                    for r in rows:
                        r.setdefault("sfx", "")
                    if refresh_legacy_sfx and not curr_url:
                        log_warning(
                            f"Ch {ch_num:03d}: legacy staged manifest cannot be refreshed for SFX "
                            "because no scrape URL is available; preserving narration with blank SFX tags."
                        )
                    elif not refresh_legacy_sfx:
                        log_info(
                            f"Ch {ch_num:03d}: preserving legacy staged narration unchanged; "
                            "missing SFX tags default to blank. Set refresh_legacy_cache_for_sfx=true "
                            "to explicitly regenerate legacy staging."
                        )

                title = cached.get("title", f"Ch {ch_num:03d}")
                cached_next = cached.get("next_url")
                if cached_next:
                    curr_url = cached_next
                elif curr_url:
                    curr_url = scrape_chapter_content(
                        session, curr_url, ch_num, config.get("default_topic", "Arc")
                    )[2]

                sync_new_characters_to_staging(stage_file, rows)
                log_success(f"Ch {ch_num:03d}: Manifest verified and characters synced ({len(rows)} segments).")
                return title, rows, curr_url
            except Exception:
                if not curr_url:
                    log_warning(f"Missing scrape URL at Chapter {ch_num:03d}")
                    return None, None, None
                title, text, next_url = scrape_chapter_content(
                    session, curr_url, ch_num, config.get("default_topic", "Arc")
                )
                rows = parse_chapter_via_gemini_director(
                    gemini_client,
                    title,
                    text,
                    stage_file,
                    narration_threshold,
                    refresh_legacy_cache_for_sfx=bool(config.get("refresh_legacy_cache_for_sfx", False)),
                )
                return title, rows, next_url
        else:
            if not curr_url:
                log_warning(f"End of novel or missing next URL at Chapter {ch_num:03d}")
                return None, None, None
            title, text, next_url = scrape_chapter_content(
                session, curr_url, ch_num, config.get("default_topic", "Arc")
            )
            rows = parse_chapter_via_gemini_director(
                gemini_client,
                title,
                text,
                stage_file,
                narration_threshold,
                refresh_legacy_cache_for_sfx=bool(config.get("refresh_legacy_cache_for_sfx", False)),
            )
            return title, rows, next_url

    async def step1_producer_scrape_and_parse():
        log_info(f"[{novel_slug}] [Streaming Pipe] Step 1 (Scraper/Director) & Step 3 (TTS) active concurrently...")
        with httpx.Client(follow_redirects=True, timeout=30.0) as session:
            curr_url = config.get("start_url")
            for ch_num in range(start_ch, end_ch + 1):
                title, rows, next_url = await asyncio.to_thread(
                    _parse_single_chapter_sync, session, ch_num, curr_url
                )
                if rows is None:
                    break
                curr_url = next_url

                # Normalize title pronunciation
                title = sanitize_chapter_title(title)

                #print("HELLO IAM HERE");

                # Clean text and filter out author notes
                cleaned_rows = []
                for r in rows:
                    txt = r.get("text", "")
                    if is_author_note_or_meta(txt):
                        continue
                    r["text"] = sanitize_audiobook_text(txt)
                    # Persist only an allowed lowercase SFX key, or an empty string.
                    # This also gives generated intro/pause rows an explicit SFX field.
                    r["sfx"] = normalize_sfx_key(r.get("sfx", ""))
                    cleaned_rows.append(r)
                rows = cleaned_rows

                # Prepend dynamic intro to the first chapter in this run
                if ch_num == start_ch:
                    intro_hook = config.get("intro_hook", "")
                    intro_segments = get_channel_intro_segments(
                        start_chapter=start_ch,
                        intro_hook=intro_hook,
                        narrator_voice=narrator_voice
                    )
                    non_intro_rows = [r for r in rows if not str(r.get("line_id", "")).startswith("intro_")]
                    rows = intro_segments + non_intro_rows

                # Normalize all rows again after intro insertion so every staged row,
                # including generated intro and pause segments, has a valid SFX field.
                for r in rows:
                    r["sfx"] = normalize_sfx_key(r.get("sfx", ""))

                manifest_data = {"title": title, "rows": rows, "next_url": curr_url}
                ch_json = os.path.join(build_dir, f"ch_{ch_num:03d}_staged.json")
                if AIOFILES_AVAILABLE:
                    async with aiofiles.open(ch_json, "w", encoding="utf-8") as f:
                        await f.write(json.dumps(manifest_data, indent=2, ensure_ascii=False))
                else:
                    with open(ch_json, "w", encoding="utf-8") as f:
                        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

                await chapter_queue.put((ch_num, rows, title))

        log_info(f"[{novel_slug}] Persisting staged character discoveries to master registry...")
        finalize_and_merge_master_registry(novel_slug, stage_file)
        log_success("Master novel_entities_registry.json updated successfully.")

        for _ in range(parallel_chapters):
            await chapter_queue.put(None)

    await step1_producer_scrape_and_parse()

    await asyncio.gather(
        visuals_background_task,
        asyncio.gather(*consumer_tasks)
    )
    log_success("Steps 1, 2, and 3 complete: Staging, background visuals, and audio synthesis verified.")

    synthesized_results.sort(key=lambda x: x[0])

    chapter_files, chapter_durations, timestamps, all_subtitles = [], {}, [], []
    offset = 0.0

    for ch_num, mp3_path, dur, title, rel_subs in synthesized_results:
        chapter_files.append(mp3_path)
        chapter_durations[ch_num] = dur
        timestamps.append(f"{format_timestamp(offset)} - {title}")

        for item in rel_subs:
            if isinstance(item, (tuple, list)):
                s_rel, e_rel, text = item[0], item[1], item[2]
            elif isinstance(item, dict):
                s_rel, e_rel, text = item["start"], item["end"], item["text"]
            else:
                continue
            all_subtitles.append((offset + s_rel, offset + e_rel, text))

        offset += dur

    block_durations = {
        cfg["index"]: sum(chapter_durations.get(c, 0.0) for c in range(cfg["range"][0], cfg["range"][1] + 1))
        for cfg in blocks
    }

    # Save Timestamps
    timestamps_file = config.get("timestamps_file", os.path.join(build_dir, "timestamps.txt"))
    timestamps_content = "\n".join(timestamps)
    if AIOFILES_AVAILABLE:
        async with aiofiles.open(timestamps_file, "w", encoding="utf-8") as f:
            await f.write(timestamps_content)
    else:
        with open(timestamps_file, "w", encoding="utf-8") as f:
            f.write(timestamps_content)
    log_success(f"Timestamps file written: '{timestamps_file}'")

    # English Master Subtitles
    subtitles_file = config.get("subtitles_file", os.path.join(build_dir, "subtitles.srt"))
    build_srt_subtitles(all_subtitles, subtitles_file)
    log_success(f"English Master Subtitles written: '{subtitles_file}'")

    # ---------------------------------------------------------
    # PHASE 4: Audio Normalization (-14 LUFS) & VST3 Mastering
    # ---------------------------------------------------------
    log_info(f"[{novel_slug}] [Phase 4/5] Normalizing Audio to -14 LUFS with Studio Mastering...")
    final_audio = config.get("final_audio", os.path.join(build_dir, "final_audio.mp3"))
    master_final_audio(
        chapter_files=chapter_files,
        build_dir=build_dir,
        final_audio_path=final_audio,
        enable_voicefixer=config.get("enable_voicefixer", False)
    )
    log_success(f"Master Audio complete: '{final_audio}'")

    # ---------------------------------------------------------
    # PHASE 5: Multiplexing Final Video
    # ---------------------------------------------------------
    log_info(f"[{novel_slug}] [Phase 5/5] Multiplexing Video Frames with Pre-rendered Images & Subtitles...")
    final_video = config.get("final_video", os.path.join(build_dir, "final_video.mp4"))
    assemble_multi_image_video(
        blocks=blocks,
        block_durations=block_durations,
        build_dir=build_dir,
        final_audio_path=final_audio,
        output_video_path=final_video,
        subtitles_srt_path=subtitles_file
    )
    log_success(f"Final Video rendered: '{final_video}'")

    # Save Complete Upload Payload
    payload_file = config.get("payload_file", os.path.join(build_dir, "upload_payload.json"))
    payload = {
        "snippet": {
            "title": config.get("video_title", f"{novel_slug.upper()} Ch {start_ch}-{end_ch}"),
            "description": f"{config.get('desc_header', '')}{chr(10).join(timestamps)}{config.get('desc_footer', '')}",
            "tags": config.get("tags", []),
            "categoryId": "24",
            "defaultLanguage": "en-US"
        },
        "status": {
            "privacyStatus": config.get("privacy_status", "unlisted"),
            "selfDeclaredMadeForKids": False
        },
        "assets": {
            "video_file": os.path.abspath(final_video),
            "thumbnail_file": os.path.abspath(primary_thumb),
            "subtitles_file": os.path.abspath(subtitles_file),
            "subtitles_dir": os.path.abspath(os.path.join(build_dir, "subtitles")),
            "timestamps_file": os.path.abspath(timestamps_file)
        }
    }
    if AIOFILES_AVAILABLE:
        async with aiofiles.open(payload_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        with open(payload_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    log_success(f"Upload payload generated: '{payload_file}'")

    # ---------------------------------------------------------
    # STEP 3: Closed-Loop Registry Final Safety Flush
    # ---------------------------------------------------------
    finalize_and_merge_master_registry(novel_slug, stage_file)
    log_success("Master novel_entities_registry.json merged and verified.")

    # ---------------------------------------------------------
    # PHASE 6: Multilingual Subtitles Engine
    # ---------------------------------------------------------
    subtitles_bundle = {}
    if config.get("enable_subtitles", True):
        log_info(f"[{novel_slug}] Starting Post-Render Multilingual Subtitle Translations...")
        target_langs = config.get("subtitle_languages", [
            "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
        ])
        subtitles_bundle = generate_subtitles_bundle(
            base_subtitles=all_subtitles,
            build_dir=build_dir,
            target_languages=target_langs
        )
        log_success(f"Multilingual subtitles complete: '{os.path.join(build_dir, 'subtitles')}' ({len(subtitles_bundle)} tracks)")

    # ---------------------------------------------------------
    # PHASE 7: Summary Dashboard
    # ---------------------------------------------------------
    if RICH_AVAILABLE and console:
        summary_table = Table(title="Production Run Summary", border_style="cyan")
        summary_table.add_column("Artifact", style="bold white")
        summary_table.add_column("Path / Specification", style="cyan")
        summary_table.add_column("Status", style="bold green")

        summary_table.add_row("Total Chapters", f"{start_ch} to {end_ch} ({len(chapter_files)} chs)", "Completed")
        summary_table.add_row("Run Duration", format_timestamp(offset), "Verified")
        summary_table.add_row("Master Audio", final_audio, f"{os.path.getsize(final_audio) // (1024*1024)} MB")
        summary_table.add_row("Final Video", final_video, f"{os.path.getsize(final_video) // (1024*1024)} MB")
        summary_table.add_row("Subtitles Tracks", f"{len(subtitles_bundle)} Languages in build/subtitles/", "Soft CC Ready")
        summary_table.add_row("YouTube Payload", payload_file, "Metadata Ready")

        console.print("\n")
        console.print(summary_table)
        console.print("\n")
    else:
        print("\n" + "=" * 78)
        print("PRODUCTION RUN COMPLETED SUCCESSFULLY")
        print(f"* Audio: {final_audio} ({os.path.getsize(final_audio) // (1024*1024)} MB)")
        print(f"* Video: {final_video} ({os.path.getsize(final_video) // (1024*1024)} MB)")
        print(f"* Subtitles: {len(subtitles_bundle)} tracks in build/subtitles/")
        print(f"* Duration: {format_timestamp(offset)}")
        print("=" * 78 + "\n", flush=True)

    return {
        "status": "success",
        "audio_path": final_audio,
        "video_path": final_video,
        "audio_file": final_audio,
        "video_file": final_video,
        "duration": offset,
        "timestamps_path": timestamps_file,
        "timestamps_file": timestamps_file,
        "subtitles_path": subtitles_file,
        "subtitles": subtitles_bundle,
        "payload_path": payload_file,
        "upload_payload": payload_file
    }