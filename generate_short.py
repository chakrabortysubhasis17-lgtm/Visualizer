import os
import re
import sys
import json
import time
import math
import random
import shutil
import argparse
import subprocess
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from google import genai
from google.genai import types, errors
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Global Constants & Credentials
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6KJlwWC1fIYVtIs1So-sgN3lw-IMXKo7k82EofcYJ5S8Q")

CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"
BUILD_DIR = "build_shorts_temp"
MAX_STORY_DURATION = 45.0
OUTRO_DURATION = 7.0
MAX_TOTAL_DURATION = 58.5
REQUEST_TIMEOUT = 25


# ---------------------------------------------------------------------------
# Dynamic Structured Schema for 5-Scene Non-Repetitive Storyboard
# ---------------------------------------------------------------------------
class CharacterProfile(BaseModel):
    name_or_role: str = Field(description="Name or narrative role identified from dialogue")
    true_identity: str = Field(description="True nature/archetype deduced from Title + Dialogue (e.g. Transformed Vampire Noble, Blood Tyrant, S-Rank Hunter)")
    visual_appearance: str = Field(description="Specific attire, hair, eye features, materials (lace, velvet, leather, metals)")

class StoryContinuity(BaseModel):
    deduced_universe_genre: str = Field(description="Genre deduced from Title (e.g. LitRPG / Dark Fantasy / Vampire Nobility / Cultivation)")
    deduced_environment: str = Field(description="Specific setting matching the genre and dialogue (e.g. Hunter guild tavern, dark fantasy inn)")
    characters: list[CharacterProfile] = Field(description="Profiles of characters appearing in the snippet")
    lighting_and_atmosphere: str = Field(description="Atmospheric lighting palette (e.g. warm amber lantern glow, deep cinematic shadows)")

class DeducedScene(BaseModel):
    scene_number: int = Field(description="Index: 1, 2, 3, 4, or 5")
    action_summary: str = Field(description="Narrative action in this specific beat")
    camera_framing: str = Field(description="Strict camera angle: 'wide shot', 'medium shot', 'close-up shot', 'low angle', or 'over-the-shoulder'")
    image_prompt: str = Field(
        description=(
            "Ultra-sharp, hyper-detailed 2D anime manhwa prompt (under 140 chars). "
            "Must specify: camera framing, intricate clothing texture (lace, velvet, leather), sharp crisp contours, [setting], razor-sharp eyes. "
            "DO NOT use 'cel shaded' or 'flat colors'. Ensure high texture and distinct camera angles across all 5 scenes."
        )
    )

class UniversalStoryboard(BaseModel):
    continuity: StoryContinuity
    scenes: list[DeducedScene] = Field(description="Exactly 5 sequential, visually diverse, highly textured comic scenes")


def get_ytdlp_cmd() -> list:
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    return [sys.executable, "-m", "yt_dlp"]


