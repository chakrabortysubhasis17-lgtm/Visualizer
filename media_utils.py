import os
import re
import json
import random
import asyncio
import subprocess
import edge_tts

RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')
RE_PAUSE_TAGS = re.compile(r'\[(?:pause|Pause)\s*[\w\s.]*\]|\((?:pause|Pause)\s*[\w\s.]*\)', re.I)

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

async def synthesize_line_record(row: dict, out_file: str, sem: asyncio.Semaphore, max_retries: int = 5):
    if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
        return

    pause_dur = row.get("pause_duration")
    raw_text = row.get("text", "").strip()
    text = RE_PAUSE_TAGS.sub("", raw_text).strip()

    # Programmatic silence gap for pauses
    if pause_dur or not text or not RE_ALPHANUM.search(text):
        dur = float(pause_dur) if pause_dur else 0.5
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", f"{dur:.2f}", "-q:a", "9", "-acodec", "libmp3lame", out_file
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    line_type = row.get("line_type", "Narration")
    is_system = (line_type == "System")

    # Narrator remains completely standard en-US-GuyNeural
    if is_system:
        # Female mecha voice strictly for System prompts
        voice = "en-US-AriaNeural"
        pitch = "-2Hz"
        rate = "+0%"
    else:
        # Dialogue and Narrator keep their configured voices
        voice = row.get("voice", "en-US-GuyNeural")
        pitch = row.get("pitch", "+0Hz")
        rate = row.get("rate", "+5%")

    chunk_timeout = max(35.0, 25.0 + (len(text.split()) * 0.40))
    raw_tts_file = out_file + ".raw.mp3" if is_system else out_file

    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                active_voice = voice
                if attempt >= 4:
                    if is_system:
                        active_voice = "en-US-AriaNeural"
                    else:
                        active_voice = "en-US-GuyNeural" if row.get("gender") == "Male" else "en-US-JennyNeural"

                comm = edge_tts.Communicate(text, active_voice, pitch=pitch, rate=rate)
                await asyncio.wait_for(comm.save(raw_tts_file), timeout=chunk_timeout)

                # Metallic mecha DSP filter applied EXCLUSIVELY to System lines
                if is_system and os.path.exists(raw_tts_file) and os.path.getsize(raw_tts_file) > 100:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", raw_tts_file,
                        "-af", "aecho=0.8:0.4:12:0.25,treble=g=3:f=3500,equalizer=f=800:width_type=q:w=1.2:g=-2",
                        "-q:a", "2", "-acodec", "libmp3lame", out_file
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    try:
                        os.remove(raw_tts_file)
                    except OSError:
                        pass
                    return

                # Normal Narration and Dialogue write straight to out_file with zero filters
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

async def synthesize_chapter_task(ch_num: int, rows: list, title: str, build_dir: str, global_sem: asyncio.Semaphore):
    chapter_mp3 = os.path.join(build_dir, f"ch_{ch_num:03d}.mp3")
    chapter_meta = os.path.join(build_dir, f"ch_{ch_num:03d}_meta.json")
    if os.path.exists(chapter_mp3) and os.path.exists(chapter_meta):
        try:
            with open(chapter_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("duration", 0) > 5.0 and len(meta.get("relative_subtitles", [])) > 0:
                return ch_num, chapter_mp3, meta["duration"], meta["title"], meta["relative_subtitles"]
        except Exception:
            pass

    temp_dir = os.path.join(build_dir, f"temp_ch_{ch_num:03d}")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files, tasks = [], []
    for row in rows:
        c_path = os.path.join(temp_dir, f"seg_{row['line_id']}.mp3")
        chunk_files.append(c_path)
        tasks.append(synthesize_line_record(row, c_path, global_sem))

    await asyncio.gather(*tasks)

    valid_chunks = []
    rel_subtitles = []
    rel_time = 0.0
    for cf, row in zip(chunk_files, rows):
        if os.path.exists(cf) and os.path.getsize(cf) > 100:
            valid_chunks.append(cf)
            dur = get_audio_duration(cf)
            raw_text = RE_PAUSE_TAGS.sub("", row.get("text", "")).strip()

            if raw_text and not row.get("pause_duration"):
                sub_text = f"[{row['speaker']}]: {raw_text}" if row.get("line_type") == "Dialogue" else raw_text
                rel_subtitles.append((rel_time, rel_time + dur, sub_text))

            rel_time += dur

    if not valid_chunks:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "3.0", "-q:a", "9", "-acodec", "libmp3lame", chapter_mp3
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        manifest_path = os.path.join(temp_dir, "manifest.txt")
        with open(manifest_path, "w", encoding="utf-8") as f:
            for cf in valid_chunks:
                f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest_path, "-c", "copy", chapter_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    final_dur = get_audio_duration(chapter_mp3)
    with open(chapter_meta, "w", encoding="utf-8") as f:
        json.dump({"title": title, "duration": final_dur, "relative_subtitles": rel_subtitles}, f)

    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    try: os.remove(os.path.join(temp_dir, "manifest.txt"))
    except OSError: pass
    try: os.rmdir(temp_dir)
    except OSError: pass

    print(f"[Synthesized Audio] {title} ({format_timestamp(final_dur)})", flush=True)
    return ch_num, chapter_mp3, final_dur, title, rel_subtitles

def master_final_audio(chapter_files: list, build_dir: str, final_audio_path: str):
    raw_master_audio = os.path.join(build_dir, "raw_master.mp3")
    master_manifest = os.path.join(build_dir, "master_list.txt")
    with open(master_manifest, "w", encoding="utf-8") as f:
        for cf in chapter_files:
            f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", master_manifest, "-c", "copy", raw_master_audio], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_master_audio,
        "-af", "highpass=f=85,equalizer=f=3200:t=q:w=1.5:g=2.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50,loudnorm=I=-14:TP=-1.5:LRA=7,apad=pad_dur=15",
        "-c:a", "libmp3lame", "-b:a", "192k", final_audio_path
    ], check=True)

def assemble_multi_image_video(blocks: list, block_durations: dict, build_dir: str, final_audio_path: str, output_video_path: str):
    print("\n[Multiplexer] Assembling Video Frames + Outro Card...", flush=True)
    video_segments = []
    for cfg in blocks:
        b_idx = cfg["index"]
        dur = block_durations.get(b_idx, 0.0)
        if dur <= 0.1:
            dur = 60.0

        cover_path = cfg["cover_file"]
        segment_video = os.path.join(build_dir, f"v_seg_block_{b_idx}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", f"{dur:.3f}",
            "-i", cover_path, "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", segment_video
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        video_segments.append(segment_video)

    outro_slate = os.path.join(build_dir, "outro_slate_card.jpg")
    outro_seg = os.path.join(build_dir, "v_seg_outro.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", "15.000",
        "-i", outro_slate, "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", outro_seg
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    video_segments.append(outro_seg)

    v_manifest = os.path.join(build_dir, "v_segments_list.txt")
    with open(v_manifest, "w", encoding="utf-8") as f:
        for vs in video_segments:
            f.write(f"file '{os.path.abspath(vs).replace(os.sep, '/')}'\n")

    full_video_track = os.path.join(build_dir, "full_video_track.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_manifest, "-c", "copy", full_video_track], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", full_video_track, "-i", final_audio_path, "-c", "copy", "-movflags", "+faststart", "-shortest", output_video_path], check=True)

    for vs in video_segments:
        try: os.remove(vs)
        except OSError: pass
    try: os.remove(v_manifest)
    except OSError: pass
    try: os.remove(full_video_track)
    except OSError: pass
