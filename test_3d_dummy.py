import asyncio
import hashlib
import json
import math
import os
import shutil
import subprocess
import time
import numpy as np
import edge_tts

from media_utils import (
    PEDALBOARD_AVAILABLE,
    RE_ALPHANUM,
    RE_PAUSE_TAGS,
    find_sfx_file,
    find_bgm_file,
    normalize_sfx_key,
    normalize_bgm_mood,
    get_sub_perceptual_jitter,
    calculate_sfx_overlap_timing,
    calculate_dynamic_rate,
    resolve_dynamic_voice_pitch,
    _probe_duration_sync,
    master_audio_with_pedalboard,
    format_timestamp,
)
from lexicon_utils import apply_pronunciation_lexicon

if PEDALBOARD_AVAILABLE:
    from pedalboard import (
        Pedalboard,
        HighpassFilter,
        LowShelfFilter,
        PeakFilter,
        HighShelfFilter,
    )
    from pedalboard.io import AudioFile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STAGED_JSON_PATH = os.path.join(
    SCRIPT_DIR, "build_origin_summoner_91_120", "ch_091_staged.json"
)
SFX_DIR = os.path.join(SCRIPT_DIR, "assets", "sfx")
BGM_DIR = os.path.join(SCRIPT_DIR, "assets", "bgm")
WORK_DIR = os.path.join(SCRIPT_DIR, "_full_ch091_3d_build")

OUT_3D_MP3 = os.path.join(SCRIPT_DIR, "ch091_3d_enhanced_master.mp3")
OUT_MONO_MP3 = os.path.join(SCRIPT_DIR, "ch091_mono_control.mp3")


# =====================================================================
# 1. TRAILING SILENCE TRIM + 12ms MICRO-FADES
# =====================================================================

def trim_and_microfade_speech(raw_mp3: str, clean_mp3: str, trailing_pad_sec: float = 0.0) -> None:
    tmp_out = clean_mp3 + ".trim_tmp.mp3"
    pad_filter = f",apad=pad_dur={trailing_pad_sec:.3f}" if trailing_pad_sec > 0.02 else ""
    af = (
        "areverse,"
        "silenceremove=start_periods=1:start_duration=0.015:start_threshold=-52dB,"
        "areverse,"
        "afade=t=in:st=0:d=0.012,"
        "areverse,afade=t=in:st=0:d=0.012,areverse"
        f"{pad_filter}"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", raw_mp3, "-af", af,
            "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "24000", "-ac", "1",
            tmp_out,
        ],
        check=True,
    )
    os.replace(tmp_out, clean_mp3)


# =====================================================================
# 2. ROLE & EMOTION TIMBRE SCULPTING (ZERO REVERB / ZERO ECHO)
# =====================================================================

def apply_role_timbre_sculpting(mono_mp3: str, row: dict) -> None:
    if not PEDALBOARD_AVAILABLE:
        return

    speaker = str(row.get("speaker", "")).strip().lower()
    line_type = str(row.get("line_type", "Narration")).strip()
    pitch_tier = str(row.get("pitch_tier", "")).strip().lower()
    emotion = str(row.get("emotion", "")).strip().lower()

    chain = []
    if line_type == "System":
        chain.extend([
            HighpassFilter(cutoff_frequency_hz=130.0),
            PeakFilter(cutoff_frequency_hz=850.0, gain_db=-2.2, q=1.2),
            HighShelfFilter(cutoff_frequency_hz=3600.0, gain_db=2.8),
        ])
    elif any(k in speaker for k in ("lord", "king", "beast", "boar", "monster", "dragon", "demon")):
        chain.extend([
            LowShelfFilter(cutoff_frequency_hz=125.0, gain_db=3.2),
            PeakFilter(cutoff_frequency_hz=260.0, gain_db=1.5, q=1.0),
            HighShelfFilter(cutoff_frequency_hz=5500.0, gain_db=-1.5),
        ])
    elif "strained" in pitch_tier or "alarmed" in pitch_tier or emotion in ("ominous", "calm_defiant"):
        chain.extend([
            PeakFilter(cutoff_frequency_hz=3100.0, gain_db=2.0, q=1.3),
            LowShelfFilter(cutoff_frequency_hz=180.0, gain_db=1.0),
        ])

    if not chain:
        return

    board = Pedalboard(chain)
    with AudioFile(mono_mp3) as f:
        sr = f.samplerate
        audio = f.read(f.frames)

    processed = board(audio, sr)
    tmp_wav = mono_mp3 + ".timbre.wav"
    with AudioFile(tmp_wav, "w", sr, processed.shape[0]) as o:
        o.write(processed)

    tmp_mp3 = mono_mp3 + ".timbre.mp3"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", tmp_wav, "-c:a", "libmp3lame", "-b:a", "192k", "-ar", str(sr), "-ac", "1",
            tmp_mp3,
        ],
        check=True,
    )
    os.remove(tmp_wav)
    os.replace(tmp_mp3, mono_mp3)