def ensure_cinzel_font() -> str:
    if os.path.exists(CINZEL_LOCAL_PATH) and os.path.getsize(CINZEL_LOCAL_PATH) > 10000:
        return CINZEL_LOCAL_PATH
    try:
        resp = requests.get(CINZEL_URL, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(CINZEL_LOCAL_PATH, "wb") as f:
                f.write(resp.content)
            return CINZEL_LOCAL_PATH
    except Exception:
        pass
    for fp in ["C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/timesbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]:
        if os.path.exists(fp):
            return fp
    return "arialbd.ttf"


def parse_timestamp_to_seconds(ts_str: str) -> float:
    ts_str = ts_str.strip()
    parts = ts_str.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def format_seconds_to_hhmmss(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_audio_duration(file_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 0.0


def fetch_online_title(video_url: str) -> str:
    try:
        cmd = get_ytdlp_cmd() + ["--print", "title", "--no-warnings", video_url]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        title = res.stdout.strip()
        if title:
            return title
    except Exception:
        pass
    return "Dark Fantasy Webtoon Story"


# ==================== STAGE 2: STREAM SLICING ====================
def download_stream_slice(video_url: str, start_sec: float, end_sec: float, out_video: str, out_audio: str) -> float:
    print(f"\n[Stage 2] Active URL: {video_url}", flush=True)
    print(f"[Stage 2] Slicing stream from {format_seconds_to_hhmmss(start_sec)} to {format_seconds_to_hhmmss(end_sec)}...", flush=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    start_str = format_seconds_to_hhmmss(start_sec)
    end_str = format_seconds_to_hhmmss(end_sec)
    target_pattern = f"*{start_str}-{end_str}"
    
    raw_segment = os.path.join(BUILD_DIR, "raw_slice.mp4")
    if os.path.exists(raw_segment):
        try: os.remove(raw_segment)
        except OSError: pass

    cmd_dl = get_ytdlp_cmd() + [
        "--download-sections", target_pattern,
        "--force-keyframes-at-cuts",
        "--extractor-args", "youtube:player_client=android,web",
        "--downloader-args", "ffmpeg_i:-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "-f", "bv*[height<=720][ext=mp4]+ba*[ext=m4a]/b[height<=720][ext=mp4]/best",
        "--no-check-certificates",
        "-o", raw_segment,
        video_url
    ]
    subprocess.run(cmd_dl, check=True)

    subprocess.run([
        "ffmpeg", "-y", "-i", raw_segment,
        "-vn", "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1",
        out_audio
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    actual_dur = get_audio_duration(out_audio)
    print(f"[Stage 2] Downloaded slice: {actual_dur:.2f}s audio extracted.", flush=True)
    return actual_dur


# ==================== STAGE 3: 5-SCENE DIVERSE DEDUCTION ====================
def transcribe_audio_to_text(audio_path: str) -> str:
    print("\n[Stage 3] Transcribing audio with Speech Recognition...", flush=True)
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            print(f"[Stage 3] Spoken Dialogue: \"{text}\"", flush=True)
            return text
    except Exception as e:
        print(f"[Stage 3] Speech recognition note: {e}", flush=True)
        return ""


def deduce_scenes_via_gemini(client: genai.Client, story_title: str, raw_transcript: str, total_duration: float) -> list:
    print(f"\n[Stage 3] Deducing 5 Textured Storyboard Scenes with Gemini...", flush=True)
    print(f"     Title: \"{story_title}\"", flush=True)

    system_instruction = """
You are the creative director and storyboard lead for an elite 2D manhwa webtoon adaptation studio.
Your mandate is to deduce an exact FIVE-SCENE (5-Panel) sequential storyboard with rich textures and sharp details.

CRITICAL DIRECTIVES FOR HIGH TEXTURE & RAZOR SHARPNESS:
1. TITLE LORE INTEGRATION:
   - Identify core power systems, character roles, and worldbuilding tags from the Title (e.g. "Blood Tyrant", "S-Rank Hunters", "LitRPG", "Vampire").
   - Character identities must match this lore (e.g. vampires/nobles in ornate gothic dark garments with lace/velvet, masked hunters, etc.).
   - NEVER render modern mundane school uniforms or classrooms unless explicitly stated in the title.
2. STRICT VISUAL DIVERSITY (NO REPETITION ACROSS THE 5 PANELS):
   Every scene MUST use a distinctly different camera angle and subject focus:
   - Scene 1 [Wide Shot]: Wide establishing shot showing tavern architecture, lantern lighting, and characters.
   - Scene 2 [Medium Shot]: Medium shot focusing on the secondary character's surprised reaction or posture.
   - Scene 3 [Mid Shot]: Mid-shot focusing on the central feast table, steam, dangling feet, and food texture.
   - Scene 4 [Close-Up Shot]: Close-up on character's expressive face, sharp red vampire eyes, and detailed hair strands.
   - Scene 5 [Low Angle Shot]: Resolute character pose highlighting ornate gothic skirt texture and silhouette.
3. HIGH TEXTURE PROMPT SPECIFICATIONS:
   - Format: "[camera framing], [characters with fabric textures], [setting with lighting], sharp ink contours, highly detailed, 8k webtoon masterpiece"
   - Keep each prompt under 140 characters.
   - AVOID words like 'cel shaded' or 'flat colors'.
"""

    model_candidates = [
        "gemini-flash-lite-latest",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash"
    ]
    response = None

    for model_name in model_candidates:
        try:
            print(f"     [Gemini] Submitting context to '{model_name}'...", flush=True)
            response = client.models.generate_content(
                model=model_name,
                contents=(
                    f"TITLE: \"{story_title}\"\n\n"
                    f"TRANSCRIPT: \"{raw_transcript}\"\n\n"
                    f"Deduce exactly 5 sequential, non-repetitive comic panels with varied camera angles and rich fabric/surface textures."
                ),
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=UniversalStoryboard,
                    temperature=0.2,
                )
            )
            if response and response.text:
                break
        except Exception as e:
            print(f"     [Gemini] '{model_name}' note: {e}. Trying next model...")
            time.sleep(1)

    base_dur = round(total_duration / 5.0, 2)
    durations = [base_dur] * 4
    durations.append(round(total_duration - sum(durations), 2))

    scenes = []
    if response and response.text:
        try:
            parsed = json.loads(response.text)
            continuity = parsed.get("continuity", {})
            genre = continuity.get("deduced_universe_genre", "Fantasy LitRPG")
            env = continuity.get("deduced_environment", "Fantasy Tavern")
            print(f"\n=======================================================")
            print(f"✅ DEDUCED GENRE       : {genre}")
            print(f"✅ DEDUCED SETTING     : {env}")
            print(f"✅ CHARACTER PROFILES  :")
            for ch in continuity.get("characters", []):
                print(f"   • {ch.get('name_or_role')}: {ch.get('true_identity')} | Attire: {ch.get('visual_appearance')}")
            print(f"=======================================================\n")

            for i, sc in enumerate(parsed.get("scenes", [])[:5]):
                scenes.append({
                    "id": i + 1,
                    "action": sc.get("action_summary"),
                    "framing": sc.get("camera_framing", "medium shot"),
                    "duration": durations[i],
                    "prompt": sc.get("image_prompt")
                })
        except Exception as e:
            print(f"     [Gemini] Parse error: {e}. Using algorithmic fallback.", flush=True)

    if len(scenes) < 5:
        fallbacks = [
            ("wide shot", "Establishing the characters and tavern interior", "wide shot, gothic tavern interior with amber lantern lighting, rich dark wood textures, sharp crisp ink contours, 8k webtoon"),
            ("medium shot", "Secondary character reaction and dialogue exchange", "medium shot, bewildered waiter in leather vest and linen shirt, surprised expression, sharp crisp ink contours, 8k webtoon"),
            ("mid shot", "Focus on the central feast table and physical action", "mid shot, wooden feast table laden with roasted meats and steam, small dangling feet beneath, sharp crisp ink contours, 8k webtoon"),
            ("close-up shot", "Close-up on character's expressive face and eyes", "close-up shot, young vampire girl with glowing sharp red eyes and intricate silver hair strands, sharp crisp ink contours, 8k webtoon"),
            ("low angle shot", "Resolute character pose highlighting attire", "low angle shot, resolute vampire girl posing in ornate gothic velvet dress with heavy black lace texture, sharp crisp ink contours, 8k webtoon")
        ]
        scenes = []
        for i, (framing, act, p) in enumerate(fallbacks, 1):
            scenes.append({
                "id": i,
                "action": act,
                "framing": framing,
                "duration": durations[i - 1],
                "prompt": p
            })

    print("----------------------------------------------------------------------------------")
    print("📖 Final Deduced 5-Scene Storyboard (Rich Texture & High Sharpness):")
    for sc in scenes:
        print(f"\n   [Scene {sc['id']}/5] [{sc['framing'].upper()}]: \"{sc['action']}\"")
        print(f"   [Prompt]: \"{sc['prompt']}\"")
    print("----------------------------------------------------------------------------------\n")
    return scenes


# ==================== STAGE 4: DUAL-BAND TEXTURE & SHARPNESS ====================
def upscale_and_sharpen_vertical(img: Image.Image) -> Image.Image:
    """Scales to native 1080x1920 using Lanczos with dual-band micro-texture and edge sharpening."""
    target_w, target_h = 1080, 1920
    target_ratio = target_w / target_h
    img_w, img_h = img.size
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        new_w = int(img_h * target_ratio)
        left = (img_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, img_h))
    else:
        new_h = int(img_w / target_ratio)
        top = (img_h - new_h) // 2
        img = img.crop((0, top, img_w, top + new_h))

    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.DETAIL)

    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=170, threshold=0))
    img = img.filter(ImageFilter.UnsharpMask(radius=3.0, percent=115, threshold=1))

    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.09)
    img = ImageEnhance.Color(img).enhance(1.05)

    return img


def format_frame_with_blurred_bg(raw_img_path: str, out_path: str):
    src = Image.open(raw_img_path).convert("RGBA")
    sw, sh = src.size

    bg = upscale_and_sharpen_vertical(src)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=25))

    target_fg_w = 1080
    target_fg_h = int(sh * (target_fg_w / sw))
    fg = src.resize((target_fg_w, target_fg_h), Image.Resampling.LANCZOS)

    y_pos = (1920 - target_fg_h) // 2
    bg.paste(fg, (0, y_pos), fg)
    bg.convert("RGB").save(out_path, "PNG")


