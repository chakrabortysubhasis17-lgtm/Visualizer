import asyncio
import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import warnings
import weakref
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
# ACOUSTIC MASTERING CONSTANTS (BROADCAST VOCAL POLISHING)
# =====================================================================

# Studio vocal mastering filter chain:
# 1. highpass=f=80: Eliminates artificial digital rumble/plosives below 80 Hz.
# 2. equalizer (250 Hz, +1.8dB): Restores vocal body and natural chest resonance.
# 3. equalizer (6500 Hz, -2.5dB): Tames brittle digital sibilance ('s', 'sh', 't' artifacts).
# 4. acompressor: Tames dynamic spikes between shouts and murmurs with transparent release.
# 5. aecho: Applies a 5% subtle room dimension to remove dead-air sterility.
# 6. loudnorm: Conforms to YouTube/broadcast loudness standard (-14 LUFS, flat dynamic curve).
BROADCAST_VOCAL_FILTER = (
    "highpass=f=80,"
    "equalizer=f=250:width_type=h:width=120:g=1.8,"
    "equalizer=f=6500:width_type=h:width=1400:g=-2.5,"
    "acompressor=threshold=-18dB:ratio=3:attack=5:release=100:makeup=2dB,"
    "aecho=0.8:0.88:20|40:0.05|0.02,"
    "loudnorm=I=-14:LRA=7:TP=-1.5"
)

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
# SFX ADDITIONS (separate from TTS throttling and semaphore)
# =====================================================================

SFX_PIPELINE_VERSION = 2
SFX_MAX_CONCURRENT_FFMPEG = 2

# Complete 53-Key Master SFX Taxonomy
# Master SFX Taxonomy (including new targeted movement, ambient & action keys)
SFX_KEYS = frozenset({
    # Physical movement & transport
    "footsteps", "run", "tiptoe", "horseandcart", "steps_indoor", "patter", "heavy_steps", "car", "screech",
    # Environmental & atmosphere
    "creak", "crackle", "thunder", "drip", "wind", "forest", "ocean", "crickets", "rain", "clock",
    # Magic, portals & energy
    "hum", "whoosh", "teleport",
    # Combat, martial & bodily impact
    "impact", "thud", "blade", "armor", "slash", "monster", "wardrum", "pain", "gunshot", "explosion", "snarl",
    # LitRPG, item & system events
    "chime", "levelup", "interface", "swish", "quest", "alert",
    "achievement", "reward", "loot", "coin", "chest", "equip",
    # Character reactions, physical interactions & everyday actions
    "heartbeat", "gasp", "knock", "rustle", "splash", "squeak", "sigh", "slam", "glass_break", "paper",
    # Social, culinary & crowd dynamics
    "market", "cheer", "disappointed", "dishes", "eating", "cooking",
    # Romance & intimacy
    "heartwarm", "intimate",
    # Supernatural, occult & sacred
    "whisper", "haunt", "howl", "bells", "gong", "intro", "crow"
})

SFX_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac", ".opus")

_SFX_COPY_LOCK = threading.Lock()
_SFX_COPIED_BUILDS = {}
_SFX_SEMAPHORES = weakref.WeakKeyDictionary()

# =====================================================================
# BGM ADDITIONS (Low Volume Ambient Scene Mood Beds)
# =====================================================================

BGM_MOODS = frozenset({"combat", "tension", "sorrow", "wonder", "warmth", "no_mood"})
BGM_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac", ".opus")
_BGM_COPY_LOCK = threading.Lock()
_BGM_COPIED_BUILDS = {}


def normalize_bgm_mood(value: Any) -> str:
    """Return an allowed lowercase BGM mood key, strictly defaulting to 'no_mood'."""
    if not isinstance(value, str):
        return "no_mood"
    key = value.strip().lower()
    return key if key in BGM_MOODS else "no_mood"


