try:
    import cv2
    import numpy as np
    CV2_NUMPY_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_NUMPY_AVAILABLE = False
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

from audio_constants import (
    SFX_PIPELINE_VERSION,
    SFX_MAX_CONCURRENT_FFMPEG,
    BROADCAST_VOCAL_FILTER,
    VOICE_PITCH_PROFILES,
    BGM_MOODS,
    BGM_MOOD_PITCH_DELTAS_BY_VOICE,
    BGM_MOOD_RATE_DELTAS_BY_VOICE,
    SPEAKER_PITCH_OFFSETS,
    SFX_EXTENSIONS,
    BGM_EXTENSIONS,
    SFX_KEYS,
    SFX_SYNONYMS,
)
from lexicon_utils import apply_pronunciation_lexicon

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


def calculate_rate_velocity_pitch_offset(rate_str: str) -> float:
    """Computes micro-pitch shift driven by speech velocity (+10% rate -> +0.3Hz, -10% -> -0.3Hz)."""
    try:
        match = re.search(r'([+-]?\d+)', str(rate_str))
        if match:
            rate_val = int(match.group(1))
            # 0.03 Hz shift per 1% rate deviation from baseline
            return round(rate_val * 0.03, 2)
    except Exception:
        pass
    return 0.0


def calculate_speaker_pitch_offset(speaker_name: str) -> float:
    """Assigns deterministic micro-pitch offsets for distinct roles sharing identical voices."""
    if not speaker_name:
        return 0.0
    sp_clean = speaker_name.strip().lower()
    for role_key, offset in SPEAKER_PITCH_OFFSETS.items():
        if role_key in sp_clean:
            return offset
    # Deterministic pseudo-random micro-offset (-0.2Hz to +0.2Hz) to keep characters distinct
    h = int(hashlib.md5(sp_clean.encode("utf-8")).hexdigest()[:4], 16)
    return round(((h % 5) - 2) * 0.1, 2)


def resolve_dynamic_voice_pitch(
    voice_name: str,
    pitch_tier: Optional[str] = None,
    bgm_mood: str = "no_mood",
    current_rate: str = "+0%",
    speaker: str = "",
    fallback_pitch: str = "-2Hz",
    line_id: str = "",
) -> str:
    voice_key = str(voice_name).strip()
    profile = VOICE_PITCH_PROFILES.get(voice_key, VOICE_PITCH_PROFILES["default"])

    # 1. Base Pitch from Tier (falls back cleanly if line has no pitch_tier)
    tier_clean = str(pitch_tier).strip().lower() if pitch_tier else ""
    base_pitch_str = profile.get(tier_clean, fallback_pitch)

    try:
        m = re.search(r'([+-]?\d+(?:\.\d+)?)', str(base_pitch_str))
        base_hz = float(m.group(1)) if m else -2.0
    except Exception:
        base_hz = -2.0

    # 2. BGM Mood Pitch Delta
    mood = normalize_bgm_mood(bgm_mood)
    mood_profiles = BGM_MOOD_PITCH_DELTAS_BY_VOICE.get(voice_key, BGM_MOOD_PITCH_DELTAS_BY_VOICE["default"])
    mood_hz = mood_profiles.get(mood, 0.0)

    # 3. Speech Rate Velocity Offset
    velocity_hz = calculate_rate_velocity_pitch_offset(current_rate)

    # 4. Speaker Identity Offset
    is_narrator = "christopher" in voice_key.lower() or speaker.strip().lower() == "narrator"
    speaker_hz = 0.0 if is_narrator else calculate_speaker_pitch_offset(speaker)

    # Composite Combined Pitch
    pitch_drift = get_sub_perceptual_jitter(line_id, "pitch", -0.6, 0.6) if line_id else 0.0
    total_hz = base_hz + mood_hz + velocity_hz + speaker_hz + pitch_drift

    # Expanded Acoustic Headroom allows full 3-octave SolfÃ¨ge scale (-6.5Hz to +4.5Hz)
    clamped_hz = max(-7.0, min(5.0, total_hz))

    # Edge TTS strictly requires integer Hertz (+0Hz, -2Hz, +1Hz)
    int_hz = int(round(clamped_hz))
    return f"{int_hz:+d}Hz"


_SFX_COPY_LOCK = threading.Lock()
_SFX_COPIED_BUILDS = {}
_SFX_SEMAPHORES = weakref.WeakKeyDictionary()


_BGM_COPY_LOCK = threading.Lock()
_BGM_COPIED_BUILDS = {}


def normalize_bgm_mood(value: Any) -> str:
    """Return an allowed lowercase BGM mood key, strictly defaulting to 'no_mood'."""
    if not isinstance(value, str):
        return "no_mood"
    key = value.strip().lower()
    return key if key in BGM_MOODS else "no_mood"