# =====================================================================
# 3. DRY 3D BINAURAL SPATIALIZER (ILD + ITD + HEAD-SHADOW)
# =====================================================================

def get_speaker_azimuth(speaker: str, line_type: str, line_id: str) -> float:
    sp = speaker.strip().lower()
    if line_type == "Narration" or sp == "narrator" or line_type == "System":
        return 0.0
    if "katherine" in sp:
        base_pan = -0.25
    elif "webfiend" in sp:
        base_pan = 0.28
    else:
        h = int(hashlib.md5(sp.encode("utf-8")).hexdigest()[:4], 16)
        base_pan = ((h % 7) - 3) * 0.09
    drift = get_sub_perceptual_jitter(line_id, "pan3d", -0.03, 0.03)
    return max(-0.35, min(0.35, base_pan + drift))


def convert_segment_to_dry_3d(mono_mp3: str, out_3d_mp3: str, speaker: str, line_type: str, line_id: str) -> float:
    if not PEDALBOARD_AVAILABLE:
        raise RuntimeError("pedalboard is required for 3D spatial processing.")

    pan = get_speaker_azimuth(speaker, line_type, line_id)

    with AudioFile(mono_mp3) as f:
        sr = f.samplerate
        audio = f.read(f.frames)

    mono = audio[0] if audio.ndim > 1 else audio
    n = len(mono)
    if n < int(sr * 0.04):
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mono_mp3, "-ac", "2", out_3d_mp3],
            check=True,
        )
        return pan

    angle = (pan + 1.0) * (math.pi / 4.0)
    left = mono * math.cos(angle)
    right = mono * math.sin(angle)

    itd_samples = int(round(abs(pan) * 0.00030 * sr))
    if itd_samples > 0:
        if pan > 0:
            left = np.pad(left, (itd_samples, 0))[:n]
        else:
            right = np.pad(right, (itd_samples, 0))[:n]

    stereo = np.vstack([left, right]).astype(np.float32)

    if abs(pan) > 0.08:
        shadow = HighShelfFilter(cutoff_frequency_hz=4200.0, gain_db=-3.2 * abs(pan) * 2.5)
        far_ch = 0 if pan > 0 else 1
        stereo[far_ch] = shadow(stereo[far_ch][None, :], sr)[0]

    tmp_wav = out_3d_mp3 + ".3d_tmp.wav"
    with AudioFile(tmp_wav, "w", sr, 2) as o:
        o.write(stereo)

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", tmp_wav, "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "24000", "-ac", "2",
            out_3d_mp3,
        ],
        check=True,
    )
    os.remove(tmp_wav)
    return pan


# =====================================================================
# 4. SPEAKER-LOCKED SFX PANNING
# =====================================================================

