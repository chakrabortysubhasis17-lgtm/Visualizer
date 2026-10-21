import os
import re
import sys
import json
import math
import time
import shutil
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
    build_srt_subtitles,
    format_timestamp,
    format_srt_time
)


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
        console.print(f"[success][✓][/success] {msg}")
    else:
        print(f"[✓] {msg}", flush=True)


def log_warning(msg: str):
    if RICH_AVAILABLE and console:
        console.print(f"[warning][!][/warning] {msg}")
    else:
        print(f"[!] {msg}", flush=True)


def log_error(msg: str):
    if RICH_AVAILABLE and console:
        console.print(f"[error][✗][/error] {msg}")
    else:
        print(f"[✗] {msg}", flush=True)


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
# CHANNEL INTRO SEGMENTS
# =====================================================================

def get_channel_intro_segments(narrator_voice: str = "en-US-GuyNeural") -> list:
    return [
        {
            "line_id": "intro_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Welcome to Being a Bong. If you enjoy our adaptations, please subscribe and let us know your thoughts in the comments to support future releases.",
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+5%"
        },
        {
            "line_id": "intro_pause_1s",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 1.0,
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        },
        {
            "line_id": "intro_02",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Let's jump straight into this episode.",
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+5%"
        },
        {
            "line_id": "intro_pause_2s",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 2.0,
            "voice": narrator_voice,
            "pitch": "+0Hz",
            "rate": "+0%"
        }
    ]


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
            dst = os.path.join(build_dir, fname)
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
    # PHASE 1: Scrape & Director Parsing with Real-time Learning
    # ---------------------------------------------------------
    log_info(f"[{novel_slug}] [Phase 1/5] Scraping Chapters & Parsing with Dynamic Registry...")
    staged_chapters = []
    narration_threshold = config.get("max_narration_merge", 650)
    narrator_voice = config.get("narrator_voice", "en-US-GuyNeural")

    with httpx.Client(follow_redirects=True, timeout=30.0) as session:
        curr_url = config["start_url"]
        for ch_num in range(start_ch, end_ch + 1):
            if not curr_url:
                log_warning(f"End of novel or missing next URL at Chapter {ch_num:03d}")
                break

            ch_json = os.path.join(build_dir, f"ch_{ch_num:03d}_staged.json")

            if os.path.exists(ch_json):
                try:
                    if AIOFILES_AVAILABLE:
                        async with aiofiles.open(ch_json, "r", encoding="utf-8") as f:
                            cached = clean_and_parse_json(await f.read())
                    else:
                        with open(ch_json, "r", encoding="utf-8") as f:
                            cached = clean_and_parse_json(f.read())

                    rows = cached.get("rows", [])
                    if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
                        raise ValueError(f"Corrupt or placeholder manifest in Ch {ch_num}")

                    title = cached.get("title", f"Ch {ch_num:03d}")
                    curr_url = cached.get("next_url") or scrape_chapter_content(
                        session, curr_url, ch_num, config.get("default_topic", "Arc")
                    )[2]

                    # Sync cached chapter character records into active staging
                    sync_new_characters_to_staging(stage_file, rows)

                    log_success(f"Ch {ch_num:03d}: Manifest verified and characters synced ({len(rows)} segments).")
                except Exception:
                    title, text, next_url = scrape_chapter_content(
                        session, curr_url, ch_num, config.get("default_topic", "Arc")
                    )
                    rows = parse_chapter_via_gemini_director(
                        gemini_client, title, text, stage_file, narration_threshold
                    )
                    curr_url = next_url
            else:
                title, text, next_url = scrape_chapter_content(
                    session, curr_url, ch_num, config.get("default_topic", "Arc")
                )
                rows = parse_chapter_via_gemini_director(
                    gemini_client, title, text, stage_file, narration_threshold
                )
                curr_url = next_url

            if ch_num == start_ch:
                intro_segments = get_channel_intro_segments(narrator_voice)
                if not any(r.get("line_id") == "intro_01" for r in rows):
                    rows = intro_segments + rows

            manifest_data = {"title": title, "rows": rows, "next_url": curr_url}
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(ch_json, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(manifest_data, indent=2, ensure_ascii=False))
            else:
                with open(ch_json, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2, ensure_ascii=False)

            staged_chapters.append((ch_num, rows, title))

    # EARLY PERSISTENCE: Save new characters immediately after Phase 1 staging
    log_info(f"[{novel_slug}] Persisting staged character discoveries to master registry...")
    finalize_and_merge_master_registry(novel_slug, stage_file)
    log_success("Master novel_entities_registry.json updated successfully.")

    # ---------------------------------------------------------
    # PHASE 2: Upfront Visual Engine (Covers & Dynamic Outro)
    # ---------------------------------------------------------
    log_info(f"[{novel_slug}] [Phase 2/5] Generating Visual Covers & Outro Slate UPFRONT...")
    blocks = config["blocks"]
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

    primary_thumb = config["cover_image"]
    if os.path.exists(blocks[0]["cover_file"]) and not os.path.exists(primary_thumb):
        shutil.copy2(blocks[0]["cover_file"], primary_thumb)
        log_success(f"Primary thumbnail created: '{primary_thumb}'")

    # ---------------------------------------------------------
    # PHASE 3: Concurrent Audio TTS Synthesis (Two-Tier Semaphore)
    # ---------------------------------------------------------
    log_info(f"[{novel_slug}] [Phase 3/5] Synthesizing Audio with Edge-TTS (Parallel Chapters)...")
    parallel_chapters = config.get("parallel_chapters", 3)
    global_max_tts = config.get("global_max_tts", 6)
    tts_workers_per_chapter = max(1, global_max_tts // parallel_chapters)

    chapter_semaphore = asyncio.Semaphore(parallel_chapters)
    log_info(f"Concurrency Setup: {parallel_chapters} Parallel Chapters | {tts_workers_per_chapter} Workers/Chapter")

    async def run_ch_bounded(cn, rw, tt):
        async with chapter_semaphore:
            ch_sem = asyncio.Semaphore(tts_workers_per_chapter)
            log_info(f"Spawning Chapter {cn:03d} execution ({len(rw)} segments)...")
            return await synthesize_chapter_task(cn, rw, tt, build_dir, ch_sem)

    all_results = await asyncio.gather(*[run_ch_bounded(cn, rw, tt) for cn, rw, tt in staged_chapters])
    all_results.sort(key=lambda x: x[0])

    chapter_files, chapter_durations, timestamps, all_subtitles = [], {}, [], []
    offset = 0.0

    for ch_num, mp3_path, dur, title, rel_subs in all_results:
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
    timestamps_file = config["timestamps_file"]
    timestamps_content = "\n".join(timestamps)
    if AIOFILES_AVAILABLE:
        async with aiofiles.open(timestamps_file, "w", encoding="utf-8") as f:
            await f.write(timestamps_content)
    else:
        with open(timestamps_file, "w", encoding="utf-8") as f:
            f.write(timestamps_content)
    log_success(f"Timestamps file written: '{timestamps_file}'")

    # Save Subtitles
    subtitles_file = config["subtitles_file"]
    build_srt_subtitles(all_subtitles, subtitles_file)
    log_success(f"Subtitles file written: '{subtitles_file}'")

    # ---------------------------------------------------------
    # PHASE 4: Audio Normalization (-14 LUFS)
    # ---------------------------------------------------------
    log_info(f"[{novel_slug}] [Phase 4/5] Normalizing Audio to -14 LUFS with 15s Outro Pad...")
    final_audio = config["final_audio"]
    master_final_audio(chapter_files, build_dir, final_audio)
    log_success(f"Master Audio complete: '{final_audio}'")

    # ---------------------------------------------------------
    # PHASE 5: Multiplexing Final Video
    # ---------------------------------------------------------
    log_info(f"[{novel_slug}] [Phase 5/5] Multiplexing Video Frames with Pre-rendered Images...")
    final_video = config["final_video"]
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
    payload_file = config["payload_file"]
    payload = {
        "snippet": {
            "title": config["video_title"],
            "description": f"{config.get('desc_header', '')}{chr(10).join(timestamps)}{config.get('desc_footer', '')}",
            "tags": config.get("tags", []),
            "categoryId": "24",
            "defaultLanguage": "en-US"
        },
        "status": {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": False
        },
        "assets": {
            "video_file": os.path.abspath(final_video),
            "thumbnail_file": os.path.abspath(primary_thumb),
            "subtitles_file": os.path.abspath(subtitles_file),
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

    # ---------------------------------------------------------
    # PHASE 6: Rich Completion Dashboard
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
        summary_table.add_row("Subtitles Track", subtitles_file, "Soft CC Embedded")
        summary_table.add_row("YouTube Payload", payload_file, "Metadata Ready")

        console.print("\n")
        console.print(summary_table)
        console.print("\n")
    else:
        print("\n" + "=" * 78)
        print("PRODUCTION RUN COMPLETED SUCCESSFULLY")
        print(f"• Audio: {final_audio} ({os.path.getsize(final_audio) // (1024*1024)} MB)")
        print(f"• Video: {final_video} ({os.path.getsize(final_video) // (1024*1024)} MB)")
        print(f"• Duration: {format_timestamp(offset)}")
        print("=" * 78 + "\n", flush=True)

    return {
        "audio_path": final_audio,
        "video_path": final_video,
        "duration": offset,
        "timestamps_path": timestamps_file,
        "subtitles_path": subtitles_file,
        "payload_path": payload_file
    }