def prepare_bgm_assets(build_dir: str) -> str:
    """Synchronize recognized BGM loop tracks from root assets/bgm into build_dir/bgm."""
    build_root = os.path.abspath(build_dir)
    source_dir = os.path.join(_SCRIPT_DIR, "assets", "bgm")
    target_dir = os.path.join(build_root, "bgm")

    with _BGM_COPY_LOCK:
        os.makedirs(target_dir, exist_ok=True)
        if not os.path.isdir(source_dir):
            return target_dir

        try:
            for filename in os.listdir(source_dir):
                stem, extension = os.path.splitext(filename)
                if normalize_bgm_mood(stem) == "no_mood" or extension.lower() not in BGM_EXTENSIONS:
                    continue
                src = os.path.join(source_dir, filename)
                dst = os.path.join(target_dir, filename)
                if os.path.exists(dst):
                    try:
                        if os.path.getsize(src) == os.path.getsize(dst):
                            continue
                    except OSError:
                        pass
                try:
                    shutil.copy2(src, dst)
                except OSError:
                    pass
        except OSError:
            pass

    return target_dir


def find_bgm_file(bgm_dir: str, mood_key: str) -> Optional[str]:
    """Find an audio loop file matching the requested mood in the bgm directory."""
    mood = normalize_bgm_mood(mood_key)
    if mood == "no_mood" or not os.path.isdir(bgm_dir):
        return None

    try:
        filenames = os.listdir(bgm_dir)
    except OSError:
        return None

    for ext in BGM_EXTENSIONS:
        target = f"{mood}{ext}"
        candidate = os.path.join(bgm_dir, target)
        if os.path.isfile(candidate) and os.path.getsize(candidate) > 1000:
            return candidate

    return None


def mix_chapter_bgm_bed(
    chapter_audio_path: str,
    rows: list,
    line_durations: list,
    bgm_dir: str,
    output_path: str
) -> bool:
    """Mix low-volume ambient BGM beds into the chapter audio based on tagged mood spans."""
    if not os.path.isfile(chapter_audio_path) or not rows or not line_durations:
        return False

    intervals = []
    current_mood = "no_mood"
    interval_start = 0.0
    accumulated_time = 0.0

    for row, dur in zip(rows, line_durations):
        mood = normalize_bgm_mood(row.get("bgm_mood", "no_mood"))
        if mood != current_mood:
            if current_mood != "no_mood":
                intervals.append((current_mood, interval_start, accumulated_time))
            current_mood = mood
            interval_start = accumulated_time
        accumulated_time += dur

    if current_mood != "no_mood":
        intervals.append((current_mood, interval_start, accumulated_time))

    # Filter for intervals that are long enough (>= 8.0s) and have matching audio files in bgm folder
    valid_intervals = []
    for mood, start, end in intervals:
        dur = end - start
        if dur >= 8.0:
            bgm_file = find_bgm_file(bgm_dir, mood)
            if bgm_file:
                valid_intervals.append((bgm_file, start, end, dur))

    if not valid_intervals:
        return False

    # Build FFmpeg filter graph to overlay ambient music beds at an ultra-low volume (-27 dB)
    inputs = ["-i", chapter_audio_path]
    filter_complex_parts = []
    mix_inputs = ["[0:a]"]

    for idx, (bgm_file, start, end, dur) in enumerate(valid_intervals, start=1):
        inputs.extend(["-i", bgm_file])
        fade_in = min(2.5, dur * 0.25)
        fade_out = min(3.0, dur * 0.25)
        out_start = max(0.0, dur - fade_out)

        # Loop, trim, fade-in/out, clear vocal mids (dip at 2.5kHz), and set volume to -27dB (~0.044 gain)
        filt = (
            f"[{idx}:a]aloop=loop=-1:size=2e+09,"
            f"atrim=0:{dur:.3f},"
            f"afade=t=in:ss=0:d={fade_in:.2f},"
            f"afade=t=out:st={out_start:.2f}:d={fade_out:.2f},"
            f"equalizer=f=2500:t=q:w=1.0:g=-4.0,"
            f"volume=0.044,"
            f"adelay={int(start * 1000)}|{int(start * 1000)}[bgm_{idx}]"
        )
        filter_complex_parts.append(filt)
        mix_inputs.append(f"[bgm_{idx}]")

    num_streams = len(mix_inputs)
    filter_complex_parts.append(
        f"{''.join(mix_inputs)}amix=inputs={num_streams}:duration=first:dropout_transition=2:weights=1.0 {'1.0 ' * (num_streams - 1)}[outa]"
    )

    temp_mixed = output_path + ".bgm_tmp.mp3"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", ";".join(filter_complex_parts),
        "-map", "[outa]",
        "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        temp_mixed
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True)
        if os.path.isfile(temp_mixed) and os.path.getsize(temp_mixed) > 300:
            os.replace(temp_mixed, output_path)
            return True
    except Exception as exc:
        print(f"[BGM Notice] BGM mixing bypassed ({exc}). Retaining dry narration.", flush=True)
    finally:
        if os.path.exists(temp_mixed):
            try:
                os.remove(temp_mixed)
            except OSError:
                pass

    return False