def compute_sfx_pan(sfx_key: str, speaker: str, speaker_pan: float, line_id: str) -> float:
    key = sfx_key.lower()
    sp = speaker.strip().lower()
    if any(k in key for k in ("breath", "gasp", "step", "footstep", "cough")):
        if abs(speaker_pan) > 0.05:
            return round(speaker_pan, 2)
        if "female" in key or "katherine" in sp:
            return -0.25
    if abs(speaker_pan) > 0.05:
        jitter = get_sub_perceptual_jitter(line_id, "sfx_pan_bias", -0.15, 0.15)
        return round(max(-0.55, min(0.55, speaker_pan * 1.2 + jitter)), 2)
    return round(get_sub_perceptual_jitter(line_id, "sfx_pan", -0.45, 0.45), 2)


def prepend_sfx_locked(
    sfx_path: str,
    speech_path: str,
    out_path: str,
    line_id: str,
    stereo: bool,
    sfx_pan: float = 0.0,
) -> None:
    ch_layout = "stereo" if stereo else "mono"
    ac = "2" if stereo else "1"
    tmp_out = out_path + ".sfx_tmp.mp3"
    pan_filter = f",stereotools=mpan={sfx_pan}" if stereo else ""

    filename = os.path.basename(sfx_path).lower()
    if "breath" in filename or "gasp" in filename:
        fc = (
            f"[0:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts={ch_layout},"
            f"apad=whole_dur=0.235,atrim=0:0.235,asetpts=PTS-STARTPTS,"
            f"volume=0.35{pan_filter},afade=t=out:st=0.20:d=0.035[sfx];"
            f"[1:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts={ch_layout}[speech];"
            f"[sfx][speech]acrossfade=d=0.025:c1=exp:c2=log[out]"
        )
    else:
        d_sfx = _probe_duration_sync(sfx_path)
        t_lead, t_bleed = calculate_sfx_overlap_timing(d_sfx, line_id=line_id)
        d_total = t_lead + t_bleed

        if t_bleed <= 0.05:
            fc = (
                f"[0:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts={ch_layout},"
                f"loudnorm=I=-20:TP=-3:LRA=7,volume=0.55{pan_filter}[sfx];"
                f"[1:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts={ch_layout}[speech];"
                f"[sfx][speech]concat=n=2:v=0:a=1[out]"
            )
        else:
            fc = (
                f"[0:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts={ch_layout},"
                f"atrim=0:{d_total:.3f},asetpts=PTS-STARTPTS,"
                f"loudnorm=I=-20:TP=-3:LRA=7{pan_filter},"
                f"asplit=2[sfx_raw1][sfx_raw2];"
                f"[sfx_raw1]atrim=0:{t_lead:.3f},asetpts=PTS-STARTPTS,volume=0.55[sfx_head];"
                f"[sfx_raw2]atrim={t_lead:.3f}:{d_total:.3f},asetpts=PTS-STARTPTS,"
                f"equalizer=f=2000:t=q:w=1.2:g=-6,highpass=f=100,volume=0.22,"
                f"afade=t=out:st=0:d={t_bleed:.3f}:curve=log[sfx_tail];"
                f"[1:a:0]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts={ch_layout}[speech];"
                f"[speech][sfx_tail]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[speech_tail];"
                f"[sfx_head][speech_tail]concat=n=2:v=0:a=1[out]"
            )

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", sfx_path, "-i", speech_path,
            "-filter_complex", fc, "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "24000", "-ac", ac,
            tmp_out,
        ],
        check=True,
    )
    os.replace(tmp_out, out_path)


# =====================================================================
# 5. SPEECH-TRIGGERED BGM SIDECHAIN DUCKING + BROADCAST MASTERING
# =====================================================================

