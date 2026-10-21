"""
================================================================================
BEINGABONG MASTER CATALOG REEL GENERATOR (FLICKER-FREE + SMOOTH SWIPE)
================================================================================
"""

import os
import glob
import math
import asyncio
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# ------------------------------------------------------------------------------
# 1. CONFIGURATION & SCENES
# ------------------------------------------------------------------------------
THUMBNAILS_DIR = "downloaded_thumbnails"
TEMP_VIDEO = "temp_silent_reel.mp4"
TEMP_AUDIO = "temp_voiceover.mp3"
OUTPUT_FILE = "BeingABong_Flashy_Reel_Smooth.mp4"

WIDTH, HEIGHT = 1080, 1920
FPS = 30
TOTAL_DURATION = 58.0
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)

COLOR_INK_BLACK = (13, 13, 17)
COLOR_NEON_BLUE = (0, 212, 255)
COLOR_CRIMSON_RED = (216, 27, 38)
COLOR_NEON_MAGENTA = (224, 36, 195)
COLOR_NEON_GOLD = (255, 170, 0)
COLOR_WHITE = (251, 248, 242)

SCENES = [
    {
        "name": "HOOK",
        "start_sec": 0.0,
        "end_sec": 4.0,
        "title": "STOP SCROLLING",
        "subtitle": "500+ HOURS OF AUDIOBOOKS",
        "badge": "BEING A BONG AUDIO DRAMAS",
        "theme_color": COLOR_NEON_BLUE,
        "accent_color": COLOR_CRIMSON_RED,
        "vo_text": "If you love fantasy audiobooks, stop scrolling. Welcome to Being a Bong, your ultimate home for massive progression marathons."
    },
    {
        "name": "XIANXIA",
        "start_sec": 4.0,
        "end_sec": 12.0,
        "title": "XIANXIA • TALENT COPYING",
        "subtitle": "DUPLICATE GOD-TIER DAO ENTRIES",
        "badge": "CULTIVATION PROGRESSION",
        "theme_color": COLOR_CRIMSON_RED,
        "accent_color": COLOR_NEON_BLUE,
        "vo_text": "Craving Eastern cultivation? We take you into supreme worlds of Xianxia, where transmigrators steal divine physiques, duplicate god tier entries, and break through the heavens."
    },
    {
        "name": "LITRPG",
        "start_sec": 12.0,
        "end_sec": 22.0,
        "title": "LITRPG • STAT SYSTEMS",
        "subtitle": "POINTS EVERY SECOND • DEMIGOD POWERS",
        "badge": "INFINITE EVOLUTION",
        "theme_color": COLOR_NEON_BLUE,
        "accent_color": COLOR_NEON_BLUE,
        "vo_text": "More into hard LitRPG numbers? Experience endless stat progression, glitched evolutionary systems that grant points every single second, and demigod slaying domain abilities."
    },
    {
        "name": "BEAST_TAMING",
        "start_sec": 22.0,
        "end_sec": 30.0,
        "title": "BEAST TAMING & DUNGEONS",
        "subtitle": "MYTHICAL FAMILIARS • GODDESS SUMMONS",
        "badge": "MONSTER COMPANIONS & RAIDS",
        "theme_color": COLOR_NEON_MAGENTA,
        "accent_color": COLOR_NEON_BLUE,
        "vo_text": "We have deep beast taming sagas and lethal dungeon crawlers: raising mythical familiars, summoning cosmic goddesses, and raiding shattered ruins."
    },
    {
        "name": "APOCALYPSE",
        "start_sec": 30.0,
        "end_sec": 40.0,
        "title": "SYSTEM APOCALYPSE",
        "subtitle": "50-TON WAR RIGS • SKY FORTRESSES",
        "badge": "DOOMSDAY SURVIVAL",
        "theme_color": COLOR_CRIMSON_RED,
        "accent_color": COLOR_NEON_BLUE,
        "vo_text": "When the world ends, our apocalypse series kick into high gear: ruthless wasteland survival, building 50 ton armored war rigs, and commanding nuclear sky fortresses above drowning continents."
    },
    {
        "name": "KINGDOM",
        "start_sec": 40.0,
        "end_sec": 46.0,
        "title": "KINGDOM BUILDING & ROMANCE",
        "subtitle": "NATIONAL FATE • 10,000x MULTIPLIERS",
        "badge": "SOVEREIGN DOMAIN CONTROL",
        "theme_color": COLOR_NEON_GOLD,
        "accent_color": COLOR_CRIMSON_RED,
        "vo_text": "Need kingdom building with royal romance? We have got national fate games, sovereign court politics, and 10,000x multiplier rewards."
    },
    {
        "name": "MOSAIC",
        "start_sec": 46.0,
        "end_sec": 54.0,
        "title": "35 COMPLETE SERIES",
        "subtitle": "121 FULL-LENGTH MARATHONS",
        "badge": "100% FREE ON YOUTUBE",
        "theme_color": COLOR_NEON_BLUE,
        "accent_color": COLOR_CRIMSON_RED,
        "vo_text": "Over 120 full length marathon episodes across 35 complete series are live right now on YouTube, organized chronologically by playlist."
    },
    {
        "name": "CTA",
        "start_sec": 54.0,
        "end_sec": 58.0,
        "title": "WHERE WILL YOU BEGIN?",
        "subtitle": "COMMENT • LIKE • SUBSCRIBE",
        "badge": "TAP PINNED LINK IN BIO",
        "theme_color": COLOR_CRIMSON_RED,
        "accent_color": COLOR_NEON_BLUE,
        "vo_text": "Drop a comment on which genre is your favorite, hit that like button, and subscribe if you like the stories!"
    }
]