def calculate_dynamic_rate(base_rate_str: str, bgm_mood_str: str, voice_name: str, line_id: str = "") -> str:
    """Calculates vocal rate using speaker-specific mood deltas, strictly preserving no_mood."""
    mood = normalize_bgm_mood(bgm_mood_str)
    if mood == "no_mood":
        return base_rate_str

    voice_key = voice_name.strip()
    profile = BGM_MOOD_RATE_DELTAS_BY_VOICE.get(
        voice_key,
        BGM_MOOD_RATE_DELTAS_BY_VOICE["default"]
    )
    delta = profile.get(mood, 0)
    if delta == 0:
        return base_rate_str

    # Extract base numeric percentage (e.g. "+5%", "-2%", "0%")
    match = re.search(r'([+-]?\d+)', str(base_rate_str))
    base_val = int(match.group(1)) if match else 0

    rate_drift = get_sub_perceptual_jitter(line_id, "rate", -1.5, 1.8) if line_id else 0.0
    combined = base_val + delta + rate_drift
    # Clamp bounds to avoid Edge-TTS distortion or intelligibility loss
    clamped = max(-25, min(40, int(round(combined))))
    return f"{clamped:+d}%"

def prepare_bgm_assets(build_dir: str) -> str:
    """Synchronize all audio files from root assets/bgm into build_dir/bgm."""
    build_root = os.path.abspath(build_dir)
    source_dir = os.path.join(_SCRIPT_DIR, "assets", "bgm")
    target_dir = os.path.join(build_root, "bgm")

    with _BGM_COPY_LOCK:
        os.makedirs(target_dir, exist_ok=True)
        if not os.path.isdir(source_dir):
            return target_dir

        try:
            for filename in os.listdir(source_dir):
                _, extension = os.path.splitext(filename)
                # Copy all valid audio files regardless of fixed mood set
                if extension.lower() not in BGM_EXTENSIONS:
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

def get_matching_audio_variants(directory: str, key: str, valid_extensions: tuple) -> list:
    """Finds all audio files matching <key> or <key><number> (e.g., clock, clock1, clock2)."""
    if not key or not os.path.isdir(directory):
        return []
    clean_key = key.strip().lower()
    pattern = re.compile(rf"^{re.escape(clean_key)}(?:\d+)?$", re.IGNORECASE)

    try:
        filenames = os.listdir(directory)
    except OSError:
        return []

    candidates = []
    for filename in filenames:
        stem, extension = os.path.splitext(filename)
        if extension.lower() not in valid_extensions:
            continue
        if pattern.match(stem):
            path = os.path.join(directory, filename)
            try:
                if os.path.isfile(path) and os.path.getsize(path) > 0:
                    candidates.append(path)
            except OSError:
                continue
    return sorted(candidates)