def normalize_sfx_key(value: Any) -> str:
    """Return an allowed lowercase SFX key, or an empty string."""
    if not isinstance(value, str):
        return ""
    key = value.strip().lower()
    return key if key in SFX_KEYS else ""


def _get_sfx_semaphore() -> asyncio.Semaphore:
    """Get a dedicated SFX FFmpeg semaphore for the running event loop."""
    loop = asyncio.get_running_loop()
    semaphore = _SFX_SEMAPHORES.get(loop)
    if semaphore is None:
        semaphore = asyncio.Semaphore(SFX_MAX_CONCURRENT_FFMPEG)
        _SFX_SEMAPHORES[loop] = semaphore
    return semaphore


def _sfx_asset_snapshot(directory: str) -> tuple:
    """Describe recognized SFX files in a flat directory, including change markers."""
    if not os.path.isdir(directory):
        return ()

    items = []
    try:
        filenames = os.listdir(directory)
    except OSError:
        return ()

    for filename in filenames:
        stem, extension = os.path.splitext(filename)
        if normalize_sfx_key(stem) not in SFX_KEYS or extension.lower() not in SFX_EXTENSIONS:
            continue
        path = os.path.join(directory, filename)
        try:
            if not os.path.isfile(path):
                continue
            stat = os.stat(path)
            if stat.st_size <= 0:
                continue
            items.append((filename, stat.st_size, stat.st_mtime_ns))
        except OSError:
            continue
    return tuple(sorted(items))


def prepare_sfx_assets(build_dir: str) -> str:
    """Synchronize recognized SFX files into build_dir/sfx without stale assets.

    Multi-process safe for concurrent PowerShell runner instances:
    - Skips overwriting files if the destination already exists with matching size.
    - Gracefully handles Windows PermissionError [WinError 32] when another thread
      or runner has an active read lock via FFmpeg.
    """
    build_root = os.path.abspath(build_dir)
    source_dir = os.path.join(_SCRIPT_DIR, "assets", "sfx")
    target_dir = os.path.join(build_root, "sfx")

    with _SFX_COPY_LOCK:
        os.makedirs(target_dir, exist_ok=True)
        source_exists = os.path.isdir(source_dir)
        source_snapshot = _sfx_asset_snapshot(source_dir) if source_exists else ()
        target_snapshot = _sfx_asset_snapshot(target_dir)
        target_sizes = tuple((item[0], item[1]) for item in target_snapshot)
        source_sizes = tuple((item[0], item[1]) for item in source_snapshot)

        # Fast path across runs or separate process instances when already in sync
        if (
            source_exists
            and target_sizes == source_sizes
            and len(source_sizes) > 0
        ):
            _SFX_COPIED_BUILDS[build_root] = source_snapshot
            return target_dir

        if (
            _SFX_COPIED_BUILDS.get(build_root) == source_snapshot
            and target_sizes == source_sizes
        ):
            return target_dir

        source_names = {item[0] for item in source_snapshot}
        copy_failed = False

        # Remove recognized assets that no longer exist in the source
        for filename, _, _ in target_snapshot:
            if filename not in source_names:
                try:
                    os.remove(os.path.join(target_dir, filename))
                except PermissionError:
                    pass
                except OSError as exc:
                    copy_failed = True
                    print(f"[SFX Notice] Could not remove stale asset '{filename}': {exc}", flush=True)

        if source_exists:
            for filename, _, _ in source_snapshot:
                src = os.path.join(source_dir, filename)
                dst = os.path.join(target_dir, filename)
                try:
                    # Skip copying if destination already exists with matching size (multi-process safe)
                    if os.path.exists(dst):
                        try:
                            if os.path.getsize(src) == os.path.getsize(dst):
                                continue
                        except OSError:
                            pass

                    shutil.copy2(src, dst)
                except PermissionError:
                    # Destination is actively open/locked by FFmpeg in another thread or runner.
                    # If it already exists and has size > 0, it is valid and ready to use.
                    if not (os.path.exists(dst) and os.path.getsize(dst) > 0):
                        copy_failed = True
                except OSError as exc:
                    copy_failed = True
                    print(f"[SFX Notice] Could not copy SFX asset '{filename}': {exc}", flush=True)
        elif not _SFX_COPIED_BUILDS.get(build_root) == ():
            print(f"[SFX Notice] SFX source folder not found: {source_dir}; SFX will be skipped.", flush=True)

        final_snapshot = _sfx_asset_snapshot(target_dir)
        final_sizes = tuple((item[0], item[1]) for item in final_snapshot)
        if not copy_failed and final_sizes == source_sizes:
            _SFX_COPIED_BUILDS[build_root] = source_snapshot
        else:
            _SFX_COPIED_BUILDS.pop(build_root, None)

    return target_dir