def mix_sidechained_bgm_and_master(
    concat_audio: str,
    rows: list,
    durations: list,
    final_out: str,
    stereo: bool,
) -> None:
    ch_layout = "stereo" if stereo else "mono"
    ac = "2" if stereo else "1"

    intervals = []
    cur_mood = "no_mood"
    start_t = 0.0
    acc_t = 0.0
    for r, d in zip(rows, durations):
        m = normalize_bgm_mood(r.get("bgm_mood", "no_mood"))
        if m != cur_mood:
            if cur_mood != "no_mood":
                intervals.append((cur_mood, start_t, acc_t))
            cur_mood = m
            start_t = acc_t
        acc_t += d
    if cur_mood != "no_mood":
        intervals.append((cur_mood, start_t, acc_t))

    valid_bgm = []
    for mood, s_t, e_t in intervals:
        span = e_t - s_t
        if span >= 5.0:
            bgm_f = find_bgm_file(BGM_DIR, mood)
            if bgm_f:
                valid_bgm.append((mood, bgm_f, s_t, span))

    mixed_bgm = concat_audio + ".bgm.mp3"
    if valid_bgm:
        inputs = ["-i", concat_audio]
        fc_parts = ["[0:a]asplit=2[voc_main][sc_trig]"]
        bgm_pads = []
        widen = ",stereotools=mlev=0.85:slev=1.25" if stereo else ""

        for idx, (mood, bgm_f, s_t, span) in enumerate(valid_bgm, start=1):
            print(f"[Assets] BGM span '{mood}' ({span:.1f}s @ {s_t:.1f}s) -> {os.path.basename(bgm_f)}", flush=True)
            inputs.extend(["-i", bgm_f])
            fi = min(2.5, span * 0.25)
            fo = min(2.5, span * 0.25)
            out_st = max(0.0, span - fo)
            fc_parts.append(
                f"[{idx}:a]aresample=24000,aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts={ch_layout},"
                f"aloop=loop=-1:size=2e+09,atrim=0:{span:.3f},"
                f"afade=t=in:ss=0:d={fi:.2f}:curve=qsin,"
                f"afade=t=out:st={out_st:.2f}:d={fo:.2f}:curve=tri,"
                f"equalizer=f=2500:t=q:w=1.0:g=-4.0,highshelf=f=7000:g=-3.0{widen},"
                f"volume=0.135,adelay={int(s_t * 1000)}|{int(s_t * 1000)}[bgm_{idx}]"
            )
            bgm_pads.append(f"[bgm_{idx}]")

        if len(bgm_pads) == 1:
            fc_parts.append(f"{bgm_pads[0]}anull[bgm_bus]")
        else:
            n_b = len(bgm_pads)
            fc_parts.append(
                f"{''.join(bgm_pads)}amix=inputs={n_b}:duration=longest:dropout_transition=2:normalize=0[bgm_bus]"
            )

        fc_parts.append(
            "[bgm_bus][sc_trig]sidechaincompress=threshold=0.018:ratio=5.5:attack=35:release=340:makeup=1[bgm_ducked];"
            "[voc_main][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2:weights=1.0 1.0:normalize=0[outa]"
        )

        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                *inputs, "-filter_complex", ";".join(fc_parts), "-map", "[outa]",
                "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "24000", "-ac", ac,
                mixed_bgm,
            ],
            check=True,
        )
    else:
        shutil.copy2(concat_audio, mixed_bgm)

    pb_wav = concat_audio + ".pb.wav"
    pb_ok = master_audio_with_pedalboard(mixed_bgm, pb_wav)
    src = pb_wav if pb_ok else mixed_bgm

    post_filter = (
        "[0:a]volume=1.5dB,equalizer=f=3200:t=q:w=1.5:g=2.0,loudnorm=I=-14:TP=-1.5:LRA=7[master_clean];"
        "anoisesrc=d=1000:c=pink:r=44100:a=0.002[room_tone];"
        "[master_clean][room_tone]amix=inputs=2:duration=first:weights=1 1[outa]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", src, "-filter_complex", post_filter, "-map", "[outa]",
            "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", ac,
            final_out,
        ],
        check=True,
    )


# =====================================================================
# 6. POST-MASTER AUDIO QC SCANNER
# =====================================================================