def execute_cooldown_timer(wait_seconds: int, reason: str = "Backoff pause"):
    for remaining in range(wait_seconds, 0, -1):
        print(f"\r     [{reason}] Retrying in {remaining:2d}s...", end="", flush=True)
        time.sleep(1)
    print(f"\r     [{reason}] {wait_seconds}s pause elapsed. Firing request...             ", flush=True)


def fetch_comic_artwork(prompt: str, out_path: str, raw_video_path: str, time_offset: float, scene_index: int):
    clean_p = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt)[:140].strip()
    
    full_prompt = (
        f"{clean_p}, sharp detailed anime eyes, clear pupil and iris, "
        f"intricate fabric texture, finely detailed hair, crisp clean ink linework, "
        f"subsurface lighting, masterpiece 2D anime manhwa, sharp focus, 8k uhd"
    )
    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(10000, 9999999)

    # 40 seconds initial wait, then +5s increments up to 1 minute 30 seconds (90s total)
    # 40 + (10 * 5) = 90 seconds (11 attempts)
    if scene_index == 1:
        progressive_delays = [0, 40] + [5] * 10
    else:
        progressive_delays = [40] + [5] * 10

    for attempt, delay_sec in enumerate(progressive_delays, 1):
        if delay_sec > 0:
            reason_label = f"Cooldown {delay_sec}s (Attempt {attempt}/{len(progressive_delays)})"
            execute_cooldown_timer(delay_sec, reason=reason_label)

        # Standard free Pollinations endpoint without restrictive parameters
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&seed={seed + attempt}"

        try:
            print(f"     [Image Engine] Polling Pollinations 720p HD (Attempt {attempt}/{len(progressive_delays)}, timeout={REQUEST_TIMEOUT}s)...", flush=True)
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=REQUEST_TIMEOUT
            )

            if resp.status_code == 200 and len(resp.content) > 10000:
                raw_temp = out_path + ".tmp.jpg"
                with open(raw_temp, "wb") as f:
                    f.write(resp.content)
                base = Image.open(raw_temp).convert("RGBA")
                bw, bh = base.size
                # Cleanly crop bottom 5.5% border to remove watermark
                base = base.crop((0, 0, bw, bh - int(bh * 0.055)))
                base = upscale_and_sharpen_vertical(base)
                base.convert("RGB").save(out_path, "PNG")
                try: os.remove(raw_temp)
                except OSError: pass
                print(f"     [Image Engine] Succeeded on Attempt {attempt}! Watermark stripped & rendered to 1080x1920 HD ({len(resp.content)} bytes).", flush=True)
                return True
            else:
                print(f"     [Image Engine] Attempt {attempt} returned HTTP {resp.status_code}. Pausing before next attempt...", flush=True)
        except requests.exceptions.Timeout:
            print(f"     [Image Engine] Attempt {attempt} timed out after {REQUEST_TIMEOUT}s. Pausing before next attempt...", flush=True)
        except Exception as e:
            print(f"     [Image Engine] Attempt {attempt} error: {e}. Pausing before next attempt...", flush=True)

    # Fallback to source video frame only after exhausting the full 1m 30s schedule
    print(f"     [Image Engine] All attempts up to 1m 30s exhausted. Slicing native frame from video slice at {time_offset:.2f}s...", flush=True)
    raw_frame = out_path + ".raw.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{time_offset:.2f}",
        "-i", raw_video_path, "-vframes", "1", raw_frame
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(raw_frame) and os.path.getsize(raw_frame) > 5000:
        format_frame_with_blurred_bg(raw_frame, out_path)
        try: os.remove(raw_frame)
        except OSError: pass
        print("     [Image Engine] Sourced frame styled into 9:16 vertical comic layout.", flush=True)
        return False

    fallback = Image.new("RGB", (1080, 1920), (35, 45, 60))
    fallback.save(out_path, "PNG")
    return False


