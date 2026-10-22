import os
import sys
import re
import math
import shutil
import random
import asyncio
import warnings
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Suppress PyTorch TorchScript warnings from VoiceFixer internals
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.jit")

import edge_tts

# =====================================================================
# SUBTITLE ENGINE DELEGATION (Maintains 100% Backwards Compatibility)
# =====================================================================
try:
    from subtitle_utils import build_srt_subtitles, generate_subtitles_bundle
except ImportError:
    def build_srt_subtitles(all_subtitles: list, output_srt_path: str) -> bool:
        return False
    def generate_subtitles_bundle(base_subtitles: list, build_dir: str, target_languages: list = None) -> dict:
        return {}

# =====================================================================
# OPTIONAL & PERFORMANCE LIBRARIES (Graceful Fallbacks)
# =====================================================================

try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from aiolimiter import AsyncLimiter
    TTS_BURST_LIMITER = AsyncLimiter(max_rate=8, time_period=1.0)
except ImportError:
    TTS_BURST_LIMITER = None

try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    import json as orjson
    ORJSON_AVAILABLE = False

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

try:
    import pedalboard
    from pedalboard import (
        Pedalboard,
        Compressor,
        HighpassFilter,
        Limiter,
        Gain,
        LowShelfFilter,
        PeakFilter,
        HighShelfFilter,
        load_plugin
    )
    from pedalboard.io import AudioFile
    PEDALBOARD_AVAILABLE = True
except Exception:
    PEDALBOARD_AVAILABLE = False

# VoiceFixer (Neural Bandwidth & Timbre Restoration)
try:
    from voicefixer import VoiceFixer
    VOICEFIXER_AVAILABLE = True
    _voicefixer_model = None
except ImportError:
    VOICEFIXER_AVAILABLE = False
    _voicefixer_model = None


# =====================================================================
# CONSTANTS & DIRECTORIES
# =====================================================================

RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')
RE_PAUSE_TAGS = re.compile(r'\[(?:pause|Pause)\s*[\w\s.]*\]|\((?:pause|Pause)\s*[\w\s.]*\)', re.I)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCAL_PLUGINS = os.path.join(_SCRIPT_DIR, "assets", "plugins")
_CWD_PLUGINS = os.path.join(os.getcwd(), "assets", "plugins")
PLUGINS_DIR = _LOCAL_PLUGINS if os.path.exists(_LOCAL_PLUGINS) else _CWD_PLUGINS


# =====================================================================
# DURATION PROBING & FORMATTING
# =====================================================================

def _probe_duration_sync(file_path: str) -> float:
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
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
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
        return float(res.stdout.strip())
    except Exception:
        return 0.5


async def get_audio_duration(file_path: str) -> float:
    return await asyncio.to_thread(_probe_duration_sync, file_path)


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_seconds_to_timestamp(seconds: float) -> str:
    return format_timestamp(seconds)


def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = min(int(round((seconds - int(seconds)) * 1000)), 999)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# =====================================================================
# TTS SYNTHESIS
# =====================================================================