def find_sfx_file(sfx_dir: str, sfx_key: str) -> Optional[str]:
    """Find an audio file whose filename stem exactly matches an allowed SFX key."""
    key = normalize_sfx_key(sfx_key)
    if not key or not os.path.isdir(sfx_dir):
        return None

    try:
        filenames = os.listdir(sfx_dir)
    except OSError:
        return None

    candidates = []
    for filename in filenames:
        stem, extension = os.path.splitext(filename)
        extension = extension.lower()
        if stem.lower() != key or extension not in SFX_EXTENSIONS:
            continue
        path = os.path.join(sfx_dir, filename)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            candidates.append((SFX_EXTENSIONS.index(extension), path))

    candidates.sort(key=lambda item: item[0])
    return candidates[0][1] if candidates else None


def _sfx_asset_identity(path: Optional[str]) -> Optional[dict]:
    """Return a stable identity for an SFX file, or None when it is unavailable."""
    if not path:
        return None
    try:
        stat = os.stat(path)
        if not os.path.isfile(path) or stat.st_size <= 0:
            return None
        return {
            "filename": os.path.basename(path),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
    except OSError:
        return None


def _sfx_manifest_signature(rows: list, sfx_dir: str) -> str:
    """Fingerprint row-to-SFX assignments and the assets available for them."""
    manifest = []
    for row in rows:
        key = normalize_sfx_key(row.get("sfx", ""))
        if not key:
            continue
        path = find_sfx_file(sfx_dir, key)
        if path:
            try:
                stat = os.stat(path)
                asset = (os.path.basename(path), stat.st_size, stat.st_mtime_ns)
            except OSError:
                asset = (os.path.basename(path), None, None)
        else:
            asset = (key, None, None)
        manifest.append((str(row.get("line_id", "")), key, asset))

    raw = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sfx_metadata_path(segment_path: str) -> str:
    return segment_path + ".sfxmeta.json"


def _sfx_speech_path(segment_path: str) -> str:
    return segment_path + ".speech.mp3"


def _read_sfx_metadata(segment_path: str) -> Optional[dict]:
    path = _sfx_metadata_path(segment_path)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _write_sfx_metadata(
    segment_path: str,
    sfx_key: str,
    sfx_applied: bool,
    asset_signature: Optional[dict] = None,
) -> None:
    path = _sfx_metadata_path(segment_path)
    temp_path = path + ".tmp"
    payload = {
        "sfx_pipeline_version": SFX_PIPELINE_VERSION,
        "sfx": normalize_sfx_key(sfx_key),
        "sfx_applied": bool(sfx_applied),
        "sfx_asset_signature": asset_signature,
    }
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
    except OSError as exc:
        print(f"[SFX Notice] Could not write metadata for {os.path.basename(segment_path)}: {exc}", flush=True)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _atomic_copy_audio(source_path: str, target_path: str) -> None:
    temp_path = target_path + ".copy_tmp.mp3"
    try:
        shutil.copyfile(source_path, temp_path)
        os.replace(temp_path, target_path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _prepend_sfx_audio_sync(sfx_path: str, speech_path: str, output_path: str) -> None:
    """Create a new segment with the SFX first and the original speech second."""
    temp_output = output_path + ".sfx_tmp.mp3"
    filter_complex = (
        "[0:a:0]aresample=24000,"
        "aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[sfx];"
        "[1:a:0]aresample=24000,"
        "aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[speech];"
        "[sfx][speech]concat=n=2:v=0:a=1[out]"
    )
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", sfx_path,
        "-i", speech_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        temp_output,
    ]
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if not os.path.isfile(temp_output) or os.path.getsize(temp_output) <= 300:
            raise RuntimeError("FFmpeg did not produce a valid SFX-prefixed segment.")
        os.replace(temp_output, output_path)
    finally:
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except OSError:
                pass


async def ensure_segment_sfx(row: dict, segment_path: str, sfx_dir: str) -> None:
    """Apply the row's SFX once, rebuilding from the preserved speech copy when needed."""
    if not os.path.isfile(segment_path) or os.path.getsize(segment_path) <= 300:
        return

    sfx_key = normalize_sfx_key(row.get("sfx", ""))
    sfx_path = find_sfx_file(sfx_dir, sfx_key) if sfx_key else None
    asset_signature = _sfx_asset_identity(sfx_path)
    speech_path = _sfx_speech_path(segment_path)
    metadata = _read_sfx_metadata(segment_path)
    speech_exists = os.path.isfile(speech_path) and os.path.getsize(speech_path) > 300

    if not speech_exists:
        if metadata and metadata.get("sfx_applied"):
            print(
                f"[SFX Warning] Original speech copy missing for {os.path.basename(segment_path)}; "
                "skipping SFX changes to avoid duplication.",
                flush=True,
            )
            return
        if not sfx_key:
            _write_sfx_metadata(segment_path, "", False, None)
            return
        try:
            await asyncio.to_thread(shutil.copy2, segment_path, speech_path)
            speech_exists = True
        except OSError as exc:
            print(f"[SFX Warning] Could not preserve speech segment: {exc}", flush=True)
            return

    metadata_matches_current_asset = bool(
        metadata
        and metadata.get("sfx_pipeline_version") == SFX_PIPELINE_VERSION
        and metadata.get("sfx") == sfx_key
        and metadata.get("sfx_asset_signature") == asset_signature
    )
    expected_applied = bool(sfx_key and sfx_path)

    if (
        metadata_matches_current_asset
        and bool(metadata.get("sfx_applied")) == expected_applied
    ):
        return

    if not sfx_key:
        if metadata and metadata.get("sfx_applied") and speech_exists:
            try:
                await asyncio.to_thread(_atomic_copy_audio, speech_path, segment_path)
            except OSError as exc:
                print(f"[SFX Warning] Could not restore original speech segment: {exc}", flush=True)
                return
        _write_sfx_metadata(segment_path, "", False, None)
        return

    if not sfx_path:
        if metadata and metadata.get("sfx_applied") and speech_exists:
            try:
                await asyncio.to_thread(_atomic_copy_audio, speech_path, segment_path)
            except OSError as exc:
                print(f"[SFX Warning] Could not remove stale SFX from segment: {exc}", flush=True)
                return
        _write_sfx_metadata(segment_path, sfx_key, False, None)
        print(f"[SFX Notice] Asset '{sfx_key}' not found; speech remains unchanged.", flush=True)
        return

    try:
        async with _get_sfx_semaphore():
            await asyncio.to_thread(
                _prepend_sfx_audio_sync,
                sfx_path,
                speech_path,
                segment_path,
            )
        _write_sfx_metadata(segment_path, sfx_key, True, asset_signature)
    except Exception as exc:
        try:
            await asyncio.to_thread(_atomic_copy_audio, speech_path, segment_path)
        except Exception:
            pass
        _write_sfx_metadata(segment_path, sfx_key, False, asset_signature)
        print(
            f"[SFX Warning] Failed to prepend '{sfx_key}' to "
            f"{os.path.basename(segment_path)}: {exc}",
            flush=True,
        )


# =====================================================================
# SYSTEM TOOL CHECKS
# =====================================================================

def verify_ffmpeg_installation() -> bool:
    """Verifies whether ffmpeg and ffprobe are available in the system PATH."""
    return (
        shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
    )

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


def get_media_duration(file_path: str) -> float:
    """Synchronous media duration probe using ffprobe with graceful fallback."""
    return _probe_duration_sync(file_path)


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
# SILENCE & MICRO-PAUSE GENERATION
# =====================================================================

def generate_silence_segment(output_path: str, duration: float = 0.3) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    duration = max(0.05, float(duration))

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", f"{duration:.3f}",
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        output_path,
    ]
    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return output_path