def find_bgm_file(bgm_dir: str, mood_key: str) -> Optional[str]:
    """Find a BGM file matching mood_key or mood_key<number>, picking randomly if multiple exist."""
    mood = normalize_bgm_mood(mood_key)
    if mood == "no_mood" or not os.path.isdir(bgm_dir):
        return None

    candidates = get_matching_audio_variants(bgm_dir, mood, BGM_EXTENSIONS)
    return random.choice(candidates) if candidates else None


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
        fade_in = min(3.0, dur * 0.25)
        fade_out = min(3.0, dur * 0.25)
        out_start = max(0.0, dur - fade_out)

        # Loop, trim, exponential swell, linear egress decay, clear vocal mids & tame high-frequency air
        filt = (
            f"[{idx}:a]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono,"
            f"aloop=loop=-1:size=2e+09,"
            f"atrim=0:{dur:.3f},"
            f"afade=t=in:ss=0:d={fade_in:.2f}:curve=qsin,"
            f"afade=t=out:st={out_start:.2f}:d={fade_out:.2f}:curve=tri,"
            f"equalizer=f=2500:t=q:w=1.0:g=-4.0,"
            f"highshelf=f=7000:g=-3.0,"
            f"volume=0.079,"
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
    """Return an allowed canonical SFX key, standardizing punctuation, casing, and director synonyms."""
    if not isinstance(value, str):
        return ""
    
    # Strip spaces, brackets, quotes, or accidental punctuation
    clean = re.sub(r'[^a-zA-Z0-9_]', '', value.strip().lower().replace("-", "_").replace(" ", "_"))
    
    # Check direct canonical key
    if clean in SFX_KEYS:
        return clean
        
    # Check synonym mapping
    canonical = SFX_SYNONYMS.get(clean, "")
    return canonical if canonical in SFX_KEYS else ""


def _get_sfx_semaphore() -> asyncio.Semaphore:
    """Get a dedicated SFX FFmpeg semaphore for the running event loop."""
    loop = asyncio.get_running_loop()
    semaphore = _SFX_SEMAPHORES.get(loop)
    if semaphore is None:
        semaphore = asyncio.Semaphore(SFX_MAX_CONCURRENT_FFMPEG)
        _SFX_SEMAPHORES[loop] = semaphore
    return semaphore


def _sfx_asset_snapshot(directory: str) -> tuple:
    """Describe all recognized audio files in a flat directory, including change markers."""
    if not os.path.isdir(directory):
        return ()

    items = []
    try:
        filenames = os.listdir(directory)
    except OSError:
        return ()

    for filename in filenames:
        _, extension = os.path.splitext(filename)
        # Snapshot and copy all audio assets regardless of frozenset membership
        if extension.lower() not in SFX_EXTENSIONS:
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


def find_sfx_file(sfx_dir: str, sfx_key: str, seed: Optional[str] = None) -> Optional[str]:
    """Find an audio file matching sfx_key or sfx_key<number>, supporting randomized variants."""
    key = normalize_sfx_key(sfx_key)
    if not key or not os.path.isdir(sfx_dir):
        return None

    candidates = get_matching_audio_variants(sfx_dir, key, SFX_EXTENSIONS)
    if not candidates:
        return None

    # Deterministic seed per line_id ensures cache stability while randomizing across different lines
    if seed:
        rnd = random.Random(seed)
        return rnd.choice(candidates)

    return random.choice(candidates)


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
        line_id = str(row.get("line_id", ""))
        path = find_sfx_file(sfx_dir, key, seed=f"{line_id}_{key}")
        if path:
            try:
                stat = os.stat(path)
                asset = (os.path.basename(path), stat.st_size, stat.st_mtime_ns)
            except OSError:
                asset = (os.path.basename(path), None, None)
        else:
            asset = (key, None, None)
        manifest.append((line_id, key, asset))

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
    t_lead: float = 0.0,
) -> None:
    path = _sfx_metadata_path(segment_path)
    temp_path = path + ".tmp"
    payload = {
        "sfx_pipeline_version": SFX_PIPELINE_VERSION,
        "sfx": normalize_sfx_key(sfx_key),
        "sfx_applied": bool(sfx_applied),
        "sfx_asset_signature": asset_signature,
        "t_lead": float(t_lead),
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


# =====================================================================
# SUB-PERCEPTUAL HUMANIZATION & SFX TIMING HELPERS
# =====================================================================

def get_sub_perceptual_jitter(identifier: str, param_name: str, min_val: float, max_val: float) -> float:
    """Computes a deterministic, sub-perceptual floating-point delta within [min_val, max_val].

    Seeded by identifier + param_name to ensure cache stability and reproducible builds.
    """
    if not identifier:
        return 0.0
    seed_key = f"{identifier}_{param_name}".encode("utf-8")
    digest = hashlib.md5(seed_key).hexdigest()
    normalized_ratio = int(digest[:8], 16) / 0xFFFFFFFF
    return min_val + normalized_ratio * (max_val - min_val)


def calculate_sfx_overlap_timing(d_sfx: float, line_id: str = "") -> Tuple[float, float]:
    """Calculates lead-in (T_lead) and under-voice bleed (T_bleed) based on asset duration.

    - Short (<= 1.5s): 100% solo lead, 0.0s bleed.
    - Medium (1.5s - 3.0s): First 80% solo lead, remaining 20% bleed (0.3s - 0.6s).
    - Full (3.0s - 5.0s): Solo lead is (d_sfx - 1.0s), bleed capped at 1.0s.
    """
    d_clamped = min(5.0, max(0.1, float(d_sfx)))

    if d_clamped <= 1.5:
        return round(d_clamped, 3), 0.0
    elif d_clamped <= 3.0:
        t_bleed = round(0.2 * d_clamped, 2)
        t_lead = round(d_clamped - t_bleed, 2)
    else:
        t_bleed = 1.0
        t_lead = round(d_clamped - 1.0, 2)

    if line_id and t_bleed > 0.0:
        drift = get_sub_perceptual_jitter(line_id, "sfx_lead", -0.04, 0.05)
        t_lead = max(0.3, round(t_lead + drift, 3))
        t_bleed = max(0.1, round(d_clamped - t_lead, 3))

    return t_lead, t_bleed

def _prepend_sfx_audio_sync(sfx_path: str, speech_path: str, output_path: str, line_id: str = "") -> float:
    """Concatenate or crossfade SFX with speech, ensuring the speech track remains an untouched master bus."""
    temp_output = output_path + ".sfx_tmp.mp3"
    filename = os.path.basename(sfx_path).lower()
    is_breath = "breath" in filename or "gasp" in filename

    if is_breath:
        # Retain original gentle crossfade for breath assets
        filter_complex = (
            "[0:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono,"
            "volume=0.32,"
            "afade=t=out:st=0.20:d=0.035[sfx];"
            "[1:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[speech];"
            "[sfx][speech]acrossfade=d=0.025:c1=exp:c2=log[out]"
        )
        t_lead = 0.20
    else:
        d_sfx = _probe_duration_sync(sfx_path)
        t_lead, t_bleed = calculate_sfx_overlap_timing(d_sfx, line_id=line_id)

        if t_bleed <= 0.05:
            # Short SFX (<= 1.5s): Pure sequential playback
            filter_complex = (
                "[0:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[sfx];"
                "[1:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[speech];"
                "[sfx][speech]concat=n=2:v=0:a=1[out]"
            )
        else:
            # Medium/Full SFX (> 1.5s): Asymmetric dampening & midrange notch on SFX tail only
            d_total = t_lead + t_bleed
            duck_dur = min(0.15, round(0.25 * t_bleed, 3))
            filter_complex = (
                f"[0:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono,asplit=2[sfx_raw1][sfx_raw2];"
                f"[sfx_raw1]atrim=0:{t_lead:.3f}[sfx_head];"
                f"[sfx_raw2]atrim={t_lead:.3f}:{d_total:.3f},asetpts=PTS-STARTPTS,"
                f"equalizer=f=2000:t=q:w=1.2:g=-6,highpass=f=100,"
                f"volume=0.20,"
                f"afade=t=out:st=0:d={t_bleed:.3f}:curve=log[sfx_tail];"
                f"[1:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[speech];"
                f"[speech][sfx_tail]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[speech_tail];"
                f"[sfx_head][speech_tail]concat=n=2:v=0:a=1[out]"
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
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True)
        if not os.path.isfile(temp_output) or os.path.getsize(temp_output) <= 300:
            raise RuntimeError("FFmpeg did not produce a valid SFX-prefixed segment.")
        os.replace(temp_output, output_path)
        return t_lead
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
    line_id = str(row.get("line_id", ""))
    sfx_path = find_sfx_file(sfx_dir, sfx_key, seed=f"{line_id}_{sfx_key}") if sfx_key else None
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
            t_lead_applied = await asyncio.to_thread(
                _prepend_sfx_audio_sync,
                sfx_path,
                speech_path,
                segment_path,
                line_id=line_id,
            )
        _write_sfx_metadata(segment_path, sfx_key, True, asset_signature, t_lead=t_lead_applied)
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
    line_id = str(row.get("line_id", ""))

    # Micro-pause jitter: break metronomic 300ms turn-taking gap
    if pause_dur is not None:
        try:
            base_p = float(pause_dur)
            if base_p > 0.05:
                jitter = get_sub_perceptual_jitter(line_id, "pause", -0.035, 0.040)
                pause_dur = max(0.05, round(base_p + jitter, 3))
        except (ValueError, TypeError):
            pass
    
    # Dual-Text Separation: Route tts_text to voice engine, falling back to text
    raw_text = row.get("tts_text") or row.get("text", "").strip()
    # Apply LitRPG phonetic dictionary ONLY to spoken audio
    tts_sculpted = apply_pronunciation_lexicon(raw_text)
    text = RE_PAUSE_TAGS.sub("", tts_sculpted).strip()

    # A row is ONLY a pure pause if it contains no spoken alphanumeric text
    is_pure_pause = not text or not RE_ALPHANUM.search(text)

    if is_pure_pause:
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
    speaker_name = row.get("speaker", "Narrator")

    bgm_mood = normalize_bgm_mood(row.get("bgm_mood", "no_mood"))
    pitch_tier = row.get("pitch_tier")

    if is_system:
        voice = "en-US-AriaNeural"
        pitch = "-2Hz"
        rate = "+0%"
    elif is_narration:
        voice = "en-US-ChristopherNeural"
        base_rate = row.get("rate", "+0%")
        rate = calculate_dynamic_rate(base_rate, bgm_mood, voice, line_id=line_id)
        pitch = resolve_dynamic_voice_pitch(
            voice_name=voice,
            pitch_tier=pitch_tier,
            bgm_mood=bgm_mood,
            current_rate=rate,
            speaker=speaker_name,
            fallback_pitch=row.get("pitch", "-2Hz"),
            line_id=line_id
        )
    else:
        req_voice = row.get("voice", "en-US-GuyNeural")
        if req_voice in ["en-US-TonyNeural", "en-US-JasonNeural"]:
            req_voice = "en-US-ChristopherNeural"
        voice = req_voice
        base_rate = row.get("rate", "-4%" if line_type == "Dialogue" else "+0%")
        rate = calculate_dynamic_rate(base_rate, bgm_mood, voice, line_id=line_id)
        pitch = resolve_dynamic_voice_pitch(
            voice_name=voice,
            pitch_tier=pitch_tier,
            bgm_mood=bgm_mood,
            current_rate=rate,
            speaker=speaker_name,
            fallback_pitch=row.get("pitch", "+0Hz"),
            line_id=line_id
        )

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

        except Exception as exc:
            if attempt == max_retries:
                print(f"[TTS Error] Final attempt failed for line {row.get('line_id')}: {exc} (Voice: {active_voice}, Pitch: {pitch}, Rate: {rate})", flush=True)

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
            
            # Subtitle reads literary display_text, keeping phonetic respellings OFF the screen
            raw_display_text = row.get("display_text") or row.get("text", "")
            disp_clean = RE_PAUSE_TAGS.sub("", raw_display_text).strip()

            sfx_offset = 0.0
            segment_meta = _read_sfx_metadata(cf)
            if segment_meta and segment_meta.get("sfx_applied"):
                # Use exact speech onset time (t_lead) rather than full SFX file length
                if "t_lead" in segment_meta:
                    sfx_offset = min(float(segment_meta["t_lead"]), dur)
                else:
                    applied_key = normalize_sfx_key(segment_meta.get("sfx", ""))
                    if applied_key:
                        if applied_key not in sfx_duration_cache:
                            applied_path = find_sfx_file(sfx_dir, applied_key)
                            sfx_duration_cache[applied_key] = (
                                await get_audio_duration(applied_path) if applied_path else 0.0
                            )
                        sfx_offset = min(sfx_duration_cache.get(applied_key, 0.0), dur)

            # Subtitle is generated for any row that contains spoken literary words
            if disp_clean and RE_ALPHANUM.search(disp_clean):
                sub_text = f"[{row['speaker']}]: {disp_clean}" if row.get("line_type") == "Dialogue" else disp_clean
                subtitle_start = rel_time + sfx_offset
                subtitle_end = max(subtitle_start + 0.1, rel_time + dur)
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
    enable_voicefixer: bool = False,
    force_remaster: bool = False,
):
    if (
        not force_remaster
        and os.path.isfile(final_audio_path)
        and os.path.getsize(final_audio_path) > 100_000
    ):
        dur_str = format_timestamp(_probe_duration_sync(final_audio_path))
        print(
            f"\n[Audio Master Engine] [✓] Reusing existing mastered audio: {final_audio_path} ({dur_str})",
            flush=True,
        )
        return

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

        print("[Audio Master Engine] Applying EBU R128 loudness normalization & analog room tone (-54 dB)...", flush=True)
        
        # Inject continuous room tone AFTER compression so it cannot pump during pauses
        # -54 dB amplitude = 0.002
        post_filter = (
            f"[0:a]{audio_filter}[master_clean];"
            f"anoisesrc=d=100000:c=pink:r=44100:a=0.002[room_tone];"
            f"[master_clean][room_tone]amix=inputs=2:duration=first:weights=1 1[outa]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-i", source_audio,
            "-filter_complex", post_filter,
            "-map", "[outa]",
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
# VIDEO MULTIPLEXING (5-Minute Rolling HUD Loop + 10 Backgrounds)
# =====================================================================

def _resolve_hud_overlay_path() -> Optional[str]:
    """Locates hud_overlay_10s.webm in assets/ or working directory."""
    candidates = [
        os.path.join(_SCRIPT_DIR, "assets", "hud_overlay_10s.webm"),
        os.path.join(os.getcwd(), "assets", "hud_overlay_10s.webm"),
        os.path.join(_SCRIPT_DIR, "hud_overlay_10s.webm"),
    ]
    for path in candidates:
        if os.path.isfile(path) and os.path.getsize(path) > 1000:
            return path
    return None


def _build_pseudo_depth_map(bgr_img: "np.ndarray") -> "np.ndarray":
    """
    Computes a smooth [0.0..1.0] 2.5D depth map (1.0 = foreground character/limelight,
    0.0 = distant sky/horizon) combining vertical perspective, center saliency, and edge detail.
    """
    h, w = bgr_img.shape[:2]
    gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    # 1. Vertical depth gradient (bottom foreground is closer than upper sky)
    y_grad = np.linspace(0.10, 0.85, h, dtype=np.float32)[:, None]
    y_map = np.repeat(y_grad, w, axis=1)

    # 2. High-detail edge/focal saliency (sharp foreground subjects vs soft sky/mist)
    lap = np.abs(cv2.Laplacian(gray, cv2.CV_32F, ksize=3))
    lap_blur = cv2.GaussianBlur(lap, (0, 0), sigmaX=max(25, w // 32))
    if lap_blur.max() > 1e-5:
        lap_blur /= lap_blur.max()

    # 3. Rule-of-thirds / lower-center subject bias
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.50, h * 0.58
    dist_sq = ((xx - cx) / (w * 0.42)) ** 2 + ((yy - cy) / (h * 0.45)) ** 2
    center_bias = np.exp(-0.5 * dist_sq)

    depth = 0.42 * y_map + 0.33 * center_bias + 0.25 * lap_blur
    depth = cv2.GaussianBlur(depth, (0, 0), sigmaX=max(35, w // 24))
    d_min, d_max = float(depth.min()), float(depth.max())
    if d_max - d_min > 1e-5:
        depth = (depth - d_min) / (d_max - d_min)
    return depth.astype(np.float32)


def _build_energy_shimmer_mask(bgr_img: "np.ndarray") -> "np.ndarray":
    """
    Isolates luminous magic/Qi energy & high-saturation aura zones so heat-haze
    pixel ripples target glowing Spirit Qi, flames, and skies rather than rigid faces.
    """
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV).astype(np.float32)
    sat = hsv[:, :, 1] / 255.0
    val = hsv[:, :, 2] / 255.0
    energy = np.clip((val - 0.52) * 1.6 + sat * 0.45, 0.0, 1.0)
    energy = cv2.GaussianBlur(energy, (0, 0), sigmaX=24)
    return energy.astype(np.float32)


def _build_god_rays_overlay(w: int, h: int, seed_val: int) -> "np.ndarray":
    """Precomputes diagonal volumetric god-ray light shafts (float32 [0..1] BGR tint)."""
    rng = random.Random(seed_val)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    angle = rng.uniform(0.32, 0.58)  # Diagonal sunbeam tilt
    coord = xx * math.cos(angle) + yy * math.sin(angle)

    rays = (
        0.50 * np.sin(coord * 0.011 + rng.uniform(0, 6.28))
        + 0.30 * np.sin(coord * 0.027 + rng.uniform(0, 6.28))
        + 0.20 * np.cos(coord * 0.049 + rng.uniform(0, 6.28))
    )
    rays = np.clip((rays + 0.25) / 1.25, 0.0, 1.0) ** 1.8

    # Fade rays smoothly toward bottom so they illuminate the upper atmosphere
    vert_fade = np.clip(1.0 - (yy / (h * 0.88)), 0.0, 1.0)[:, :, None]
    tint_bgr = np.array([155.0, 220.0, 255.0], dtype=np.float32)  # Warm Celestial Gold-White
    return (rays[:, :, None] * vert_fade * tint_bgr).astype(np.float32)


def _render_25d_parallax_shot_to_ffmpeg(
    img_path: str,
    out_mp4: str,
    num_frames: int,
    fps: int,
    z0: float,
    dz: float,
    x0: float,
    dx: float,
    y0: float,
    dy: float,
    seed_key: str,
) -> None:
    """
    Renders a 1080p shot with true 2.5D Depth Parallax, sinusoidal Energy/Heat-Haze
    Shimmer, and sweeping Volumetric God Rays via OpenCV/NumPy, then pipes directly into
    FFmpeg for Optical Rack Focus, Magic Qi Highlight Bloom, Dynamic Vignette, and 35mm Grain.
    """
    raw_bgr = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if raw_bgr is None:
        raise FileNotFoundError(f"Failed to load background image: {img_path}")

    out_w, out_h = 1920, 1080
    src_bgr = cv2.resize(raw_bgr, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    depth_map = _build_pseudo_depth_map(src_bgr)
    shimmer_mask = _build_energy_shimmer_mask(src_bgr)

    rng = random.Random(seed_key)
    god_rays = _build_god_rays_overlay(out_w, out_h, rng.randint(1, 999999))
    sway_x_amp = rng.uniform(0.012, 0.022) * rng.choice([-1, 1])
    sway_y_amp = rng.uniform(0.012, 0.022) * rng.choice([-1, 1])
    sway_ph = rng.uniform(0.0, 2.0 * math.pi)
    shimmer_phase = rng.uniform(0.0, 2.0 * math.pi)

    # Precompute base normalized pixel grid [0..out_w-1], [0..out_h-1]
    grid_y, grid_x = np.mgrid[0:out_h, 0:out_w].astype(np.float32)
    norm_x = grid_x / float(out_w)
    norm_y = grid_y / float(out_h)

    # FFmpeg post-FX chain:
    # 1. Optical Rack Focus (first 0.65s snaps from soft lens blur into razor focus)
    # 2. Magic / Qi Highlight Bloom (bright energy areas blurred and screen-blended)
    # 3. Dynamic Lighting pulse + Cinematic Vignette + 35mm Film Grain
    vf_post = (
        "[0:v]"
        "gblur=sigma=9:enable='lt(t,0.30)',"
        "gblur=sigma=3.5:enable='between(t,0.30,0.65)',"
        "split[base][hi];"
        "[hi]lutyuv=y='if(gt(val,185),val,0)':u=128:v=128,gblur=sigma=20[bloom];"
        "[base][bloom]blend=all_mode=screen:all_opacity=0.42,"
        "eq=brightness='0.018*sin(2*PI*t/10)':contrast=1.04:saturation=1.08,"
        "vignette=angle=PI/4.6,"
        "noise=alls=6:allf=t+u,"
        "format=yuv420p[outv]"
    )

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{out_w}x{out_h}", "-r", str(fps),
        "-i", "pipe:0",
        "-filter_complex", vf_post,
        "-map", "[outv]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-an",
        out_mp4,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for f_idx in range(num_frames):
            t_u = f_idx / float(max(1, num_frames - 1))
            ease = 0.5 * (1.0 - math.cos(math.pi * t_u))

            # 2.5D Parallax: foreground moves/zooms 1.45x faster than distant background
            z_base = z0 + dz * ease
            z_fg = 1.0 + (z_base - 1.0) * 1.45
            z_bg = 1.0 + (z_base - 1.0) * 0.72
            z_map = z_bg + (z_fg - z_bg) * depth_map

            pan_x = np.clip(
                x0 + dx * ease + sway_x_amp * math.sin(math.pi * t_u + sway_ph),
                0.0, 1.0
            )
            pan_y = np.clip(
                y0 + dy * ease + sway_y_amp * math.cos(math.pi * t_u + sway_ph),
                0.0, 1.0
            )

            # Parallax shift amplifies on foreground pixels (depth_map -> 1.0)
            parallax_gain = 0.65 + 0.75 * depth_map
            eff_pan_x = np.clip(0.5 + (pan_x - 0.5) * parallax_gain, 0.0, 1.0)
            eff_pan_y = np.clip(0.5 + (pan_y - 0.5) * parallax_gain, 0.0, 1.0)

            crop_w = out_w / z_map
            crop_h = out_h / z_map
            map_x = (out_w - crop_w) * eff_pan_x + norm_x * crop_w
            map_y = (out_h - crop_h) * eff_pan_y + norm_y * crop_h

            # Sinusoidal Energy & Heat-Haze Shimmer on glowing Qi/aura regions
            wave_t = (2.0 * math.pi * 2.0 * t_u) + shimmer_phase
            ripple_x = 2.2 * np.sin(grid_y * 0.045 + wave_t) * shimmer_mask
            ripple_y = 1.6 * np.cos(grid_x * 0.040 + wave_t * 1.3) * shimmer_mask
            map_x = (map_x + ripple_x).astype(np.float32)
            map_y = (map_y + ripple_y).astype(np.float32)

            warped = cv2.remap(
                src_bgr, map_x, map_y,
                interpolation=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT_101,
            )

            # Volumetric God Rays sweeping gently in brightness
            ray_strength = 0.14 + 0.08 * math.sin(2.0 * math.pi * t_u + sway_ph)
            composited = np.clip(
                warped.astype(np.float32) + god_rays * ray_strength,
                0, 255
            ).astype(np.uint8)

            proc.stdin.write(composited.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg post-FX pipe failed with exit code {ret}")


def build_5min_hud_loop_video(
    blocks: list,
    build_dir: str,
    loop_duration_sec: float = 300.0,
    fps: int = 30,
) -> str:
    """
    Builds a 5-minute (300s) 1080p/30fps animated master loop using the 10 blocks x 3 angles x 10s
    structure enhanced with:
      - 2.5D Depth Parallax, Energy Shimmer & Volumetric God Rays (OpenCV/NumPy)
      - Optical Rack Focus, Magic Qi Highlight Bloom, Dynamic Vignette & 35mm Grain (FFmpeg)
      - Seamless xfade Morph Transitions between all 30 camera angles + hud_overlay_10s.webm
    """
    master_loop_path = os.path.join(build_dir, "master_hud_loop_5m.mp4")
    if os.path.isfile(master_loop_path) and os.path.getsize(master_loop_path) > 100_000:
        print(f"[HUD Loop] [✓] Reusing cached 5-minute master loop: {master_loop_path}", flush=True)
        return master_loop_path

    bg_images: List[Tuple[int, str]] = []
    for cfg in blocks:
        b_idx = cfg["index"]
        cover_path = cfg.get("cover_file")
        if not cover_path or not os.path.exists(cover_path):
            r_start, r_end = cfg.get("range", (0, 0))
            candidate = os.path.join(build_dir, f"cover_block_{r_start}_{r_end}.jpg")
            if os.path.exists(candidate):
                cover_path = candidate
        if cover_path and os.path.exists(cover_path):
            bg_images.append((b_idx, cover_path))

    if not bg_images:
        raise FileNotFoundError("No background cover images found to build the 5-minute HUD loop.")

    hud_webm = _resolve_hud_overlay_path()
    if not hud_webm:
        raise FileNotFoundError(
            "assets/hud_overlay_10s.webm not found. Run 'python testdraw.py' first to generate the HUD overlay."
        )

    num_imgs = len(bg_images)
    angles_per_img = 3
    effective_angle_sec = round(loop_duration_sec / (num_imgs * angles_per_img), 3)  # 10.0s per angle
    xfade_dur = 0.50  # 0.50s smooth xfade overlap between every camera cut
    raw_angle_frames = int(round((effective_angle_sec + xfade_dur) * fps))  # 315 frames = 10.50s
    raw_angle_sec = raw_angle_frames / float(fps)
    block_dur_with_tail = round(angles_per_img * effective_angle_sec + xfade_dur, 3)  # 30.50s

    angle_templates = [
        ("Hero Right Push-In",    1.02, 0.24, 0.48,  0.28, 0.48, -0.08),
        ("Upper-Left Vista Zoom", 1.04, 0.23, 0.42, -0.25, 0.42, -0.18),
        ("Rising Center Reveal",  1.03, 0.25, 0.46,  0.12, 0.70, -0.30),
    ]
    intra_xfades = ["dissolve", "smoothup", "radial", "smoothright"]
    inter_xfades = ["fadeblack", "dissolve", "smoothleft", "wipeleft"]

    print(
        f"[HUD Loop] Building {loop_duration_sec:.0f}s 2.5D FX reel from {num_imgs} backgrounds "
        f"({angles_per_img} angles x {effective_angle_sec:.1f}s + {xfade_dur}s xfade)...",
        flush=True,
    )

    block_clips = []
    temp_files = []
    total_shots = num_imgs * angles_per_img
    shot_counter = 0

    for seq_idx, (b_idx, img_path) in enumerate(bg_images, 1):
        angle_clips = []
        for ang_idx, (ang_name, z0, dz, x0, dx, y0, dy) in enumerate(angle_templates, 1):
            shot_counter += 1
            ang_out = os.path.join(build_dir, f"_tmp_25d_b{seq_idx:02d}_a{ang_idx}.mp4")
            temp_files.append(ang_out)

            if CV2_NUMPY_AVAILABLE:
                _render_25d_parallax_shot_to_ffmpeg(
                    img_path=img_path,
                    out_mp4=ang_out,
                    num_frames=raw_angle_frames,
                    fps=fps,
                    z0=z0, dz=dz, x0=x0, dx=dx, y0=y0, dy=dy,
                    seed_key=f"fx_25d_{b_idx}_{ang_idx}",
                )
            else:
                # Pure-FFmpeg fallback if OpenCV is unavailable
                ease = f"(0.5*(1-cos(PI*on/{raw_angle_frames})))"
                vf = (
                    f"scale=5760:-1:flags=lanczos,"
                    f"zoompan=z='{z0}+{dz}*{ease}':"
                    f"x='(iw-iw/zoom)*clip({x0}+({dx})*{ease},0,1)':"
                    f"y='(ih-ih/zoom)*clip({y0}+({dy})*{ease},0,1)':"
                    f"d={raw_angle_frames}:s=1920x1080:fps={fps},"
                    f"gblur=sigma=8:enable='lt(t,0.45)',"
                    f"vignette=angle=PI/4.6,noise=alls=6:allf=t+u,format=yuv420p"
                )
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-loop", "1", "-t", f"{raw_angle_sec:.3f}", "-i", img_path,
                        "-vf", vf, "-t", f"{raw_angle_sec:.3f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                        "-pix_fmt", "yuv420p", "-an", ang_out,
                    ],
                    check=True,
                )

            angle_clips.append(ang_out)
            print(
                f"     [HUD Loop] Rendered {shot_counter:02d}/{total_shots} "
                f"(2.5D FX {ang_name}): {os.path.basename(img_path)}",
                flush=True,
            )

        # Blend the 3 angles of this block with xfade (keeps 0.50s tail for inter-block xfade)
        block_out = os.path.join(build_dir, f"_tmp_25d_block_{seq_idx:02d}.mp4")
        temp_files.append(block_out)
        tr1 = intra_xfades[(b_idx) % len(intra_xfades)]
        tr2 = intra_xfades[(b_idx + 1) % len(intra_xfades)]
        off1 = round(effective_angle_sec, 3)
        off2 = round(effective_angle_sec * 2.0, 3)

        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", angle_clips[0], "-i", angle_clips[1], "-i", angle_clips[2],
                "-filter_complex",
                f"[0:v][1:v]xfade=transition={tr1}:duration={xfade_dur:.2f}:offset={off1:.3f}[xf1];"
                f"[xf1][2:v]xfade=transition={tr2}:duration={xfade_dur:.2f}:offset={off2:.3f}[vblk]",
                "-map", "[vblk]",
                "-t", f"{block_dur_with_tail:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-g", str(fps),
                "-pix_fmt", "yuv420p", "-an",
                block_out,
            ],
            check=True,
        )
        block_clips.append(block_out)

    # Blend all 10 block clips together via xfade into the 300s background track
    raw_bg_300s = os.path.join(build_dir, "_tmp_25d_bg_300s.mp4")
    temp_files.append(raw_bg_300s)

    blk_inputs = []
    for bc in block_clips:
        blk_inputs.extend(["-i", bc])

    blk_xfade_chains = []
    prev_pad = "[0:v]"
    per_block_step = round(angles_per_img * effective_angle_sec, 3)  # 30.0s
    for k in range(1, len(block_clips)):
        off_b = round(k * per_block_step, 3)
        tr_b = inter_xfades[k % len(inter_xfades)]
        out_pad = f"[bxf{k}]" if k < len(block_clips) - 1 else "[v300]"
        blk_xfade_chains.append(
            f"{prev_pad}[{k}:v]xfade=transition={tr_b}:duration={xfade_dur:.2f}:offset={off_b:.3f}{out_pad}"
        )
        prev_pad = out_pad

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            *blk_inputs,
            "-filter_complex", ";".join(blk_xfade_chains),
            "-map", "[v300]",
            "-t", f"{loop_duration_sec:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-g", str(fps),
            "-pix_fmt", "yuv420p", "-an",
            raw_bg_300s,
        ],
        check=True,
    )

    # Composite transparent hud_overlay_10s.webm over the 300s 2.5D FX reel
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", raw_bg_300s,
            "-c:v", "libvpx-vp9", "-stream_loop", "-1", "-i", hud_webm,
            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[outv]",
            "-map", "[outv]",
            "-t", f"{loop_duration_sec:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-g", str(fps),
            "-pix_fmt", "yuv420p", "-an",
            master_loop_path,
        ],
        check=True,
    )

    for tmp in temp_files:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass

    print(f"[HUD Loop] [✓] Created 5-minute 2.5D FX master loop: {master_loop_path}", flush=True)
    return master_loop_path


