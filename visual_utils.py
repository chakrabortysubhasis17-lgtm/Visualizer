import os
import io
import time
import base64
import random
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"

GRADIENT_PALETTES = [
    ((100, 230, 255), (20, 110, 240)),
    ((255, 215, 100), (240, 90, 30)),
    ((180, 120, 255), (90, 30, 210)),
]

def ensure_cinzel_font() -> str:
    if os.path.exists(CINZEL_LOCAL_PATH) and os.path.getsize(CINZEL_LOCAL_PATH) > 10000:
        return CINZEL_LOCAL_PATH
    try:
        resp = requests.get(CINZEL_URL, timeout=12)
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

def fit_crop_and_sharpen_1080p(img: Image.Image) -> Image.Image:
    target_w, target_h = 1920, 1080
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
    img = ImageEnhance.Brightness(img).enhance(1.06)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Color(img).enhance(1.20)
    img = img.filter(ImageFilter.DETAIL)
    img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=145, threshold=0))
    img = ImageEnhance.Sharpness(img).enhance(1.25)
    return img

def fetch_comic_artwork_landscape(prompt: str, out_path: str, block_index: int, cf_account_id: str, cf_token: str, request_timeout: int = 50) -> bool:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return True

    clean_p = " ".join(prompt.split()).strip()

    # Tier 1: Cloudflare Workers AI
    if cf_account_id and cf_token:
        print(f"     [Visual Engine] Requesting Block {block_index} via Cloudflare Workers AI (FLUX-1-schnell)...", flush=True)
        url_cf = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        headers_cf = {"Authorization": f"Bearer {cf_token}", "Content-Type": "application/json"}
        payload_cf = {"prompt": clean_p, "steps": 4}
        try:
            resp = requests.post(url_cf, headers=headers_cf, json=payload_cf, timeout=request_timeout)
            if resp.status_code == 200:
                raw_bytes = None
                try:
                    data = resp.json()
                    if "result" in data and "image" in data["result"]:
                        raw_bytes = base64.b64decode(data["result"]["image"])
                except Exception:
                    pass
                if not raw_bytes and len(resp.content) > 5000:
                    raw_bytes = resp.content

                if raw_bytes:
                    img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
                    img = fit_crop_and_sharpen_1080p(img)
                    img.convert("RGB").save(out_path, "JPEG", quality=98)
                    print(f"     [Visual Engine] [✓] Delivered Block {block_index} via Cloudflare!", flush=True)
                    return True
        except Exception as e:
            print(f"     [Visual Engine] Cloudflare notice: {e}. Falling back to Pollinations...", flush=True)

    # Tier 2: Pollinations Fallback with Continuous 10s Retry Loop
    print(f"     [Visual Engine] Triggering Pollinations Fallback for Block {block_index} (Cooldown: 10s until success)...", flush=True)
    encoded = urllib.parse.quote(clean_p)
    attempt = 1

    while True:
        seed = random.randint(10000, 9999999)
        target_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed}&model=flux&nologo=true"
        print(f"     [Visual Engine] Pollinations attempt {attempt} for Block {block_index}...", flush=True)

        try:
            resp = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=request_timeout)
            if resp.status_code == 200 and len(resp.content) > 10000:
                raw_temp = out_path + ".tmp.jpg"
                with open(raw_temp, "wb") as f:
                    f.write(resp.content)
                base = Image.open(raw_temp).convert("RGBA")
                bw, bh = base.size
                base = base.crop((0, 0, bw, bh - int(bh * 0.055)))
                base = fit_crop_and_sharpen_1080p(base)
                base.convert("RGB").save(out_path, "JPEG", quality=98)
                try: os.remove(raw_temp)
                except OSError: pass
                print(f"     [Visual Engine] [✓] Delivered Block {block_index} via Pollinations on attempt {attempt}!", flush=True)
                return True
            else:
                print(f"     [Visual Engine] Pollinations attempt {attempt} returned HTTP {resp.status_code}. Waiting 10s...", flush=True)
        except Exception as e:
            print(f"     [Visual Engine] Pollinations attempt {attempt} error: {e}. Waiting 10s...", flush=True)

        attempt += 1
        time.sleep(10)

def apply_lower_third_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(overlay)
    vig_start = int(height * 0.72)
    for y in range(vig_start, height):
        alpha = int(85 * (((y - vig_start) / (height - vig_start)) ** 1.3))
        v_draw.line([(0, y), (width, y)], fill=(12, 18, 35, alpha))
    return Image.alpha_composite(base.convert("RGBA"), overlay)