# ------------------------------------------------------------------------------
# 2. VOICE GENERATION
# ------------------------------------------------------------------------------
async def generate_voiceover():
    import edge_tts
    print("Generating voiceover...")
    full_text = " ".join([s["vo_text"] for s in SCENES])
    voice = "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(full_text, voice, rate="+5%", pitch="+0Hz")
    await communicate.save(TEMP_AUDIO)
    print(f"Voiceover saved: {TEMP_AUDIO}")

# ------------------------------------------------------------------------------
# 3. CARD AND GRAPHICS HELPERS
# ------------------------------------------------------------------------------
def load_and_prep_thumbnails():
    img_files = sorted(glob.glob(os.path.join(THUMBNAILS_DIR, "*.jpg")) + 
                       glob.glob(os.path.join(THUMBNAILS_DIR, "*.png")))
    if not img_files:
        raise FileNotFoundError(f"No thumbnails found in '{THUMBNAILS_DIR}'.")
    return img_files

def get_font(size, bold=True):
    for fn in ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf", "Helvetica"]:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()

def create_card_with_neon_glow(pil_img, border_color, target_w=920, target_h=518, glow_spread=16):
    card_thumb = pil_img.copy().convert("RGB").resize((target_w, target_h), Image.Resampling.LANCZOS)
    pad = glow_spread * 2
    cw, ch = target_w + pad * 2, target_h + pad * 2
    
    glow_mask = Image.new("L", (cw, ch), 0)
    draw_glow = ImageDraw.Draw(glow_mask)
    draw_glow.rounded_rectangle([pad - 4, pad - 4, cw - pad + 4, ch - pad + 4], radius=16, fill=255)
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(glow_spread))
    
    glow_layer = Image.new("RGBA", (cw, ch), border_color + (0,))
    glow_layer.putalpha(glow_mask)
    
    final_card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    final_card.paste(glow_layer, (0, 0), glow_layer)
    
    bordered = ImageOps.expand(card_thumb, border=6, fill=border_color)
    mask = Image.new("L", bordered.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, bordered.size[0], bordered.size[1]], radius=14, fill=255)
    final_card.paste(bordered, (pad - 6, pad - 6), mask)
    return final_card

