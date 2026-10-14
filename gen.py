import os
import re
import json
import wave
import struct
import asyncio
import textwrap
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from mutagen.mp3 import MP3
import imageio_ffmpeg

# -------------------------------------------------------------------------
# 1. Canvas, Pipeline & File Configuration
# -------------------------------------------------------------------------
SCRIPT_FILE = r"D:\Projects\visualer\gen.txt"

WIDTH, HEIGHT = 1920, 1080
FPS = 12                     # 12 FPS: smooth UI border pulses & fast rendering
SAMPLE_RATE = 48000          # 48kHz stereo: zero A/V clock drift
CONVERSATIONAL_PAUSE = 1.5   # Natural 1.5s human breath between turns (no dead air)

# Pagination Limit: max lines that fit inside the sidebar card without collision
MAX_LINES_PER_PAGE = 18
TEXT_WRAP_WIDTH = 38

OUTPUT_DIR = "meeting_assets_full_60min"
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
TEMP_VIDEO = os.path.join(OUTPUT_DIR, "temp_video.mp4")
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "gelatin_project_60min_final.mp4")
MANIFEST_PATH = os.path.join(OUTPUT_DIR, "manifest_60min.json")
MASTER_AUDIO = os.path.join(OUTPUT_DIR, "master_audio_60min.aac")

os.makedirs(AUDIO_DIR, exist_ok=True)

# -------------------------------------------------------------------------
# 2. UI Layout Geometry: Left 2x3 Grid (1400px) + Right Sidebar (520px)
# -------------------------------------------------------------------------
LEFT_CANVAS_W = 1400
SIDEBAR_X = 1400
SIDEBAR_W = 520

PARTICIPANTS = {
    "Vikram Malhotra":        {"grid": (0, 0), "label": "Vikram Malhotra (Lead)"},
    "Ananya Iyer":            {"grid": (0, 1), "label": "Ananya Iyer (Frontend)"},
    "Karthik Nair":           {"grid": (0, 2), "label": "Karthik Nair (Data & DB)"},
    "Lukas Weber":            {"grid": (1, 0), "label": "Lukas Weber (DevOps)"},
    "Fiona MacLeod":          {"grid": (1, 1), "label": "Fiona MacLeod (QA & Arch)"},
    "Subhashish Chakraborty": {"grid": (1, 2), "label": "Subhashish Chakraborty (Anchor)"}
}

TILE_W, TILE_H = 410, 380
X_COORDS = [45, 495, 945]
Y_COORDS = [90, 520]

VOICE_CONFIG = {
    "Vikram Malhotra":        {"voice": "en-IN-PrabhatNeural", "rate": "+0%", "pitch": "+0Hz"},
    "Ananya Iyer":            {"voice": "en-IN-NeerjaNeural",  "rate": "+0%", "pitch": "+0Hz"},
    "Karthik Nair":           {"voice": "en-IN-PrabhatNeural", "rate": "-3%", "pitch": "+0Hz"},
    "Lukas Weber":            {"voice": "de-DE-FlorianMultilingualNeural", "rate": "+0%", "pitch": "+0Hz"},
    "Fiona MacLeod":          {"voice": "en-GB-SoniaNeural",   "rate": "+0%", "pitch": "+0Hz"},
    "Subhashish Chakraborty": {"voice": None, "rate": None, "pitch": None}  # ZERO AUDIO / SILENCE
}

# -------------------------------------------------------------------------
# 3. Dynamic Script Parser (Reads directly from gen.txt)
# -------------------------------------------------------------------------
def parse_time_seconds(time_str):
    """Converts MM:SS or HH:MM:SS to seconds."""
    parts = [int(p) for p in time_str.strip().split(':')]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