def apply_comic_book_styling(image_path: str):
    base = Image.open(image_path).convert("RGBA")
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(220):
        alpha = int(120 * (1 - (y / 220)))
        draw.line([(0, y), (width, y)], fill=(12, 14, 18, alpha))

    vig_start = int(height * 0.76)
    for y in range(vig_start, height):
        alpha = int(150 * (((y - vig_start) / (height - vig_start)) ** 1.3))
        draw.line([(0, y), (width, y)], fill=(12, 14, 18, alpha))

    draw.rectangle([(8, 8), (width - 9, height - 9)], outline=(255, 255, 255, 40), width=4)
    base = Image.alpha_composite(base, overlay)

    c_draw = ImageDraw.Draw(base)
    wx, wy = 80, 120
    c_draw.ellipse([(wx - 26, wy - 26), (wx + 26, wy + 26)], fill=(210, 150, 40, 255), outline=(255, 235, 180, 255), width=2)
    
    font_path = ensure_cinzel_font()
    star_font = ImageFont.truetype("arial.ttf", 26)
    c_draw.text((wx - 10, wy - 16), "✦", fill=(255, 255, 255, 255), font=star_font)
    
    brand_font = ImageFont.truetype(font_path, 42)
    handle_font = ImageFont.truetype("arialbd.ttf", 24)
    c_draw.text((wx + 42, wy - 24), "Being a Bong", fill=(255, 255, 255), font=brand_font)
    c_draw.text((wx + 44, wy + 20), "@beingabong", fill=(255, 215, 120, 255), font=handle_font)

    base.convert("RGB").save(image_path, "PNG")