def run_post_master_qc(audio_path: str, max_silence_sec: float = 3.5) -> None:
    cmd = [
        "ffmpeg", "-nostdin", "-i", audio_path,
        "-f", "f32le", "-ac", "2", "-acodec", "pcm_f32le", "-ar", "16000", "-"
    ]
    raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    samples = np.frombuffer(raw, np.float32).reshape(-1, 2)
    sr = 16000
    total_sec = len(samples) / sr

    peak_db = 20.0 * math.log10(max(1e-7, float(np.max(np.abs(samples)))))
    rms_l = float(np.sqrt(np.mean(samples[:, 0] ** 2)))
    rms_r = float(np.sqrt(np.mean(samples[:, 1] ** 2)))
    lr_balance_db = 20.0 * math.log10(max(1e-7, rms_l) / max(1e-7, rms_r))

    win = int(sr * 0.1)
    n_wins = len(samples) // win
    mono_win = np.mean(samples[: n_wins * win], axis=1).reshape(n_wins, win)
    win_rms_db = 20.0 * np.log10(np.maximum(1e-7, np.sqrt(np.mean(mono_win ** 2, axis=1))))

    dead_air_spans = []
    run_start = None
    for idx, db_val in enumerate(win_rms_db):
        if db_val < -48.0:
            if run_start is None:
                run_start = idx * 0.1
        else:
            if run_start is not None:
                gap = (idx * 0.1) - run_start
                if gap >= max_silence_sec:
                    dead_air_spans.append((run_start, gap))
                run_start = None

    print(
        f"\n[Audio QC] {os.path.basename(audio_path)} | Duration: {format_timestamp(total_sec)} | "
        f"True Peak: {peak_db:.2f} dBFS | L/R Balance: {lr_balance_db:+.2f} dB | "
        f"Dead-Air Alerts (>{max_silence_sec}s): {len(dead_air_spans)}",
        flush=True,
    )
    for st, gp in dead_air_spans:
        print(f"   [QC Warning] Dead-air gap of {gp:.1f}s detected at {format_timestamp(st)}", flush=True)


# =====================================================================
# PARALLEL CHAPTER SYNTHESIS & COMPARISON RUNNER
# =====================================================================