# =====================================================================
# TTS SYNTHESIS
# =====================================================================

async def synthesize_line_record(
    row: dict,
    out_file: str,
    sem: asyncio.Semaphore,
    max_retries: int = 5,
    sfx_dir: Optional[str] = None,
):
    if sfx_dir is None:
        sfx_dir = os.path.join(_SCRIPT_DIR, "assets", "sfx")

    if os.path.exists(out_file) and os.path.getsize(out_file) > 300:
        await ensure_segment_sfx(row, out_file, sfx_dir)
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
        await ensure_segment_sfx(row, out_file, sfx_dir)
        return

    line_type = row.get("line_type", "Narration")
    is_system = (line_type == "System")
    is_narration = (line_type == "Narration" or row.get("speaker", "").lower() == "narrator")

    if is_system:
        voice = "en-US-AriaNeural"
        pitch = "-2Hz"
        rate = "+0%"
    elif is_narration:
        voice = "en-US-ChristopherNeural"
        pitch = row.get("pitch", "-2Hz")
        rate = row.get("rate", "+0%")
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
                elif is_narration:
                    active_voice = "en-US-ChristopherNeural"
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
                await ensure_segment_sfx(row, out_file, sfx_dir)
                return

            if os.path.exists(out_file) and os.path.getsize(out_file) > 300:
                await ensure_segment_sfx(row, out_file, sfx_dir)
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
            await ensure_segment_sfx(row, out_file, sfx_dir)
            return

        await asyncio.sleep((attempt * 1.0) + random.uniform(0.3, 0.8))


