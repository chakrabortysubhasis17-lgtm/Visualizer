import os
import json
import shutil
import asyncio
import requests

from registry_utils import init_session_registry, finalize_and_merge_master_registry
from text_director_utils import scrape_chapter_content, parse_chapter_via_gemini_director, GENAI_AVAILABLE
from visual_utils import ensure_block_cover_jit, create_dynamic_outro_slate
from media_utils import (
    synthesize_chapter_task, master_final_audio, assemble_multi_image_video,
    format_timestamp, format_srt_time
)

try:
    from google import genai
except ImportError:
    genai = None

def get_channel_intro_segments(narrator_voice: str = "en-US-GuyNeural") -> list:
    """Creates spoken narrative hook separated by programmatic silent gaps."""
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

async def run_audiobook_pipeline(config: dict):
    build_dir = config["build_dir"]
    os.makedirs(build_dir, exist_ok=True)
    novel_slug = config["novel_slug"]
    start_ch = config["start_chapter"]
    end_ch = config["end_chapter"]
    branding = config["branding_assets"]

    print(f"=== Starting Marathon Production: {novel_slug} [Ch {start_ch}–{end_ch}] ===", flush=True)

    # 1. Sync Branding Assets
    for _, fname in branding.items():
        dst = os.path.join(build_dir, fname)
        if os.path.exists(fname):
            shutil.copy2(fname, dst)
            print(f"[Asset Sync] [✓] Copied '{fname}' -> '{build_dir}'.", flush=True)

    # 2. Step 1: Session Registry Isolation
    stage_file = os.path.join(build_dir, "session_entities_staged.json")
    init_session_registry(novel_slug, stage_file)

    gemini_client = None
    if GENAI_AVAILABLE and config.get("gemini_api_key"):
        try:
            gemini_client = genai.Client(api_key=config["gemini_api_key"])
            print("[Gemini Director] Client initialized successfully.", flush=True)
        except Exception as e:
            print(f"[Gemini Director Notice] Initialization skipped: {e}", flush=True)

    staged_chapters = []

    # Phase 1: Scraping & Director Parsing with Real-time Learning
    print(f"\n[{novel_slug}] [Phase 1/5] Scraping Chapters & Parsing with Dynamic Registry...", flush=True)
    with requests.Session() as session:
        curr_url = config["start_url"]
        for ch_num in range(start_ch, end_ch + 1):
            if not curr_url:
                break
            ch_json = os.path.join(build_dir, f"ch_{ch_num:03d}_staged.json")

            if os.path.exists(ch_json):
                try:
                    with open(ch_json, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    rows = cached.get("rows", [])
                    title = cached.get("title", f"Ch {ch_num:03d}")
                    curr_url = cached.get("next_url") or scrape_chapter_content(session, curr_url, ch_num, config.get("default_topic", "Arc"))[2]
                    print(f"     [Stage Cached] Ch.{ch_num:03d} verified on disk ({len(rows)} segments)", flush=True)
                except Exception:
                    title, text, next_url = scrape_chapter_content(session, curr_url, ch_num, config.get("default_topic", "Arc"))
                    rows = parse_chapter_via_gemini_director(gemini_client, title, text, stage_file, config.get("max_narration_merge", 210))
                    curr_url = next_url
            else:
                title, text, next_url = scrape_chapter_content(session, curr_url, ch_num, config.get("default_topic", "Arc"))
                rows = parse_chapter_via_gemini_director(gemini_client, title, text, stage_file, config.get("max_narration_merge", 210))
                curr_url = next_url

            # Prepend the channel intro with 1s and 2s silent pauses to Chapter 1
            if ch_num == start_ch:
                intro_segments = get_channel_intro_segments(config.get("narrator_voice", "en-US-GuyNeural"))
                if not any(r.get("line_id") == "intro_01" for r in rows):
                    rows = intro_segments + rows

            with open(ch_json, "w", encoding="utf-8") as f:
                json.dump({"title": title, "rows": rows, "next_url": curr_url}, f, indent=2, ensure_ascii=False)

            staged_chapters.append((ch_num, rows, title))

    # Phase 2: Upfront Visual Engine
    print(f"\n[{novel_slug}] [Phase 2/5] Generating Visual Covers & Outro Slate UPFRONT...", flush=True)
    blocks = config["blocks"]
    for cfg in blocks:
        cfg["cover_file"] = os.path.join(build_dir, f"cover_block_{cfg['range'][0]}_{cfg['range'][1]}.jpg")
        ensure_block_cover_jit(cfg, build_dir, branding, config.get("cf_account_id"), config.get("cf_api_token"))

    outro_slate = os.path.join(build_dir, "outro_slate_card.jpg")
    create_dynamic_outro_slate(outro_slate, build_dir, branding, next_ch_num=end_ch + 1)

    primary_thumb = config["cover_image"]
    if os.path.exists(blocks[0]["cover_file"]) and not os.path.exists(primary_thumb):
        shutil.copy2(blocks[0]["cover_file"], primary_thumb)

    # Phase 3: Audio TTS Synthesis
    print(f"\n[{novel_slug}] [Phase 3/5] Synthesizing Audio with Edge-TTS...", flush=True)
    global_sem = asyncio.Semaphore(config.get("global_max_tts", 3))
    chapter_semaphore = asyncio.Semaphore(config.get("parallel_chapters", 2))

    async def run_ch_bounded(cn, rw, tt):
        async with chapter_semaphore:
            return await synthesize_chapter_task(cn, rw, tt, build_dir, global_sem)

    all_results = []
    batch_size = config.get("batch_size", 5)
    for b_idx in range(0, len(staged_chapters), batch_size):
        batch = staged_chapters[b_idx:b_idx + batch_size]
        res = await asyncio.gather(*[run_ch_bounded(cn, rw, tt) for cn, rw, tt in batch])
        all_results.extend(res)

    all_results.sort(key=lambda x: x[0])
    chapter_files, chapter_durations, timestamps, all_subtitles = [], {}, [], []
    offset = 0.0

    for ch_num, mp3_path, dur, title, rel_subs in all_results:
        chapter_files.append(mp3_path)
        chapter_durations[ch_num] = dur
        timestamps.append(f"{format_timestamp(offset)} - {title}")
        for s_rel, e_rel, text in rel_subs:
            all_subtitles.append((format_srt_time(offset + s_rel), format_srt_time(offset + e_rel), text))
        offset += dur

    block_durations = {cfg["index"]: sum(chapter_durations.get(c, 0.0) for c in range(cfg["range"][0], cfg["range"][1] + 1)) for cfg in blocks}

    with open(config["timestamps_file"], "w", encoding="utf-8") as f:
        f.write("\n".join(timestamps))
    with open(config["subtitles_file"], "w", encoding="utf-8") as f:
        for idx, (s_time, e_time, text) in enumerate(all_subtitles, 1):
            f.write(f"{idx}\n{s_time} --> {e_time}\n{text}\n\n")

    # Phase 4: Audio Normalization (-14 LUFS)
    print(f"\n[{novel_slug}] [Phase 4/5] Normalizing Audio to -14 LUFS with 15s Outro Pad...", flush=True)
    master_final_audio(chapter_files, build_dir, config["final_audio"])

    # Phase 5: Multiplexing Final Video
    print(f"\n[{novel_slug}] [Phase 5/5] Multiplexing Video Frames with Pre-rendered Images...", flush=True)
    assemble_multi_image_video(blocks, block_durations, build_dir, config["final_audio"], config["final_video"])

    payload = {
        "snippet": {
            "title": config["video_title"],
            "description": f"{config['desc_header']}{chr(10).join(timestamps)}{config['desc_footer']}",
            "tags": config["tags"],
            "categoryId": "24",
            "defaultLanguage": "en-US"
        },
        "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
        "assets": {
            "video_file": os.path.abspath(config["final_video"]),
            "thumbnail_file": os.path.abspath(primary_thumb),
            "subtitles_file": os.path.abspath(config["subtitles_file"]),
            "timestamps_file": os.path.abspath(config["timestamps_file"])
        }
    }
    with open(config["payload_file"], "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Step 3: Closed-Loop Registry Final Merge
    print(f"\n[{novel_slug}] Re-merging newly discovered characters into master registry...", flush=True)
    finalize_and_merge_master_registry(novel_slug, stage_file)

    print(f"\n[✓] SUCCESS: Production Pipeline Completed! Output: '{config['final_video']}'", flush=True)