def stamp_four_corner_branding(base: Image.Image, build_dir: str, branding_assets: dict) -> Image.Image:
    """Stamps logo (TL 380px), subscribe (TR 460px), like (BL 240px h), and voice (BR 480px)."""
    if base.mode != "RGBA":
        base = base.convert("RGBA")

    # 1. Top-Left: logo.png (380px wide)
    logo_path = os.path.join(build_dir, branding_assets.get("logo", "logo.png"))
    if os.path.exists(logo_path):
        try:
            img = Image.open(logo_path).convert("RGBA")
            target_w = 380
            target_h = int(img.size[1] * (target_w / float(img.size[0])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (30, 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting logo: {e}", flush=True)

    # 2. Top-Right: subscribe.png (460px wide)
    sub_path = os.path.join(build_dir, branding_assets.get("subscribe", "subscribe.png"))
    if os.path.exists(sub_path):
        try:
            img = Image.open(sub_path).convert("RGBA")
            target_w = 460
            target_h = int(img.size[1] * (target_w / float(img.size[0])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (1920 - target_w - 30, 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting subscribe: {e}", flush=True)

    # 3. Bottom-Left: like.png (240px tall)
    like_path = os.path.join(build_dir, branding_assets.get("like", "like.png"))
    if os.path.exists(like_path):
        try:
            img = Image.open(like_path).convert("RGBA")
            target_h = 240
            target_w = int(img.size[0] * (target_h / float(img.size[1])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (30, 1080 - target_h - 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting like: {e}", flush=True)

    # 4. Bottom-Right: voice.png (480px wide)
    voice_path = os.path.join(build_dir, branding_assets.get("voice", "voice.png"))
    if os.path.exists(voice_path):
        try:
            img = Image.open(voice_path).convert("RGBA")
            target_w = 480
            target_h = int(img.size[1] * (target_w / float(img.size[0])))
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.paste(img_resized, (1920 - target_w - 30, 1080 - target_h - 30), mask=img_resized.split()[3])
        except Exception as e:
            print(f"[Watermark] Failed pasting voice: {e}", flush=True)

    return base

def create_vertical_gradient_text_mask(width: int, height: int, line: str, font: ImageFont.FreeTypeFont, top_col: tuple, bot_col: tuple) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.text((0, 0), line, fill=255, font=font)
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    for y in range(height):
        factor = y / max(1, height - 1)
        r = int(top_col[0] + (bot_col[0] - top_col[0]) * factor)
        g = int(top_col[1] + (bot_col[1] - top_col[1]) * factor)
        b = int(top_col[2] + (bot_col[2] - top_col[2]) * factor)
        g_draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    gradient.putalpha(mask)
    return gradient

def stamp_3d_metallic_flame_typography(base: Image.Image, lines: list) -> Image.Image:
    width, height = base.size
    font_path = ensure_cinzel_font()
    title_font = ImageFont.truetype(font_path, 78)
    sub_font = ImageFont.truetype(font_path, 64)
    line_spacing = 96

    clean_lines = [l for l in lines if not l.lower().startswith("chapter")]
    total_text_h = (len(clean_lines) - 1) * line_spacing + 80
    start_y = int(height * 0.66) - (total_text_h // 2)

    for i, line in enumerate(clean_lines):
        active_font = sub_font if i > 0 else title_font
        bbox = ImageDraw.Draw(base).textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)

        ImageDraw.Draw(base).text((x + 4, y + 5), line, font=active_font, fill=(15, 20, 30, 255), stroke_width=7, stroke_fill=(15, 20, 30, 255))
        ImageDraw.Draw(base).text((x, y), line, font=active_font, fill=(30, 45, 60, 255), stroke_width=4, stroke_fill=(30, 45, 60, 255))

        palette = GRADIENT_PALETTES[min(i, len(GRADIENT_PALETTES) - 1)]
        grad_layer = create_vertical_gradient_text_mask(text_w + 25, text_h + 25, line, active_font, palette[0], palette[1])
        base.paste(grad_layer, (x, y), grad_layer)

    return base

def ensure_block_cover_jit(cfg: dict, build_dir: str, branding_assets: dict, cf_account_id: str, cf_token: str):
    out_file = cfg["cover_file"]
    b_idx = cfg["index"]
    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        return

    raw_art = os.path.join(build_dir, f"raw_block_{b_idx}.jpg")
    success = fetch_comic_artwork_landscape(cfg["prompt"], raw_art, block_index=b_idx, cf_account_id=cf_account_id, cf_token=cf_token)
    if success and os.path.exists(raw_art):
        base = Image.open(raw_art).convert("RGBA")
    else:
        base = Image.new("RGBA", (1920, 1080), (*cfg.get("fallback_color", (15, 25, 40)), 255))

    base = apply_lower_third_vignette(base)
    base = stamp_four_corner_branding(base, build_dir, branding_assets)
    base = stamp_3d_metallic_flame_typography(base, cfg["title"])
    base.convert("RGB").save(out_file, "JPEG", quality=98)
    print(f"[Visual Saved] Block {b_idx} Cover: '{out_file}'", flush=True)

def create_dynamic_outro_slate(out_path: str, build_dir: str, branding_assets: dict, next_ch_num: int):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return
    base = Image.new("RGB", (1920, 1080), (18, 22, 32))
    base = apply_lower_third_vignette(base)
    base = stamp_four_corner_branding(base, build_dir, branding_assets)
    draw = ImageDraw.Draw(base)
    font_path = ensure_cinzel_font()
    head_font = ImageFont.truetype(font_path, 60)
    cta_font = ImageFont.truetype(font_path, 46)
    line1 = f"CHAPTER {next_ch_num} COMING SOON"
    line2 = "SUBSCRIBE FOR THE NEXT MARATHON"
    for i, txt in enumerate([line1, line2]):
        font = head_font if i == 0 else cta_font
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        x = (1920 - tw) // 2
        y = 480 + (i * 85)
        draw.text((x + 3, y + 4), txt, font=font, fill=(10, 12, 18, 255))
        draw.text((x, y), txt, font=font, fill=(255, 215, 100, 255) if i == 0 else (255, 255, 255, 255))
    base.convert("RGB").save(out_path, "JPEG", quality=95)