async def synthesize_chapter_task(ch_num: int, rows: list, title: str, build_dir: str, chapter_sem: asyncio.Semaphore):
    chapter_mp3 = os.path.join(build_dir, f"ch_{ch_num:03d}.mp3")
    chapter_meta = os.path.join(build_dir, f"ch_{ch_num:03d}_meta.json")

    sfx_dir = await asyncio.to_thread(prepare_sfx_assets, build_dir)
    bgm_dir = await asyncio.to_thread(prepare_bgm_assets, build_dir)

    has_requested_sfx = any(normalize_sfx_key(row.get("sfx", "")) for row in rows)
    sfx_manifest_signature = _sfx_manifest_signature(rows, sfx_dir)

    if os.path.exists(chapter_mp3) and os.path.exists(chapter_meta) and os.path.getsize(chapter_mp3) > 10000:
        try:
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(chapter_meta, "rb") as f:
                    meta_raw = await f.read()
            else:
                with open(chapter_meta, "rb") as f:
                    meta_raw = f.read()

            meta = orjson.loads(meta_raw) if ORJSON_AVAILABLE else orjson.loads(meta_raw.decode("utf-8"))
            has_stored_sfx_metadata = (
                "sfx_pipeline_version" in meta or "sfx_manifest_signature" in meta
            )
            if not has_requested_sfx and not has_stored_sfx_metadata:
                sfx_cache_valid = True
            else:
                sfx_cache_valid = (
                    meta.get("sfx_pipeline_version") == SFX_PIPELINE_VERSION
                    and meta.get("sfx_manifest_signature") == sfx_manifest_signature
                )
            if (
                sfx_cache_valid
                and meta.get("duration", 0) > 10.0
                and len(meta.get("relative_subtitles", [])) > 0
            ):
                return ch_num, chapter_mp3, meta["duration"], meta["title"], meta["relative_subtitles"]
        except Exception:
            pass

    temp_dir = os.path.join(build_dir, f"temp_ch_{ch_num:03d}")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files, tasks = [], []

    for row in rows:
        c_path = os.path.join(temp_dir, f"seg_{row['line_id']}.mp3")
        chunk_files.append(c_path)
        tasks.append(
            synthesize_line_record(
                row,
                c_path,
                chapter_sem,
                sfx_dir=sfx_dir,
            )
        )

    await asyncio.gather(*tasks)

    valid_chunks = []
    rel_subtitles = []
    line_durations = []
    rel_time = 0.0
    sfx_duration_cache = {}

    for cf, row in zip(chunk_files, rows):
        if os.path.exists(cf) and os.path.getsize(cf) > 300:
            valid_chunks.append(cf)
            dur = await get_audio_duration(cf)
            line_durations.append(dur)
            raw_text = RE_PAUSE_TAGS.sub("", row.get("text", "")).strip()

            sfx_offset = 0.0
            segment_meta = _read_sfx_metadata(cf)
            if segment_meta and segment_meta.get("sfx_applied"):
                applied_key = normalize_sfx_key(segment_meta.get("sfx", ""))
                if applied_key:
                    if applied_key not in sfx_duration_cache:
                        applied_path = find_sfx_file(sfx_dir, applied_key)
                        sfx_duration_cache[applied_key] = (
                            await get_audio_duration(applied_path) if applied_path else 0.0
                        )
                    sfx_offset = min(sfx_duration_cache.get(applied_key, 0.0), dur)

            if raw_text and not row.get("pause_duration"):
                sub_text = f"[{row['speaker']}]: {raw_text}" if row.get("line_type") == "Dialogue" else raw_text
                subtitle_start = rel_time + sfx_offset
                subtitle_end = rel_time + dur
                if subtitle_start < subtitle_end:
                    rel_subtitles.append((subtitle_start, subtitle_end, sub_text))

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

        # Mix low-volume ambient BGM bed if mood tracks exist in assets/bgm
        await asyncio.to_thread(
            mix_chapter_bgm_bed,
            chapter_mp3,
            rows,
            line_durations,
            bgm_dir,
            chapter_mp3
        )

    final_dur = await get_audio_duration(chapter_mp3)
    meta_payload = {
        "title": title,
        "duration": final_dur,
        "relative_subtitles": rel_subtitles,
        "sfx_pipeline_version": SFX_PIPELINE_VERSION,
        "sfx_manifest_signature": sfx_manifest_signature,
    }

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
# AUDIO CONCATENATION & MASTERING
# =====================================================================