def draw_pill_badge(draw, text, cx, y, bg_color, border_color, text_color, font):
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 36, 16
    x0, y0 = cx - (tw // 2) - pad_x, y - pad_y
    x1, y1 = cx + (tw // 2) + pad_x, y + th + pad_y
    draw.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=bg_color, outline=border_color, width=3)
    draw.text((cx - tw // 2, y), text, font=font, fill=text_color)

def draw_hud_elements(draw, color):
    bracket_len = 70
    thick = 4
    coords = [
        ((40, 130), (40 + bracket_len, 130), (40, 130 + bracket_len)),
        ((WIDTH - 40, 130), (WIDTH - 40 - bracket_len, 130), (WIDTH - 40, 130 + bracket_len)),
        ((40, HEIGHT - 180), (40 + bracket_len, HEIGHT - 180), (40, HEIGHT - 180 - bracket_len)),
        ((WIDTH - 40, HEIGHT - 180), (WIDTH - 40 - bracket_len, HEIGHT - 180), (WIDTH - 40, HEIGHT - 180 - bracket_len))
    ]
    for origin, horiz, vert in coords:
        draw.line([origin, horiz], fill=color, width=thick)
        draw.line([origin, vert], fill=color, width=thick)

# ------------------------------------------------------------------------------
# 4. FLICKER-FREE VIDEO GENERATION
# ------------------------------------------------------------------------------
def generate_video_stream():
    thumbnails = load_and_prep_thumbnails()
    total_thumbs = len(thumbnails)
    print(f"Rendering flicker-free video with {total_thumbs} thumbnails...")

    font_title = get_font(52, bold=True)
    font_sub = get_font(36, bold=True)
    font_badge = get_font(30, bold=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(TEMP_VIDEO, fourcc, FPS, (WIDTH, HEIGHT))

    cached_images = [Image.open(p).convert("RGB") for p in thumbnails]

    # Pre-render steady blurred backgrounds to avoid real-time blur jitter
    cached_blurred_bgs = []
    dark_overlay = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 15))
    for img in cached_images:
        bg_small = img.resize((WIDTH // 4, HEIGHT // 4), Image.Resampling.BILINEAR)
        bg_blurred = bg_small.filter(ImageFilter.GaussianBlur(16)).resize((WIDTH, HEIGHT), Image.Resampling.BICUBIC)
        dimmed = Image.blend(bg_blurred, dark_overlay, 0.70)
        cached_blurred_bgs.append(dimmed)

    # 4x8 mosaic for Scene 7
    mosaic_img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_INK_BLACK)
    m_cols, m_rows = 4, 8
    cell_w, cell_h = WIDTH // m_cols, HEIGHT // m_rows
    for idx, img in enumerate(cached_images[:32]):
        c, r = idx % m_cols, idx // m_cols
        mosaic_img.paste(img.resize((cell_w, cell_h), Image.Resampling.BILINEAR), (c * cell_w, r * cell_h))

    card_interval = 0.45  # Consistent time per card

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS

        curr_scene = SCENES[-1]
        for s in SCENES:
            if s["start_sec"] <= t < s["end_sec"]:
                curr_scene = s
                break

        scene_t = t - curr_scene["start_sec"]
        scene_dur = curr_scene["end_sec"] - curr_scene["start_sec"]

        # Current and next card index for smooth transitions
        current_idx = int(t / card_interval) % total_thumbs
        next_idx = (current_idx + 1) % total_thumbs
        cycle_progress = (t % card_interval) / card_interval

        # Smooth crossfade on blurred background (eliminates background flash)
        bg_curr = cached_blurred_bgs[current_idx]
        bg_next = cached_blurred_bgs[next_idx]
        if cycle_progress > 0.80:
            fade_alpha = (cycle_progress - 0.80) / 0.20
            frame = Image.blend(bg_curr, bg_next, fade_alpha)
        else:
            frame = bg_curr.copy()

        draw = ImageDraw.Draw(frame)

        # Static clean grid lines (no blinking / flickering)
        for gy in range(0, HEIGHT, 160):
            draw.line([(0, gy), (WIDTH, gy)], fill=(20, 25, 35), width=1)
        draw_hud_elements(draw, curr_scene["theme_color"])

        # Foreground Rendering
        if curr_scene["name"] == "MOSAIC":
            zoom = 1.0 + 0.25 * (1.0 - (scene_t / scene_dur))
            zw, zh = int(WIDTH * zoom), int(HEIGHT * zoom)
            scaled = mosaic_img.resize((zw, zh), Image.Resampling.BILINEAR)
            frame.paste(scaled.crop(((zw - WIDTH)//2, (zh - HEIGHT)//2, (zw - WIDTH)//2 + WIDTH, (zh - HEIGHT)//2 + HEIGHT)), (0, 0))
            draw = ImageDraw.Draw(frame)

        elif curr_scene["name"] == "CTA":
            # Smooth gentle breathing pulse
            pulse = 1.0 + 0.02 * math.sin(t * 4.0)
            cw, ch = int(720 * pulse), int(405 * pulse)
            card = create_card_with_neon_glow(cached_images[current_idx], COLOR_CRIMSON_RED, target_w=cw, target_h=ch)
            frame.paste(card, ((WIDTH - card.width) // 2, 600 - (card.height // 2)), card)
            draw = ImageDraw.Draw(frame)

            btn_w, btn_h = 420, 96
            bx0, by0 = (WIDTH - btn_w) // 2, 920
            draw.rounded_rectangle([bx0, by0, bx0 + btn_w, by0 + btn_h], radius=48, fill=COLOR_CRIMSON_RED, outline=COLOR_WHITE, width=3)
            draw.text(((WIDTH - 240) // 2, by0 + 26), "► SUBSCRIBE", font=font_sub, fill=COLOR_WHITE)

        else:
            # ------------------------------------------------------------------
            # SMOOTH CONTINUOUS HORIZONTAL SWIPE:
            # Fluid ease-in and ease-out transitions between consecutive cards
            # ------------------------------------------------------------------
            border_curr = curr_scene["theme_color"] if (current_idx % 2 == 0) else curr_scene["accent_color"]
            card_curr = create_card_with_neon_glow(cached_images[current_idx], border_curr, target_w=920, target_h=518)

            paste_y = 820 - (card_curr.height // 2)

            if cycle_progress < 0.25:
                # Smooth deceleration entering center from right
                ease = 1.0 - (cycle_progress / 0.25)
                offset_x = int(WIDTH * (ease ** 3))
                paste_x = ((WIDTH - card_curr.width) // 2) + offset_x
                frame.paste(card_curr, (paste_x, paste_y), card_curr)

            elif cycle_progress > 0.75:
                # Smooth acceleration exiting center to left
                ease = (cycle_progress - 0.75) / 0.25
                offset_x = -int(WIDTH * (ease ** 3))
                paste_x = ((WIDTH - card_curr.width) // 2) + offset_x
                frame.paste(card_curr, (paste_x, paste_y), card_curr)

                # Incoming next card smoothly sliding in from the right edge
                border_next = curr_scene["theme_color"] if (next_idx % 2 == 0) else curr_scene["accent_color"]
                card_next = create_card_with_neon_glow(cached_images[next_idx], border_next, target_w=920, target_h=518)
                next_x = paste_x + WIDTH
                frame.paste(card_next, (next_x, paste_y), card_next)

            else:
                # Steady centered display
                paste_x = (WIDTH - card_curr.width) // 2
                frame.paste(card_curr, (paste_x, paste_y), card_curr)

            draw = ImageDraw.Draw(frame)

        # Kinetic Text & Badges (Steady, clear rendering)
        tw = font_title.getbbox(curr_scene["title"])[2] - font_title.getbbox(curr_scene["title"])[0]
        draw.text(((WIDTH - tw) // 2 + 2, 260 + 2), curr_scene["title"], font=font_title, fill=(0, 0, 0))
        draw.text(((WIDTH - tw) // 2, 260), curr_scene["title"], font=font_title, fill=curr_scene["theme_color"])

        sw = font_sub.getbbox(curr_scene["subtitle"])[2] - font_sub.getbbox(curr_scene["subtitle"])[0]
        draw.text(((WIDTH - sw) // 2 + 2, 340 + 2), curr_scene["subtitle"], font=font_sub, fill=(0, 0, 0))
        draw.text(((WIDTH - sw) // 2, 340), curr_scene["subtitle"], font=font_sub, fill=COLOR_WHITE)

        draw_pill_badge(draw, curr_scene["badge"], WIDTH // 2, 1600, COLOR_INK_BLACK, curr_scene["theme_color"], curr_scene["theme_color"], font_badge)

        # Write clean RGB frame without chromatic channel offsets
        np_frame = np.array(frame)
        out.write(cv2.cvtColor(np_frame, cv2.COLOR_RGB2BGR))

        if frame_idx % (FPS * 10) == 0:
            print(f"Rendered: {int(t)}s / {int(TOTAL_DURATION)}s")

    out.release()
    print("Video rendering complete.")

# ------------------------------------------------------------------------------
# 5. AUDIO & VIDEO MERGE
# ------------------------------------------------------------------------------
def merge_audio_video():
    print("Merging with audio via FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-i", TEMP_VIDEO,
        "-i", TEMP_AUDIO,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        OUTPUT_FILE
    ]
    subprocess.run(cmd, check=True)

    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)
    if os.path.exists(TEMP_AUDIO):
        os.remove(TEMP_AUDIO)

    print("=" * 60)
    print(f"SUCCESS! Output saved to: {os.path.abspath(OUTPUT_FILE)}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(generate_voiceover())
    generate_video_stream()
    merge_audio_video()