def render_static_scene(image_path: str, duration: float, out_video: str):
    fps = 30
    total_frames = max(1, int(round(duration * fps)))

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", str(fps),
        "-t", f"{duration:.3f}",
        "-i", image_path,
        "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "16",
        "-threads", "4",
        "-pix_fmt", "yuv420p",
        "-frames:v", str(total_frames),
        out_video
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


# ==================== STAGE 5: OUTRO WITH LIKE & BELL ICONS ====================
def draw_like_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int = 50, fill_color=(255, 255, 255)):
    draw.rounded_rectangle([(cx - size, cy - 10), (cx - size + 16, cy + 30)], radius=4, fill=fill_color)
    draw.rounded_rectangle([(cx - size + 22, cy - 5), (cx + 25, cy + 30)], radius=8, fill=fill_color)
    thumb_points = [
        (cx - size + 22, cy - 5),
        (cx - size + 26, cy - 35),
        (cx - size + 42, cy - 38),
        (cx - size + 46, cy - 5)
    ]
    draw.polygon(thumb_points, fill=fill_color)


def draw_bell_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int = 50, fill_color=(255, 255, 255)):
    draw.ellipse([(cx - 8, cy - size), (cx + 8, cy - size + 16)], outline=fill_color, width=4)
    body_points = [
        (cx - 15, cy - size + 14),
        (cx + 15, cy - size + 14),
        (cx + 28, cy + 10),
        (cx + 38, cy + 20),
        (cx - 38, cy + 20),
        (cx - 28, cy + 10)
    ]
    draw.polygon(body_points, fill=fill_color)
    draw.rounded_rectangle([(cx - 40, cy + 18), (cx + 40, cy + 26)], radius=4, fill=fill_color)
    draw.ellipse([(cx - 10, cy + 24), (cx + 10, cy + 38)], fill=fill_color)