def concat_audio_files(
    input_list_file: str,
    output_path: str,
    apply_mastering: bool = True,
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", input_list_file,
    ]

    if apply_mastering:
        cmd.extend([
            "-af", BROADCAST_VOCAL_FILTER,
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            "-ar", "44100",
        ])
    else:
        cmd.extend([
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            "-ar", "44100",
        ])

    cmd.append(output_path)

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return output_path

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
            audio_filter = "volume=1.5dB,equalizer=f=3200:t=q:w=1.5:g=2.0,loudnorm=I=-14:TP=-1.5:LRA=7,apad=pad_dur=15"
        else:
            source_audio = working_source
            audio_filter = f"{BROADCAST_VOCAL_FILTER},apad=pad_dur=15"

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
# DYNAMIC ARC IMAGE RENDERING & KEN BURNS ZOOM
# =====================================================================

def create_thematic_visual_segment(
    image_path: str,
    duration: float,
    output_path: str,
    resolution: Tuple[int, int] = (1920, 1080),
    fps: int = 30,
    enable_slow_zoom: bool = True,
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    width, height = resolution
    total_frames = int(duration * fps)

    if enable_slow_zoom:
        vf_filter = (
            f"scale=8000:-1,"
            f"zoompan=z='min(zoom+0.00012,1.08)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps},"
            f"format=yuv420p"
        )
    else:
        vf_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", vf_filter,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return output_path

# =====================================================================
# OUTRO SLATE & BRANDING OVERLAY
# =====================================================================

def overlay_channel_branding(
    video_input: str,
    output_path: str,
    logo_path: Optional[str] = None,
    subscribe_path: Optional[str] = None,
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    inputs = ["-i", video_input]
    filter_parts = []
    current_layer = "[0:v]"
    layer_idx = 1

    if logo_path and os.path.exists(logo_path):
        inputs.extend(["-i", logo_path])
        filter_parts.append(
            f"{current_layer}[{layer_idx}:v]overlay=W-w-30:30[branded1]"
        )
        current_layer = "[branded1]"
        layer_idx += 1

    if subscribe_path and os.path.exists(subscribe_path):
        inputs.extend(["-i", subscribe_path])
        filter_parts.append(
            f"{current_layer}[{layer_idx}:v]overlay=W-w-30:H-h-30[branded2]"
        )
        current_layer = "[branded2]"
        layer_idx += 1

    if not filter_parts:
        shutil.copyfile(video_input, output_path)
        return output_path

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", current_layer,
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "copy",
        output_path,
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return output_path

# =====================================================================
# VIDEO & AUDIO COMBINATION WITH AMBIENT NOISE FLOOR
# =====================================================================

def merge_audio_video_with_ambience(
    video_input: str,
    audio_input: str,
    output_path: str,
    ambience_db: float = -50.0,
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    amp = round(10 ** (ambience_db / 20.0), 5)

    filter_complex = (
        "[1:a]asplit=2[main_a][ref_a];"
        f"anoisesrc=d=100000:c=pink:r=44100:a={amp}[ambience];"
        f"[ambience][ref_a]amix=inputs=2:duration=first:weights=1 0[room_tone];"
        "[main_a][room_tone]amix=inputs=2:duration=first:dropout_transition=2[final_a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_input,
        "-i", audio_input,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[final_a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-shortest",
        output_path,
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return output_path

# =====================================================================
# SUBTITLE HARMONIZATION (SRT TO ASS/BURN-IN & SOFT MUXING)
# =====================================================================

def embed_soft_subtitles(
    video_input: str,
    subtitles_dict: Dict[str, str],
    output_path: str,
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cmd = ["ffmpeg", "-y", "-i", video_input]
    map_cmds = ["-map", "0:v", "-map", "0:a"]
    metadata_cmds = []

    sub_idx = 0
    for lang_code, srt_path in subtitles_dict.items():
        if os.path.exists(srt_path):
            cmd.extend(["-i", srt_path])
            map_cmds.extend(["-map", f"{sub_idx + 1}:s"])
            metadata_cmds.extend([
                f"-metadata:s:s:{sub_idx}", f"language={lang_code}",
                f"-metadata:s:s:{sub_idx}", f"title={lang_code.upper()}",
            ])
            sub_idx += 1

    cmd.extend(map_cmds)
    cmd.extend(metadata_cmds)
    cmd.extend([
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "mov_text",
        output_path,
    ])

    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return output_path

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

    valid_subs: Dict[str, str] = {}
    if isinstance(subtitles_srt_path, str) and os.path.exists(subtitles_srt_path) and os.path.getsize(subtitles_srt_path) > 50:
        valid_subs["eng"] = subtitles_srt_path
    elif isinstance(subtitles_srt_path, dict):
        for lang_code, srt_p in subtitles_srt_path.items():
            if srt_p and os.path.exists(srt_p) and os.path.getsize(srt_p) > 50:
                valid_subs[lang_code] = srt_p

    for srt_path in valid_subs.values():
        mux_cmd.extend(["-i", srt_path])

    mux_cmd.extend(["-map", "0:v:0", "-map", "1:a:0"])

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