async def process_single_row(idx: int, row: dict, sem: asyncio.Semaphore):
    lid = str(row.get("line_id", f"{idx:04d}"))
    prefix = f"{idx:04d}_{lid}"
    raw_text = (row.get("tts_text") or row.get("text") or "").strip()
    text = RE_PAUSE_TAGS.sub("", apply_pronunciation_lexicon(raw_text)).strip()
    is_pure_pause = not text or not RE_ALPHANUM.search(text)
    pause_dur = float(row.get("pause_duration") or 0.0)

    raw_mono = os.path.join(WORK_DIR, f"{prefix}_raw.mp3")
    seg_3d = os.path.join(WORK_DIR, f"{prefix}_3d.mp3")
    seg_mono = os.path.join(WORK_DIR, f"{prefix}_mono.mp3")

    if is_pure_pause:
        dur = max(0.05, pause_dur if pause_dur > 0 else 0.5)
        await asyncio.to_thread(
            subprocess.run,
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", f"{dur:.2f}", "-q:a", "9", "-acodec", "libmp3lame", raw_mono,
            ],
            check=True,
        )
    else:
        line_type = row.get("line_type", "Narration")
        speaker_name = row.get("speaker", "Narrator")
        bgm_mood = normalize_bgm_mood(row.get("bgm_mood", "no_mood"))
        pitch_tier = row.get("pitch_tier")
        voice = row.get("voice", "en-US-ChristopherNeural")
        base_rate = row.get("rate", "+0%")
        rate = calculate_dynamic_rate(base_rate, bgm_mood, voice, line_id=lid)
        pitch = resolve_dynamic_voice_pitch(
            voice_name=voice,
            pitch_tier=pitch_tier,
            bgm_mood=bgm_mood,
            current_rate=rate,
            speaker=speaker_name,
            fallback_pitch=row.get("pitch", "-2Hz"),
            line_id=lid,
        )

        async with sem:
            comm = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
            await comm.save(raw_mono)

        await asyncio.to_thread(trim_and_microfade_speech, raw_mono, raw_mono, pause_dur)
        await asyncio.to_thread(apply_role_timbre_sculpting, raw_mono, row)

    await asyncio.to_thread(shutil.copy2, raw_mono, seg_mono)

    if is_pure_pause:
        await asyncio.to_thread(
            subprocess.run,
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw_mono, "-ac", "2", seg_3d],
            check=True,
        )
        speaker_pan = 0.0
    else:
        speaker_pan = await asyncio.to_thread(
            convert_segment_to_dry_3d, raw_mono, seg_3d, row.get("speaker", "Narrator"), row.get("line_type", "Narration"), lid
        )

    sfx_key = normalize_sfx_key(row.get("sfx", ""))
    if sfx_key:
        sfx_path = find_sfx_file(SFX_DIR, sfx_key, seed=f"{lid}_{sfx_key}")
        if sfx_path:
            locked_pan = compute_sfx_pan(sfx_key, row.get("speaker", "Narrator"), speaker_pan, lid)
            print(
                f"[Assets] Row {lid} ({row.get('speaker')}, pan={speaker_pan:+.2f}) -> "
                f"SFX: {os.path.basename(sfx_path)} (sfx_pan={locked_pan:+.2f})",
                flush=True,
            )
            await asyncio.to_thread(prepend_sfx_locked, sfx_path, seg_3d, seg_3d, lid, True, locked_pan)
            await asyncio.to_thread(prepend_sfx_locked, sfx_path, seg_mono, seg_mono, lid, False, 0.0)

    d_3d = await asyncio.to_thread(_probe_duration_sync, seg_3d)
    d_mono = await asyncio.to_thread(_probe_duration_sync, seg_mono)
    return idx, seg_3d, seg_mono, d_3d, d_mono


async def main():
    t0 = time.time()
    if not os.path.isfile(STAGED_JSON_PATH):
        raise FileNotFoundError(f"Staged JSON not found: {STAGED_JSON_PATH}")

    with open(STAGED_JSON_PATH, "r", encoding="utf-8") as f:
        chapter_data = json.load(f)

    rows = chapter_data.get("rows", [])
    print(f"[Loaded] '{chapter_data.get('title', 'Chapter 91')}' ({len(rows)} rows) from {STAGED_JSON_PATH}", flush=True)

    os.makedirs(WORK_DIR, exist_ok=True)
    sem = asyncio.Semaphore(6)

    tasks = [process_single_row(i, row, sem) for i, row in enumerate(rows)]
    results = await asyncio.gather(*tasks)
    results.sort(key=lambda x: x[0])

    segs_3d = [r[1] for r in results]
    segs_mono = [r[2] for r in results]
    durs_3d = [r[3] for r in results]
    durs_mono = [r[4] for r in results]

    for label, seg_list, durs, out_path, is_3d in [
        ("Full Ch91 3D Enhanced", segs_3d, durs_3d, OUT_3D_MP3, True),
        ("Full Ch91 Mono Control", segs_mono, durs_mono, OUT_MONO_MP3, False),
    ]:
        manifest = os.path.join(WORK_DIR, f"list_{is_3d}.txt")
        concat_mp3 = os.path.join(WORK_DIR, f"concat_{is_3d}.mp3")
        with open(manifest, "w", encoding="utf-8") as f:
            for s in seg_list:
                f.write(f"file '{os.path.abspath(s).replace(os.sep, '/')}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", manifest, "-c", "copy", concat_mp3],
            check=True,
        )
        mix_sidechained_bgm_and_master(concat_mp3, rows, durs, out_path, stereo=is_3d)
        print(f"[✓] Created {label}: {out_path}", flush=True)

    run_post_master_qc(OUT_3D_MP3)
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    print(f"[Done] Full Chapter 91 comparison completed in {int(time.time() - t0)}s.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())