def create_shorts_outro_card(out_path: str):
    print("\n[Stage 5] Generating YouTube Shorts Outro Card with Like & Bell icons...", flush=True)
    card = Image.new("RGB", (1080, 1920), (14, 18, 24))
    draw = ImageDraw.Draw(card)
    font_path = ensure_cinzel_font()

    head_font = ImageFont.truetype(font_path, 54)
    sub_font = ImageFont.truetype("arialbd.ttf", 36)
    cta_font = ImageFont.truetype("arialbd.ttf", 40)
    pointer_font = ImageFont.truetype("arialbd.ttf", 46)

    # 1. Header Channel Brand
    draw.text((280, 320), "Being a Bong", fill=(255, 255, 255), font=head_font)
    draw.text((390, 395), "@beingabong", fill=(255, 215, 120), font=sub_font)

    # 2. Like Button Card
    draw.rounded_rectangle([(160, 560), (920, 710)], radius=30, fill=(28, 36, 48), outline=(255, 75, 75), width=3)
    draw_like_icon(draw, cx=280, cy=635, size=46, fill_color=(255, 80, 80))
    draw.text((360, 610), "LIKE THE VIDEO", fill=(255, 255, 255), font=cta_font)

    # 3. Subscribe & Bell Button Card
    draw.rounded_rectangle([(160, 760), (920, 910)], radius=30, fill=(28, 36, 48), outline=(255, 215, 80), width=3)
    draw_bell_icon(draw, cx=280, cy=835, size=46, fill_color=(255, 215, 80))
    draw.text((360, 810), "SUBSCRIBE & RING BELL", fill=(255, 255, 255), font=cta_font)

    # 4. Mobile Related Video Pointer Box
    draw.rounded_rectangle([(100, 1380), (980, 1680)], radius=25, fill=(20, 26, 36), outline=(80, 180, 255), width=4)
    
    t1 = "LISTEN TO FULL 50-CHAPTER MARATHON"
    t2 = "CLICK RELATED VIDEO BELOW ⬇"
    
    b1 = draw.textbbox((0, 0), t1, font=sub_font)
    draw.text((540 - (b1[2] - b1[0]) // 2, 1440), t1, fill=(255, 235, 140), font=sub_font)

    b2 = draw.textbbox((0, 0), t2, font=pointer_font)
    draw.text((540 - (b2[2] - b2[0]) // 2, 1530), t2, fill=(80, 210, 255), font=pointer_font)

    card.save(out_path, "PNG")
    print(f"[Stage 5] Outro card generated: '{out_path}'", flush=True)


# ==================== STAGE 6: MASTER ASSEMBLY ====================
def assemble_final_short(video_segments: list, audio_track: str, total_duration: float, out_mp4: str):
    print("\n[Stage 6] Assembling final vertical video with mobile DSP audio...", flush=True)
    manifest = os.path.join(BUILD_DIR, "v_list.txt")
    with open(manifest, "w", encoding="utf-8") as f:
        for vs in video_segments:
            f.write(f"file '{os.path.abspath(vs).replace(os.sep, '/')}'\n")

    full_video_track = os.path.join(BUILD_DIR, "v_full.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest, "-c", "copy", full_video_track], check=True)

    total_allowed = min(total_duration, MAX_TOTAL_DURATION)
    
    cmd_mux = [
        "ffmpeg", "-y",
        "-i", full_video_track,
        "-i", audio_track,
        "-t", f"{total_allowed:.2f}",
        "-af", "highpass=f=85,equalizer=f=3200:t=q:w=1.5:g=2.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50,loudnorm=I=-14:TP=-1.5:LRA=7,apad",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        out_mp4
    ]
    subprocess.run(cmd_mux, check=True)

    final_dur = get_audio_duration(out_mp4)
    print(f"\n=======================================================")
    print(f"🎉 SUCCESS! 5-Scene Short Rendered: {out_mp4}")
    print(f"⏱️ Final Runtime: {final_dur:.2f}s (Strictly under 59s)")
    print(f"🎨 Storyboard: 5 Unwatermarked Textured Panels + Outro Card")
    print(f"📐 Resolution: 1080x1920 (9:16 Vertical Shorts Standard)")
    print(f"=======================================================\n")


# ==================== MAIN CLI ENTRY POINT ====================
def main():
    parser = argparse.ArgumentParser(description="Universal 5-Scene Comic Shorts Generator with True Progressive Backoff")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--timeframe", required=True, help="Timeframe window (e.g., 00:50:38-00:51:13)")
    parser.add_argument("--title", default="", help="Novel or video title for context lore deduction")
    parser.add_argument("--output", default="short_episode.mp4", help="Output filename")
    args = parser.parse_args()

    parts = args.timeframe.strip().split("-")
    if len(parts) != 2:
        print("Error: Timeframe must be in format START-END (e.g. 00:50:38-00:51:13)")
        sys.exit(1)

    t_start = parse_timestamp_to_seconds(parts[0])
    t_end = parse_timestamp_to_seconds(parts[1])
    req_dur = t_end - t_start

    if req_dur <= 0:
        print("Error: End time must be greater than start time.")
        sys.exit(1)

    story_dur = min(req_dur, MAX_STORY_DURATION)
    t_end = t_start + story_dur

    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    os.makedirs(BUILD_DIR, exist_ok=True)

    raw_audio = os.path.join(BUILD_DIR, "clip_audio.wav")
    raw_video = os.path.join(BUILD_DIR, "raw_slice.mp4")

    resolved_title = args.title.strip() if args.title.strip() else fetch_online_title(args.url)
    print(f"\n[Context Engine] Using Story Title: \"{resolved_title}\"", flush=True)

    # Initialize Gemini Client
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Stage 2: Slicing Stream
    actual_story_dur = download_stream_slice(args.url, t_start, t_end, raw_video, raw_audio)

    # Stage 3: Transcribe Speech & Deduce 5 Non-Repetitive Scenes via Gemini
    transcript = transcribe_audio_to_text(raw_audio)
    scenes = deduce_scenes_via_gemini(client, resolved_title, transcript, actual_story_dur)

    # Stage 4: High-Res Image Synthesis with True Progressive Backoff & Static Scene Cuts
    video_segments = []
    print("\n[Stage 4] Generating and assembling 5 unwatermarked comic panels with 40s+5s backoff...", flush=True)
    for idx, sc in enumerate(scenes, 1):
        print(f"\n  -> Scene {idx}/5: [{sc['framing'].upper()}] ({sc['duration']:.2f}s)...", flush=True)
        print(f"     Action: \"{sc['action']}\"")
        print(f"     Prompt: \"{sc['prompt']}\"")
        img_path = os.path.join(BUILD_DIR, f"scene_art_{idx}.png")
        
        time_offset = (idx - 1) * (actual_story_dur / 5.0) + 0.5
        fetch_comic_artwork(sc["prompt"], img_path, raw_video, time_offset, scene_index=idx)
        apply_comic_book_styling(img_path)

        seg_vid = os.path.join(BUILD_DIR, f"scene_cut_{idx}.mp4")
        render_static_scene(img_path, sc["duration"], seg_vid)
        video_segments.append(seg_vid)

    # Stage 5: Outro Card
    outro_card = os.path.join(BUILD_DIR, "outro_card.png")
    create_shorts_outro_card(outro_card)
    
    outro_anim = os.path.join(BUILD_DIR, "outro_cut.mp4")
    render_static_scene(outro_card, OUTRO_DURATION, outro_anim)
    video_segments.append(outro_anim)

    # Stage 6: Mux & Audio Master
    total_short_duration = actual_story_dur + OUTRO_DURATION
    assemble_final_short(video_segments, raw_audio, total_short_duration, args.output)

    try:
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