def load_dialogues_from_txt(filepath):
    """Parses all 44 dialogues, speakers, and timing windows from gen.txt."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source script file not found at: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'(?=\[\d+\])', content)
    dialogues = []

    for b in blocks:
        b = b.strip()
        if not b.startswith('['):
            continue

        header_match = re.search(r'\[(\d+)\]\s*([\d:]+\s*[–-]\s*[\d:]+)\s*\|\s*([^\n\r]+)', b)
        text_match = re.search(r'"([^"]+)"', b, re.DOTALL)

        if not (header_match and text_match):
            continue

        item_id_num = int(header_match.group(1))
        time_range = header_match.group(2)
        raw_speaker = header_match.group(3)
        dialogue_text = " ".join(text_match.group(1).split())

        # Match to participant identity
        speaker = None
        for known_name in PARTICIPANTS.keys():
            if known_name in raw_speaker:
                speaker = known_name
                break

        if not speaker:
            continue

        # Extract duration from timestamp range
        range_parts = re.split(r'[–-]', time_range)
        duration_window = 0.0
        if len(range_parts) == 2:
            start_s = parse_time_seconds(range_parts[0])
            end_s = parse_time_seconds(range_parts[1])
            duration_window = max(0.0, float(end_s - start_s))

        dialogues.append({
            "id": f"turn_{item_id_num:02d}_{speaker.split()[0].lower()}",
            "turn_number": item_id_num,
            "speaker": speaker,
            "text": dialogue_text,
            "duration_window": duration_window,
            "time_range": time_range
        })

    print(f"Loaded {len(dialogues)} dialogue entries from '{filepath}'.")
    return dialogues

# -------------------------------------------------------------------------
# 4. Helper Functions: Fonts, Audio & Silence Processing
# -------------------------------------------------------------------------
def get_font(size):
    font_names = ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            continue
    return ImageFont.load_default()

FONT_HEADER = get_font(22)
FONT_NAME = get_font(18)
FONT_STATUS = get_font(15)
FONT_SIDEBAR_TITLE = get_font(20)
FONT_SIDEBAR_SUB = get_font(16)
FONT_TRANSCRIPT = get_font(20)

def generate_silent_wav(duration, out_wav_path):
    """Generates pure mathematical silence (0 dB) at 48kHz stereo."""
    with wave.open(out_wav_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = int(round(duration * SAMPLE_RATE))
        wf.writeframes(struct.pack('<h', 0) * (frames * 2))

def create_padded_audio(raw_audio_path, pause_sec, out_wav_path):
    """Appends exactly pause_sec (1.5s) of natural tail silence at 48kHz stereo."""
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y",
        "-i", raw_audio_path,
        "-af", f"apad=pad_dur={pause_sec}",
        "-ar", str(SAMPLE_RATE),
        "-ac", "2",
        out_wav_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# -------------------------------------------------------------------------
# 5. Caption Pagination & UI Canvas Pre-rendering
# -------------------------------------------------------------------------
def paginate_text(text, max_lines=MAX_LINES_PER_PAGE, width=TEXT_WRAP_WIDTH):
    """Wraps text into sequential pages that fit cleanly inside the sidebar card."""
    wrapped_lines = textwrap.wrap(text, width=width)
    pages = []
    for i in range(0, len(wrapped_lines), max_lines):
        chunk = wrapped_lines[i : i + max_lines]
        word_count = sum(len(line.split()) for line in chunk)
        pages.append({
            "lines": chunk,
            "word_count": max(1, word_count)
        })
    return pages

def create_base_canvas():
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(18, 19, 21))
    draw = ImageDraw.Draw(img)

    # Top Navigation Bar
    draw.rectangle([(0, 0), (WIDTH, 48)], fill=(24, 25, 28))
    draw.text((45, 12), "Gelatin Project — Initiation Call | L&T Finance", fill=(215, 220, 230), font=FONT_HEADER)
    draw.ellipse([(LEFT_CANVAS_W - 80, 18), (LEFT_CANVAS_W - 64, 34)], fill=(235, 60, 60))
    draw.text((LEFT_CANVAS_W - 55, 14), "REC", fill=(235, 60, 60), font=FONT_STATUS)

    # 6 Participant Tiles on Left Grid
    for _, info in PARTICIPANTS.items():
        row, col = info["grid"]
        x, y = X_COORDS[col], Y_COORDS[row]

        draw.rounded_rectangle([(x, y), (x + TILE_W, y + TILE_H)], radius=12, fill=(30, 32, 36), outline=(42, 45, 52), width=1)

        # Silhouette Avatar
        cx, cy = x + (TILE_W // 2), y + (TILE_H // 2) - 15
        draw.ellipse([(cx - 40, cy - 45), (cx + 40, cy + 35)], fill=(50, 53, 60))
        draw.chord([(cx - 80, cy + 10), (cx + 80, cy + 120)], start=180, end=0, fill=(50, 53, 60))

        # Bottom Tag
        draw.rectangle([(x + 10, y + TILE_H - 42), (x + TILE_W - 10, y + TILE_H - 10)], fill=(22, 23, 26))
        draw.text((x + 18, y + TILE_H - 36), info["label"], fill=(225, 230, 240), font=FONT_NAME)
        draw.text((x + TILE_W - 80, y + TILE_H - 34), "🔇 Muted", fill=(120, 125, 135), font=FONT_STATUS)

    # Right Sidebar Container
    draw.rectangle([(SIDEBAR_X, 0), (WIDTH, HEIGHT)], fill=(23, 24, 28))
    draw.line([(SIDEBAR_X, 0), (SIDEBAR_X, HEIGHT)], fill=(38, 40, 46), width=2)
    draw.rectangle([(SIDEBAR_X, 0), (WIDTH, 48)], fill=(28, 30, 35))
    draw.text((SIDEBAR_X + 25, 14), "Meeting Transcript & Captions", fill=(230, 235, 245), font=FONT_SIDEBAR_TITLE)

    return img

BASE_CANVAS = create_base_canvas()

def render_active_frame(active_speaker, lines_to_draw, anim_phase, is_speaking=True, page_info=""):
    """
    Renders active speaker indicator on their tile and outputs ONLY the current page of lines
    so text never overflows the card.
    """
    frame = BASE_CANVAS.copy()
    draw = ImageDraw.Draw(frame)

    info = PARTICIPANTS[active_speaker]
    row, col = info["grid"]
    x, y = X_COORDS[col], Y_COORDS[row]

    if is_speaking:
        border_pulse = 3 + int(2 * np.sin(anim_phase * np.pi))
        draw.rounded_rectangle([(x, y), (x + TILE_W, y + TILE_H)], radius=12, outline=(0, 170, 255), width=border_pulse)

        if active_speaker == "Subhashish Chakraborty":
            draw.rounded_rectangle([(x + TILE_W - 145, y + TILE_H - 38), (x + TILE_W - 15, y + TILE_H - 12)], radius=6, fill=(0, 120, 215))
            draw.text((x + TILE_W - 135, y + TILE_H - 34), "💬 CAPTION ON", fill=(255, 255, 255), font=FONT_STATUS)
        else:
            draw.rounded_rectangle([(x + TILE_W - 130, y + TILE_H - 38), (x + TILE_W - 15, y + TILE_H - 12)], radius=6, fill=(16, 140, 75))
            draw.text((x + TILE_W - 120, y + TILE_H - 34), "🔊 SPEAKING", fill=(255, 255, 255), font=FONT_STATUS)

    # Render Transcript Card on Right Sidebar (Only for active speaker)
    card_x = SIDEBAR_X + 20
    card_w = SIDEBAR_W - 40
    draw.rounded_rectangle([(card_x, 70), (card_x + card_w, 980)], radius=12, fill=(29, 31, 37), outline=(45, 48, 56), width=1)

    is_subhashish = (active_speaker == "Subhashish Chakraborty")
    tag_color = (0, 195, 255) if is_subhashish else (120, 220, 140)
    tag_prefix = "💬 Text Stream (Silent)" if is_subhashish else "🎙 Active Audio Stream"
    if page_info:
        tag_prefix += f" • {page_info}"

    draw.text((card_x + 20, 95), active_speaker, fill=(245, 248, 255), font=FONT_SIDEBAR_TITLE)
    draw.text((card_x + 20, 130), tag_prefix, fill=tag_color, font=FONT_SIDEBAR_SUB)
    draw.line([(card_x + 20, 160), (card_x + card_w - 20, 160)], fill=(45, 48, 56), width=1)

    line_y = 185
    for line in lines_to_draw:
        draw.text((card_x + 20, line_y), line, fill=(220, 225, 235), font=FONT_TRANSCRIPT)
        line_y += 34  # Clean spacing that never hits the card bottom

    return frame.tobytes()

# -------------------------------------------------------------------------
# 6. Audio Preparation Pipeline
# -------------------------------------------------------------------------
async def prepare_calibrated_audio(dialogues):
    print("\n[STEP 1/3] Generating Audio Tracks & Natural 1.5s Conversational Gaps...")
    print("=" * 75)

    manifest = []

    for idx, item in enumerate(dialogues):
        speaker = item["speaker"]
        cfg = VOICE_CONFIG[speaker]
        entry = {
            "id": item["id"],
            "turn_number": item["turn_number"],
            "speaker": speaker,
            "text": item["text"],
            "speech_duration": 0.0,
            "pause_duration": 0.0,
            "total_duration": 0.0,
            "audio_file": None,
            "is_caption_only": False
        }

        final_wav = os.path.join(AUDIO_DIR, f"{item['id']}_natural_48k.wav")

        if cfg["voice"] is None:
            # Subhashish: Caption-only silent turn (matched to script window or reading time)
            reading_dur = item["duration_window"] if item["duration_window"] > 0 else max(8.0, round(len(item["text"].split()) / 2.6, 1))
            generate_silent_wav(reading_dur, final_wav)

            entry["speech_duration"] = reading_dur
            entry["pause_duration"] = 0.5  # Minimal transition buffer
            entry["total_duration"] = reading_dur + 0.5
            entry["is_caption_only"] = True
            print(f"[{idx+1}/{len(dialogues)}] {speaker} -> Caption Silence: {reading_dur:.2f}s (No Audio)")
        else:
            raw_mp3 = os.path.join(AUDIO_DIR, f"{item['id']}_raw.mp3")
            if not os.path.exists(raw_mp3):
                import edge_tts
                comm = edge_tts.Communicate(text=item["text"], voice=cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"])
                await comm.save(raw_mp3)

            # Read exact spoken duration
            mp3_info = MP3(raw_mp3)
            speech_dur = round(mp3_info.info.length, 2)

            # Append ONLY a natural 1.5s conversational pause (no artificial dead air)
            create_padded_audio(raw_mp3, CONVERSATIONAL_PAUSE, final_wav)

            entry["speech_duration"] = speech_dur
            entry["pause_duration"] = CONVERSATIONAL_PAUSE
            entry["total_duration"] = speech_dur + CONVERSATIONAL_PAUSE
            print(f"[{idx+1}/{len(dialogues)}] {speaker} -> Spoken Speech: {speech_dur:.2f}s + 1.5s breath")

        entry["audio_file"] = os.path.abspath(final_wav)
        manifest.append(entry)

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)

    total_meeting_sec = sum(x["total_duration"] for x in manifest)
    print("-" * 75)
    print(f"Total Meeting Duration: {total_meeting_sec:.1f}s ({total_meeting_sec/60:.2f} mins)")
    print(f"Conversational Gaps:    1.5s natural breath between turns (ZERO DEAD AIR)")
    print("-" * 75)

    print("\n[STEP 2/3] Compiling Master 48kHz Audio Track...")
    concat_list = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for item in manifest:
            f.write(f"file '{item['audio_file'].replace('\\', '/')}'\n")

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c:a", "aac", "-b:a", "192k", MASTER_AUDIO
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"Master audio track compiled at: {MASTER_AUDIO}")
    return manifest

# -------------------------------------------------------------------------
# 7. Video Rendering with Speech-to-Caption Synchronization
# -------------------------------------------------------------------------
def render_synced_video(manifest):
    print("\n[STEP 3/3] Streaming Video Frames with Speech-to-Caption Sync...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # Stage 1: Pipe raw video frames directly to temp MP4
    cmd_video = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        TEMP_VIDEO
    ]

    process = subprocess.Popen(cmd_video, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    total_segments = len(manifest)

    for idx, item in enumerate(manifest):
        speaker = item["speaker"]
        speech_dur = item["speech_duration"]
        pause_dur = item["pause_duration"]
        text = item["text"]
        is_caption_only = item["is_caption_only"]

        pages = paginate_text(text, max_lines=MAX_LINES_PER_PAGE, width=TEXT_WRAP_WIDTH)
        num_pages = len(pages)
        total_words = sum(p["word_count"] for p in pages)

        speech_frames = int(round(speech_dur * FPS))
        pause_frames = int(round(pause_dur * FPS))

        print(f"Rendering turn [{idx+1}/{total_segments}]: {speaker} ({speech_dur}s speech | {num_pages} page(s))")

        # Distribute frames proportionally across pages based on word count
        frames_spoken_so_far = 0
        for page_idx, page in enumerate(pages):
            if page_idx == num_pages - 1:
                page_frames = speech_frames - frames_spoken_so_far
            else:
                page_frames = int(round(speech_frames * (page["word_count"] / total_words)))
            frames_spoken_so_far += page_frames

            page_label = f"Page {page_idx + 1}/{num_pages}" if num_pages > 1 else ""

            # Pre-render 4 looping phase buffers
            page_buffers = [
                render_active_frame(speaker, page["lines"], phase, is_speaking=True, page_info=page_label)
                for phase in [0.0, 0.25, 0.5, 0.75]
            ]

            for f in range(page_frames):
                process.stdin.write(page_buffers[f % 4])

        # Stream natural 1.5s breath pause with idle speaker tile
        if pause_frames > 0 and not is_caption_only:
            last_page = pages[-1]
            page_label = f"Page {num_pages}/{num_pages}" if num_pages > 1 else ""
            idle_buffer = render_active_frame(speaker, last_page["lines"], 0.0, is_speaking=False, page_info=page_label)
            for _ in range(pause_frames):
                process.stdin.write(idle_buffer)

    process.stdin.close()
    process.wait()
    print("Raw video generation completed.")

    # Stage 2: Mux video with master audio
    print("\nMuxing video with master audio track...")
    cmd_mux = [
        ffmpeg_exe, "-y",
        "-i", TEMP_VIDEO,
        "-i", MASTER_AUDIO,
        "-c:v", "copy",
        "-c:a", "copy",
        "-shortest",
        OUTPUT_VIDEO
    ]
    subprocess.run(cmd_mux, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)

    print("\n" + "=" * 75)
    print(f" Meeting Video Generated Successfully!")
    print(f" Output Location: {os.path.abspath(OUTPUT_VIDEO)}")
    print("=" * 75)

# -------------------------------------------------------------------------
# 8. Main Execution
# -------------------------------------------------------------------------
if __name__ == "__main__":
    dialogue_manifest = load_dialogues_from_txt(SCRIPT_FILE)
    audio_manifest = asyncio.run(prepare_calibrated_audio(dialogue_manifest))
    render_synced_video(audio_manifest)