def assemble_multi_image_video(
    blocks: list,
    block_durations: dict,
    build_dir: str,
    final_audio_path: str,
    output_video_path: str,
    subtitles_srt_path: Optional[Union[str, Dict[str, str]]] = None
):
    print("\n[Multiplexer] Assembling 5-Minute Rolling HUD Video + Outro Card...", flush=True)

    total_audio_dur = _probe_duration_sync(final_audio_path)
    if total_audio_dur <= 1.0:
        total_audio_dur = max(60.0, sum(block_durations.values()))

    outro_slate = os.path.join(build_dir, "outro_slate_card.jpg")
    has_outro = os.path.exists(outro_slate)
    outro_dur = 15.0 if has_outro else 0.0
    main_video_dur = max(10.0, total_audio_dur - outro_dur)

    # 1. Build (or reuse) the 5-minute (300s) 10-background animated HUD loop
    master_loop_5m = build_5min_hud_loop_video(blocks, build_dir, loop_duration_sec=300.0, fps=30)

    # 2. Stream-copy the 5-minute loop across the entire main audiobook duration (instantaneous)
    main_looped_track = os.path.join(build_dir, "v_seg_main_hud_loop.mp4")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-stream_loop", "-1",
            "-i", master_loop_5m,
            "-t", f"{main_video_dur:.3f}",
            "-c:v", "copy",
            main_looped_track,
        ],
        check=True,
    )

    video_segments = [main_looped_track]

    # 3. Append 15s Outro Card encoded at matching 30fps yuv420p so concat -c copy is seamless
    outro_seg = os.path.join(build_dir, "v_seg_outro.mp4")
    if has_outro:
        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-loop", "1", "-framerate", "30", "-t", f"{outro_dur:.3f}",
                "-i", outro_slate,
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
                "-r", "30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-g", "30",
                "-pix_fmt", "yuv420p", "-an",
                outro_seg,
            ],
            check=True,
        )
        video_segments.append(outro_seg)

    v_manifest = os.path.join(build_dir, "v_segments_list.txt")
    with open(v_manifest, "w", encoding="utf-8") as f:
        for vs in video_segments:
            f.write(f"file '{os.path.abspath(vs).replace(os.sep, '/')}'\n")

    full_video_track = os.path.join(build_dir, "full_video_track.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", v_manifest, "-c", "copy", full_video_track],
        check=True,
    )

    mux_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", full_video_track,
        "-i", final_audio_path,
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
        output_video_path,
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