async def synthesize_line_record(row: dict, out_file: str, sem: asyncio.Semaphore, max_retries: int = 5):
    if os.path.exists(out_file) and os.path.getsize(out_file) > 300:
        return

    pause_dur = row.get("pause_duration")
    raw_text = row.get("text", "").strip()
    text = RE_PAUSE_TAGS.sub("", raw_text).strip()

    if pause_dur or not text or not RE_ALPHANUM.search(text):
        dur = float(pause_dur) if pause_dur else 0.5
        await asyncio.to_thread(
            subprocess.run,
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", f"{dur:.2f}", "-q:a", "9", "-acodec", "libmp3lame", out_file
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return

    line_type = row.get("line_type", "Narration")
    is_system = (line_type == "System")

    if is_system:
        voice = "en-US-AriaNeural"
        pitch = "-2Hz"
        rate = "+0%"
    else:
        req_voice = row.get("voice", "en-US-GuyNeural")
        if req_voice in ["en-US-TonyNeural", "en-US-JasonNeural"]:
            req_voice = "en-US-ChristopherNeural"
        voice = req_voice
        pitch = row.get("pitch", "+0Hz")
        rate = row.get("rate", "+5%")

    chunk_timeout = max(30.0, 20.0 + (len(text.split()) * 0.40))
    raw_tts_file = out_file + ".raw.mp3" if is_system else out_file

    for attempt in range(1, max_retries + 1):
        try:
            active_voice = voice
            if attempt >= 4:
                if is_system:
                    active_voice = "en-US-AriaNeural"
                else:
                    active_voice = "en-US-GuyNeural" if row.get("gender") == "Male" else "en-US-JennyNeural"

            comm = edge_tts.Communicate(text, active_voice, pitch=pitch, rate=rate)

            async with sem:
                if TTS_BURST_LIMITER:
                    async with TTS_BURST_LIMITER:
                        await asyncio.wait_for(comm.save(raw_tts_file), timeout=chunk_timeout)
                else:
                    await asyncio.wait_for(comm.save(raw_tts_file), timeout=chunk_timeout)

            if is_system and os.path.exists(raw_tts_file) and os.path.getsize(raw_tts_file) > 300:
                await asyncio.to_thread(
                    subprocess.run,
                    [
                        "ffmpeg", "-y", "-i", raw_tts_file,
                        "-af", "aecho=0.8:0.4:12:0.25,treble=g=3:f=3500,equalizer=f=800:width_type=q:w=1.2:g=-2",
                        "-ar", "24000", "-ac", "1",
                        "-q:a", "2", "-acodec", "libmp3lame", out_file
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                if not (os.path.exists(out_file) and os.path.getsize(out_file) > 300):
                    shutil.copy2(raw_tts_file, out_file)

                try:
                    os.remove(raw_tts_file)
                except OSError:
                    pass
                return

            if os.path.exists(out_file) and os.path.getsize(out_file) > 300:
                return

        except Exception:
            pass

        if attempt == max_retries:
            await asyncio.to_thread(
                subprocess.run,
                [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", out_file
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return

        await asyncio.sleep((attempt * 1.0) + random.uniform(0.3, 0.8))


async def synthesize_chapter_task(ch_num: int, rows: list, title: str, build_dir: str, chapter_sem: asyncio.Semaphore):
    chapter_mp3 = os.path.join(build_dir, f"ch_{ch_num:03d}.mp3")
    chapter_meta = os.path.join(build_dir, f"ch_{ch_num:03d}_meta.json")

    if os.path.exists(chapter_mp3) and os.path.exists(chapter_meta) and os.path.getsize(chapter_mp3) > 10000:
        try:
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(chapter_meta, "rb") as f:
                    meta_raw = await f.read()
            else:
                with open(chapter_meta, "rb") as f:
                    meta_raw = f.read()

            meta = orjson.loads(meta_raw) if ORJSON_AVAILABLE else orjson.loads(meta_raw.decode("utf-8"))
            if meta.get("duration", 0) > 10.0 and len(meta.get("relative_subtitles", [])) > 0:
                return ch_num, chapter_mp3, meta["duration"], meta["title"], meta["relative_subtitles"]
        except Exception:
            pass

    temp_dir = os.path.join(build_dir, f"temp_ch_{ch_num:03d}")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files, tasks = [], []

    for row in rows:
        c_path = os.path.join(temp_dir, f"seg_{row['line_id']}.mp3")
        chunk_files.append(c_path)
        tasks.append(synthesize_line_record(row, c_path, chapter_sem))

    await asyncio.gather(*tasks)

    valid_chunks = []
    rel_subtitles = []
    rel_time = 0.0

    for cf, row in zip(chunk_files, rows):
        if os.path.exists(cf) and os.path.getsize(cf) > 300:
            valid_chunks.append(cf)
            dur = await get_audio_duration(cf)
            raw_text = RE_PAUSE_TAGS.sub("", row.get("text", "")).strip()

            if raw_text and not row.get("pause_duration"):
                sub_text = f"[{row['speaker']}]: {raw_text}" if row.get("line_type") == "Dialogue" else raw_text
                rel_subtitles.append((rel_time, rel_time + dur, sub_text))

            rel_time += dur

    if not valid_chunks:
        await asyncio.to_thread(
            subprocess.run,
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", "3.0", "-q:a", "9", "-acodec", "libmp3lame", chapter_mp3
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        manifest_path = os.path.join(temp_dir, "manifest.txt")
        with open(manifest_path, "w", encoding="utf-8") as f:
            for cf in valid_chunks:
                f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

        await asyncio.to_thread(
            subprocess.run,
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest_path, "-c", "copy", chapter_mp3],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    final_dur = await get_audio_duration(chapter_mp3)
    meta_payload = {"title": title, "duration": final_dur, "relative_subtitles": rel_subtitles}

    if AIOFILES_AVAILABLE:
        raw_meta = orjson.dumps(meta_payload, option=orjson.OPT_INDENT_2) if ORJSON_AVAILABLE else orjson.dumps(meta_payload, indent=2).encode("utf-8")
        async with aiofiles.open(chapter_meta, "wb") as f:
            await f.write(raw_meta)
    else:
        with open(chapter_meta, "wb") as f:
            raw_meta = orjson.dumps(meta_payload, option=orjson.OPT_INDENT_2) if ORJSON_AVAILABLE else orjson.dumps(meta_payload, indent=2).encode("utf-8")
            f.write(raw_meta)

    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"[Synthesized Audio] {title} ({format_timestamp(final_dur)})", flush=True)
    return ch_num, chapter_mp3, final_dur, title, rel_subtitles


synthesize_chapter_audio = synthesize_chapter_task


# =====================================================================
# NEURAL VOICE RESTORATION (VoiceFixer CPU Handler)
# =====================================================================

def enhance_audio_with_voicefixer(input_path: str, output_path: str, use_cuda: bool = False) -> bool:
    global _voicefixer_model
    if not VOICEFIXER_AVAILABLE:
        print("[VoiceFixer Notice] Package voicefixer not installed. Skipping.", flush=True)
        return False
    try:
        if _voicefixer_model is None:
            print("[VoiceFixer] Initializing neural model weights...", flush=True)
            _voicefixer_model = VoiceFixer()

        print(f"[VoiceFixer] Processing neural restoration on {'GPU' if use_cuda else 'CPU'}...", flush=True)
        _voicefixer_model.restore(input=input_path, output=output_path, cuda=use_cuda, mode=0)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 10000
    except Exception as e:
        print(f"[VoiceFixer Notice] Neural enhancement bypassed ({e}). Proceeding to VST3/DSP chain.", flush=True)
        return False


# =====================================================================
# STUDIO VST3 & PEDALBOARD MASTERING
# =====================================================================

def master_audio_with_pedalboard(input_path: str, output_path: str) -> bool:
    if not PEDALBOARD_AVAILABLE:
        return False
    try:
        chain = [HighpassFilter(cutoff_frequency_hz=85.0)]

        # 1. Surgical Dynamic EQ / De-Esser (TDR Nova)
        nova_vst = os.path.join(PLUGINS_DIR, "TDR Nova.vst3")
        if os.path.exists(nova_vst):
            try:
                chain.append(load_plugin(nova_vst))
                print("[Pedalboard DSP] [OK] Attached VST3: TDR Nova", flush=True)
            except Exception as e:
                print(f"[Pedalboard DSP] Could not mount TDR Nova ({e}), using native EQ fallback.", flush=True)
                chain.extend([
                    HighShelfFilter(cutoff_frequency_hz=6500.0, gain_db=-2.5),
                    PeakFilter(cutoff_frequency_hz=850.0, gain_db=-1.5, q=1.0)
                ])
        else:
            chain.extend([
                HighShelfFilter(cutoff_frequency_hz=6500.0, gain_db=-2.5),
                PeakFilter(cutoff_frequency_hz=850.0, gain_db=-1.5, q=1.0)
            ])

        # 2. Chest Resonance Warmth
        chain.append(LowShelfFilter(cutoff_frequency_hz=220.0, gain_db=1.8))

        # 3. Optical Vocal Leveler (Analog Obsession LALA)
        lala_vst = os.path.join(PLUGINS_DIR, "LALA.vst3")
        if os.path.exists(lala_vst):
            try:
                chain.append(load_plugin(lala_vst))
                print("[Pedalboard DSP] [OK] Attached VST3: LALA", flush=True)
            except Exception as e:
                print(f"[Pedalboard DSP] Could not mount LALA ({e}), using native compressor fallback.", flush=True)
                chain.append(Compressor(threshold_db=-19.0, ratio=2.2, attack_ms=25.0, release_ms=140.0))
        else:
            chain.append(Compressor(threshold_db=-19.0, ratio=2.2, attack_ms=25.0, release_ms=140.0))

        # 4. Level Boost & True-Peak Limiter Ceiling
        chain.extend([
            Gain(gain_db=1.2),
            Limiter(threshold_db=-1.0, release_ms=60.0)
        ])

        smoothing_board = Pedalboard(chain)

        print("[Pedalboard DSP] Streaming audio blocks through mastering chain...", flush=True)
        with AudioFile(input_path) as f:
            sr = f.samplerate
            num_channels = f.num_channels
            with AudioFile(output_path, "w", sr, num_channels) as o:
                chunk_size = sr * 30
                while f.tell() < f.frames:
                    chunk = f.read(chunk_size)
                    effected = smoothing_board(chunk, sr, reset=False)
                    o.write(effected)

        return os.path.exists(output_path) and os.path.getsize(output_path) > 10000
    except Exception as e:
        print(f"[Pedalboard Notice] Direct DSP processing bypassed ({e}). Using FFmpeg audio filters.", flush=True)
        return False


def master_final_audio(
    chapter_files: list,
    build_dir: str,
    final_audio_path: str,
    enable_voicefixer: bool = False
):
    raw_master_audio = os.path.join(build_dir, "raw_master.mp3")
    voicefixer_staged = os.path.join(build_dir, "voicefixer_master.wav")
    pedalboard_staged = os.path.join(build_dir, "pedalboard_master.wav")
    master_manifest = os.path.join(build_dir, "master_list.txt")

    try:
        print("\n[Audio Master Engine] Concatenating chapter audio files...", flush=True)
        with open(master_manifest, "w", encoding="utf-8") as f:
            for cf in chapter_files:
                f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", master_manifest, "-c", "copy", raw_master_audio],
            check=True
        )

        working_source = raw_master_audio

        if enable_voicefixer:
            print("[Audio Master Engine] VoiceFixer neural restoration enabled.", flush=True)
            if enhance_audio_with_voicefixer(raw_master_audio, voicefixer_staged, use_cuda=False):
                working_source = voicefixer_staged
        else:
            print("[Audio Master Engine] VoiceFixer bypassed (CPU-optimized run).", flush=True)

        pedalboard_ok = master_audio_with_pedalboard(working_source, pedalboard_staged)
        if pedalboard_ok:
            source_audio = pedalboard_staged
            audio_filter = "equalizer=f=3200:t=q:w=1.5:g=2.5,loudnorm=I=-14:TP=-1.5:LRA=7,apad=pad_dur=15"
        else:
            source_audio = working_source
            audio_filter = "highpass=f=85,equalizer=f=3200:t=q:w=1.5:g=2.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50,loudnorm=I=-14:TP=-1.5:LRA=7,apad=pad_dur=15"

        print("[Audio Master Engine] Applying EBU R128 loudness normalization (-14 LUFS)...", flush=True)
        subprocess.run([
            "ffmpeg", "-y", "-i", source_audio,
            "-af", audio_filter,
            "-c:a", "libmp3lame", "-b:a", "192k", final_audio_path
        ], check=True)
        print(f"[Audio Master Engine] [OK] Mastered audio written to {final_audio_path}", flush=True)

    finally:
        for tmp in [raw_master_audio, voicefixer_staged, pedalboard_staged, master_manifest]:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass


concatenate_and_master_audio = master_final_audio


# =====================================================================
# YOUTUBE METADATA HELPERS
# =====================================================================

async def write_youtube_timestamps_file(
    chapter_timings: List[Dict[str, Any]],
    output_path: str,
    header_text: str = "",
    footer_text: str = ""
) -> str:
    lines = []
    if header_text:
        lines.append(header_text.strip())

    for ch in chapter_timings:
        stamp = format_timestamp(ch["start_time"])
        lines.append(f"{stamp} - {ch['title']}")

    if footer_text:
        lines.append(footer_text.strip())

    full_content = "\n".join(lines) + "\n"

    if AIOFILES_AVAILABLE:
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(full_content)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_content)

    return full_content


async def write_upload_payload_file(
    output_path: str,
    title: str,
    description: str,
    tags: List[str],
    assets: Optional[Dict[str, str]] = None,
    privacy_status: str = "unlisted"
) -> None:
    payload = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "24",
            "defaultLanguage": "en-US"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    if assets:
        payload["assets"] = assets

    content = orjson.dumps(payload, option=orjson.OPT_INDENT_2) if ORJSON_AVAILABLE else orjson.dumps(payload, indent=2).encode("utf-8")
    if AIOFILES_AVAILABLE:
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(content)
    else:
        with open(output_path, "wb") as f:
            f.write(content)


# =====================================================================
# VIDEO MULTIPLEXING (Compatible with Single Path or Multilingual Dict)
# =====================================================================

def assemble_multi_image_video(
    blocks: list,
    block_durations: dict,
    build_dir: str,
    final_audio_path: str,
    output_video_path: str,
    subtitles_srt_path: Optional[Union[str, Dict[str, str]]] = None
):
    """
    Renders video block segments, appends the 15s outro slate card,
    and multiplexes master audio and subtitles using ISO 639-2 stream tags.
    Maintains 100% backward compatibility with single-string SRT paths.
    """
    print("\n[Multiplexer] Assembling Video Frames + Outro Card...", flush=True)
    video_segments = []

    for cfg in blocks:
        b_idx = cfg["index"]
        dur = block_durations.get(b_idx, 0.0)
        if dur <= 0.1:
            dur = 60.0

        cover_path = cfg.get("cover_file")
        if not cover_path or not os.path.exists(cover_path):
            r_start, r_end = cfg.get("range", (0, 0))
            candidate = os.path.join(build_dir, f"cover_block_{r_start}_{r_end}.jpg")
            cover_path = candidate if os.path.exists(candidate) else cover_path

        segment_video = os.path.join(build_dir, f"v_seg_block_{b_idx}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", f"{dur:.3f}",
            "-i", cover_path,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-r", "1",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            segment_video
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        video_segments.append(segment_video)

    outro_slate = os.path.join(build_dir, "outro_slate_card.jpg")
    outro_seg = os.path.join(build_dir, "v_seg_outro.mp4")
    if os.path.exists(outro_slate):
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", "15.000",
            "-i", outro_slate,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-r", "1",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            outro_seg
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        video_segments.append(outro_seg)

    v_manifest = os.path.join(build_dir, "v_segments_list.txt")
    with open(v_manifest, "w", encoding="utf-8") as f:
        for vs in video_segments:
            f.write(f"file '{os.path.abspath(vs).replace(os.sep, '/')}'\n")

    full_video_track = os.path.join(build_dir, "full_video_track.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_manifest, "-c", "copy", full_video_track],
        check=True
    )

    mux_cmd = [
        "ffmpeg", "-y",
        "-i", full_video_track,
        "-i", final_audio_path
    ]

    # Convert single string path to dictionary format if passed by older scripts
    valid_subs: Dict[str, str] = {}
    if isinstance(subtitles_srt_path, str) and os.path.exists(subtitles_srt_path) and os.path.getsize(subtitles_srt_path) > 50:
        valid_subs["eng"] = subtitles_srt_path
    elif isinstance(subtitles_srt_path, dict):
        for lang_code, srt_p in subtitles_srt_path.items():
            if srt_p and os.path.exists(srt_p) and os.path.getsize(srt_p) > 50:
                valid_subs[lang_code] = srt_p

    # Attach all subtitle files as inputs
    for srt_path in valid_subs.values():
        mux_cmd.extend(["-i", srt_path])

    # Map video track 0 and audio track 1
    mux_cmd.extend(["-map", "0:v:0", "-map", "1:a:0"])

    # Map and tag subtitle streams
    if valid_subs:
        for idx, lang_code in enumerate(valid_subs.keys()):
            input_stream_idx = 2 + idx
            mux_cmd.extend([
                "-map", f"{input_stream_idx}:s:0",
                f"-metadata:s:s:{idx}", f"language={lang_code}",
                f"-metadata:s:s:{idx}", f"title={lang_code.upper()}"
            ])
        mux_cmd.extend(["-c:s", "mov_text"])

    mux_cmd.extend([
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-shortest",
        output_video_path
    ])

    subprocess.run(mux_cmd, check=True)

    for vs in video_segments:
        try:
            os.remove(vs)
        except OSError:
            pass
    for tmp in [v_manifest, full_video_track]:
        try:
            os.remove(tmp)
        except OSError:
            pass


render_final_audiobook_video = assemble_multi_image_video