import os
import sys
import json
import subprocess
from pathlib import Path

# Optional mutagen for fast audio duration inspection
try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


def probe_mp3_duration(file_path: str) -> float:
    """Inspects audio duration via mutagen or ffprobe."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 1024:
        return 0.0

    if MUTAGEN_AVAILABLE:
        try:
            audio = MP3(file_path)
            if audio.info and audio.info.length > 0:
                return float(audio.info.length)
        except Exception:
            pass

    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        return float(res.stdout.strip())
    except Exception:
        return 0.0


def format_duration(seconds: float) -> str:
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def verify_pipeline_run(config: dict):
    build_dir = config["build_dir"]
    start_ch = config["start_chapter"]
    end_ch = config["end_chapter"]
    blocks = config.get("blocks", [])

    print("\n" + "=" * 78)
    print(f"PIPELINE AUDIT REPORT: {config.get('novel_slug', 'Novel')}")
    print(f"Target Chapters: {start_ch} to {end_ch} | Build Directory: '{build_dir}'")
    print("=" * 78)

    if not os.path.exists(build_dir):
        print(f"\n[CRITICAL] Build directory '{build_dir}' does not exist. No files found.\n")
        return

    # ---------------------------------------------------------
    # 1. Audit Chapter-by-Chapter Assets
    # ---------------------------------------------------------
    total_chapters = (end_ch - start_ch) + 1
    staged_ok = 0
    audio_ok = 0
    meta_ok = 0

    corrupted_stages = []
    missing_stages = []
    missing_audio = []
    missing_meta = []
    total_duration_sec = 0.0

    print(f"\n[1/4] AUDITING CHAPTER ARTIFACTS ({start_ch} - {end_ch})...\n")
    print(f"{'Chapter':<10}{'Stage JSON':<16}{'Audio (MP3)':<18}{'Meta JSON':<15}{'Duration':<10}")
    print("-" * 78)

    for ch_num in range(start_ch, end_ch + 1):
        ch_prefix = f"ch_{ch_num:03d}"
        stage_file = os.path.join(build_dir, f"{ch_prefix}_staged.json")
        audio_file = os.path.join(build_dir, f"{ch_prefix}.mp3")
        meta_file = os.path.join(build_dir, f"{ch_prefix}_meta.json")

        # --- Check Stage JSON ---
        stage_status = "MISSING"
        if os.path.exists(stage_file):
            try:
                with open(stage_file, "r", encoding="utf-8") as f:
                    s_data = json.load(f)
                rows = s_data.get("rows", [])
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
                    stage_status = f"CORRUPT ({len(rows)} rows)"
                    corrupted_stages.append(ch_num)
                else:
                    stage_status = f"OK ({len(rows)} segs)"
                    staged_ok += 1
            except Exception:
                stage_status = "INVALID JSON"
                corrupted_stages.append(ch_num)
        else:
            missing_stages.append(ch_num)

        # --- Check MP3 Audio ---
        audio_status = "MISSING"
        ch_dur = 0.0
        if os.path.exists(audio_file):
            size_kb = os.path.getsize(audio_file) / 1024
            if size_kb > 10:
                ch_dur = probe_mp3_duration(audio_file)
                if ch_dur > 5.0:
                    audio_status = f"OK ({size_kb:.0f}KB)"
                    audio_ok += 1
                    total_duration_sec += ch_dur
                else:
                    audio_status = "EMPTY AUDIO"
                    missing_audio.append(ch_num)
            else:
                audio_status = f"TOO SMALL ({size_kb:.1f}KB)"
                missing_audio.append(ch_num)
        else:
            missing_audio.append(ch_num)

        # --- Check Meta JSON ---
        meta_status = "MISSING"
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    m_data = json.load(f)
                if m_data.get("duration", 0) > 5.0 and len(m_data.get("relative_subtitles", [])) > 0:
                    meta_status = "OK"
                    meta_ok += 1
                else:
                    meta_status = "INCOMPLETE"
                    missing_meta.append(ch_num)
            except Exception:
                meta_status = "INVALID JSON"
                missing_meta.append(ch_num)
        else:
            missing_meta.append(ch_num)

        dur_str = format_duration(ch_dur) if ch_dur > 0 else "--:--:--"
        print(f"Ch {ch_num:03d}     {stage_status:<16}{audio_status:<18}{meta_status:<15}{dur_str:<10}")

    # ---------------------------------------------------------
    # 2. Audit Visual Assets & Covers
    # ---------------------------------------------------------
    print("\n" + "-" * 78)
    print("[2/4] AUDITING VISUAL & COVER BLOCKS...")
    print("-" * 78)

    covers_ok = 0
    total_covers = len(blocks)
    for b in blocks:
        b_idx = b.get("index")
        r_start, r_end = b.get("range", (0, 0))
        cover_path = os.path.join(build_dir, f"cover_block_{r_start}_{r_end}.jpg")
        if os.path.exists(cover_path) and os.path.getsize(cover_path) > 10000:
            print(f"  [✓] Block {b_idx:02d} ({r_start}-{r_end}): Cover image verified ({os.path.getsize(cover_path) // 1024} KB)")
            covers_ok += 1
        else:
            print(f"  [✗] Block {b_idx:02d} ({r_start}-{r_end}): Cover image MISSING -> '{cover_path}'")

    outro_path = os.path.join(build_dir, "outro_slate_card.jpg")
    outro_ok = os.path.exists(outro_path) and os.path.getsize(outro_path) > 10000
    print(f"  [{'✓' if outro_ok else '✗'}] Outro Slate: {'Verified' if outro_ok else 'MISSING'}")

    primary_thumb = config.get("cover_image", "")
    thumb_ok = os.path.exists(primary_thumb) and os.path.getsize(primary_thumb) > 10000
    print(f"  [{'✓' if thumb_ok else '✗'}] Primary Video Thumbnail: {'Verified' if thumb_ok else 'MISSING'} ('{primary_thumb}')")

    # ---------------------------------------------------------
    # 3. Audit Final Master Artifacts
    # ---------------------------------------------------------
    print("\n" + "-" * 78)
    print("[3/4] AUDITING FINAL PRODUCTION DELIVERABLES...")
    print("-" * 78)

    artifacts = [
        ("Timestamps", config.get("timestamps_file"), 50),
        ("Subtitles SRT", config.get("subtitles_file"), 500),
        ("Master Audio", config.get("final_audio"), 100000),
        ("Final Video", config.get("final_video"), 500000),
        ("Upload Payload", config.get("payload_file"), 100),
    ]

    final_delivery_ready = True
    for label, fpath, min_bytes in artifacts:
        if fpath and os.path.exists(fpath) and os.path.getsize(fpath) >= min_bytes:
            sz_str = f"{os.path.getsize(fpath) / (1024 * 1024):.2f} MB" if os.path.getsize(fpath) > 1024 * 1024 else f"{os.path.getsize(fpath) / 1024:.1f} KB"
            print(f"  [✓] {label:<16}: {sz_str:<12} -> '{fpath}'")
        else:
            print(f"  [✗] {label:<16}: MISSING / INCOMPLETE -> '{fpath}'")
            final_delivery_ready = False

    # ---------------------------------------------------------
    # 4. Final Verdict & Resumption Advice
    # ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("STATUS SUMMARY & ACTION ITEMS")
    print("=" * 78)
    print(f"• Stage JSONs Ready  : {staged_ok}/{total_chapters}")
    print(f"• Synthesized Audio  : {audio_ok}/{total_chapters} (Total Track Duration: {format_duration(total_duration_sec)})")
    print(f"• Metadata Manifests : {meta_ok}/{total_chapters}")
    print(f"• Visual Cover Blocks: {covers_ok}/{total_covers}")

    if corrupted_stages:
        print(f"\n[!] WARNING: {len(corrupted_stages)} corrupted or placeholder stage file(s) found:")
        print(f"    Chapters: {corrupted_stages}")
        print("    --> These files will be automatically purged by the runner script so they re-scrape cleanly.")

    if missing_audio:
        print(f"\n[!] MISSING AUDIO: {len(missing_audio)} chapter(s) have not finished TTS synthesis:")
        print(f"    Chapters: {missing_audio}")

    if final_delivery_ready and audio_ok == total_chapters and staged_ok == total_chapters:
        print("\n[✓] ALL DELIVERABLES FULLY GENERATED AND VALIDATED! You do not need to re-run.")
    else:
        print("\n[ACTION REQUIRED] The batch was not completely assembled.")
        print("  Because completed chapters are safely cached on disk, re-running your script:")
        print(f"  >>> python {sys.argv[1] if len(sys.argv) > 1 else 'run_XXXX.py'}")
        print("  will skip already synthesized chapters and only resume the remaining/corrupted steps.")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith(".py"):
        runner_path = sys.argv[1]
        if not os.path.exists(runner_path):
            print(f"[Error] Specified runner file '{runner_path}' not found.")
            sys.exit(1)

        import importlib.util
        spec = importlib.util.spec_from_file_location("runner_module", runner_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "CONFIG"):
            verify_pipeline_run(mod.CONFIG)
        else:
            print("[Error] The runner file does not define a 'CONFIG' dictionary.")
    else:
        # Default verification for Harem Training 251-300 if no argument provided
        default_config = {
            "novel_slug": "harem-training-system-every-girl-i-train-makes-me-stronger",
            "start_chapter": 251,
            "end_chapter": 300,
            "build_dir": "build_harem_training_system_251_300",
            "final_audio": "output_harem_training_system_251_300.mp3",
            "final_video": "final_harem_training_system_251_300.mp4",
            "cover_image": "cover_harem_training_system_251_300.jpg",
            "timestamps_file": "youtube_timestamps_harem_training_system_251_300.txt",
            "subtitles_file": "subtitles_harem_training_system_251_300.srt",
            "payload_file": "youtube_upload_payload_harem_training_system_251_300.json",
            "blocks": [{"index": i, "range": (251 + (i - 1) * 5, 255 + (i - 1) * 5)} for i in range(1, 11)],
        }
        print("Tip: You can pass any runner file as an argument, e.g.:")
        print("     python verify_pipeline_outputs.py run_catgirls_and_dungeons_151_200.py\n")
        verify_pipeline_run(default_config)