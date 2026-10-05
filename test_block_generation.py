import os
import io
import time
import base64
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

# ==================== CONFIGURATION ====================
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "60ea0428a4b6bd44eeef701cee024518")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "cfut_jFW6WAXHIsZAwayo09xXRQxsupmNPa0BecNmrnMM70d9ea43")

CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"
CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"

OUT_DIR = "reference_style_tests"
os.makedirs(OUT_DIR, exist_ok=True)

# 7 Precise reverse-engineered prompts corresponding to your reference images
REFERENCE_TEST_CASES = [
    {
        "id": "ref1_game_arrives_matrix",
        "title": ["GAME ARRIVES: TALENT EVOLUTION", "BROKEN REALITY BARRIER", "Chapters 101 – 105"],
        "prompt": (
            "2D manhwa comic key visual, bold vector black ink linework, flat cel-shading. "
            "Center: cracked reality glass mirror reflecting a pale celestial goddess with silver hair and glowing tiara. "
            "Foreground: cultivator Zhou Han viewed from behind looking upward, radiating brilliant cyan burst aura. "
            "Floating glowing green binary code streams and microchips in dark cosmic nebula sky. "
            "Razor-sharp linework, high contrast, vivid cyan and magenta, no blur, no 3D CGI."
        )
    },
    {
        "id": "ref2_beast_patriarch_emerald",
        "title": ["MYRIAD BEASTS CHRONICLES", "DUAL SPIRIT TAMER AWAKENING", "Chapters 106 – 110"],
        "prompt": (
            "2D manhwa webtoon key visual, bold vector black ink contours, sharp cel-shading. "
            "Center: young cultivator patriarch in emerald jade dragon robes holding sheathed sword. "
            "Flanked on left by massive purple shadow wolf with glowing amber eyes, and on right by majestic cyan lightning eagle. "
            "Behind: towering ancient stone monolith stele with glowing golden daoist calligraphy. "
            "Misty mountain peaks background, vibrant primary colors, sharp focus, no blur, no 3D CGI."
        )
    },
    {
        "id": "ref3_infinite_blade_circles",
        "title": ["INFINITE BLADE SOVEREIGN", "CONCENTRIC RUNIC DOMAIN", "Chapters 111 – 115"],
        "prompt": (
            "2D manhwa action key visual, bold vector black ink linework, flat cel-shading. "
            "Heroic cultivator in ornate steel-gold plate armor wielding heavy greatsword engulfed in blazing solar-gold flame ribbons. "
            "Surrounded by massive concentric glowing golden magic circles hovering in the air with spectral runic swords pointing outward. "
            "Background: dark stone arches, glowing blue portal gate, gargoyle silhouettes. "
            "Intense warm lighting, sharp edge contours, zero blur, no 3D CGI."
        )
    },
    {
        "id": "ref4_beast_tamer_flame_wolf",
        "title": ["BEAST TAMER CLAN SOVEREIGN", "PRIMORDIAL FLAME CONVERGENCE", "Chapters 116 – 120"],
        "prompt": (
            "2D manhwa webtoon key visual, Solo Leveling style, bold vector ink linework, flat cel-shading. "
            "Young dark-haired cultivator in black fur mantle extending hand forward with swirling golden lightning mana. "
            "Behind him: colossal twin-headed demonic spirit wolf split between blazing solar fire and electric blue plasma. "
            "Background: oriental mountain pagodas and stormy sky. "
            "Intense rim lighting, saturated colors, razor-sharp focus, no blur, no 3D CGI."
        )
    },
    {
        "id": "ref5_hud_domain_expansion",
        "title": ["GOD-SLAYING DOMAIN", "F-RANK TO S-RANK BREAKTHROUGH", "Chapters 121 – 125"],
        "prompt": (
            "2D manhwa webtoon key visual, Solo Leveling comic style, bold vector ink linework, flat cel-shading. "
            "Protagonist in dark starlit overcoat reaching forward with electric blue hand sparks. "
            "Floating translucent glowing holographic LitRPG system skill cards and floating stat windows. "
            "Behind: massive looming shadowy dragon beast and pale-haired princess silhouette over fantasy citadel. "
            "Deep sapphire and electric blue lighting, ultra-sharp focus, no blur, no 3D CGI."
        )
    },
    {
        "id": "ref6_inter_server_armored_titan",
        "title": ["INTER-SERVER SHOWDOWN", "CRIMSON TITAN INCARNATION", "Chapters 126 – 130"],
        "prompt": (
            "2D manhwa graphic novel key visual, bold vector black ink linework, flat cel-shading. "
            "Towering jagged armored titan knight standing on mountain crags, jagged obsidian spires and glowing molten core chestplate. "
            "Holding jagged greatsword against blazing crimson sunset sky filled with burning nebula clouds and falling stardust embers. "
            "Intense fiery rim lighting, deep shadows, razor-sharp edge contours, no blur, no 3D CGI."
        )
    },
    {
        "id": "ref7_winter_stele_hound",
        "title": ["MYRIAD BEAST STELE", "TRACKING AND SLAUGHTER PATH", "Chapters 131 – 135"],
        "prompt": (
            "2D manhwa webtoon key visual, bold vector black ink linework, flat cel-shading. "
            "Winter mountain landscape at twilight: hunter cultivator in thick wolf-fur coat extending hand above a sleek black spirit hound. "
            "Beside them: towering weathered ancient stone stele etched with glowing golden Chinese calligraphy runes, surrounded by swirling cyan wind mana ribbons. "
            "Snowy jagged crags, sharp vector contours, rich saturated colors, no blur, no 3D CGI."
        )
    }
]

GRADIENT_PALETTES = [
    ((255, 235, 120), (255, 120, 40)),
    ((160, 230, 255), (60, 140, 255)),
    ((220, 160, 255), (140, 60, 240)),
]

# ==================== CLOUDFLARE WORKERS AI ====================
def call_cloudflare_flux(prompt: str, out_raw_path: str) -> bool:
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "steps": 4
    }

    try:
        t0 = time.time()
        resp = requests.post(url, headers=headers, json=payload, timeout=50)
        elapsed = time.time() - t0

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
                with open(out_raw_path, "wb") as f:
                    f.write(raw_bytes)
                print(f"   [✓] Cloudflare delivered in {elapsed:.2f}s ({len(raw_bytes)} bytes)", flush=True)
                return True
        else:
            print(f"   [!] Cloudflare HTTP {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"   [!] Network exception: {e}")

    return False

# ==================== POST-PROCESSING & TYPOGRAPHY ====================
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

def apply_lower_third_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(overlay)
    vig_start = int(height * 0.82)
    for y in range(vig_start, height):
        alpha = int(75 * (((y - vig_start) / (height - vig_start)) ** 1.3))
        v_draw.line([(0, y), (width, y)], fill=(12, 18, 35, alpha))
    return Image.alpha_composite(base.convert("RGBA"), overlay)

def stamp_channel_watermark(base: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(base)
    wx, wy = 55, 45
    crest_r = 22
    draw.ellipse([(wx - crest_r, wy - crest_r), (wx + crest_r, wy + crest_r)], fill=(225, 150, 40, 255), outline=(255, 245, 220, 255), width=2)
    star_font = None
    for fp in ["C:/Windows/Fonts/seguisym.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(fp):
            try:
                star_font = ImageFont.truetype(fp, 24)
                break
            except Exception:
                pass
    if not star_font:
        star_font = ImageFont.load_default()
    bbox_star = draw.textbbox((0, 0), "✦", font=star_font)
    sw = bbox_star[2] - bbox_star[0]
    sh = bbox_star[3] - bbox_star[1]
    draw.text((wx - (sw // 2), wy - (sh // 2) - 2), "✦", fill=(255, 255, 255, 255), font=star_font)
    name_fp = "C:/Windows/Fonts/arialbd.ttf"
    if not os.path.exists(name_fp):
        name_fp = ensure_cinzel_font()
    name_font = ImageFont.truetype(name_fp, 36)
    handle_font = ImageFont.truetype(name_fp, 22)
    tx = wx + 36
    draw.text((tx + 2, wy - 18 + 2), "Being a Bong", fill=(20, 15, 10, 255), font=name_font)
    draw.text((tx, wy - 18), "Being a Bong", fill=(255, 255, 255, 255), font=name_font)
    draw.text((tx + 1, wy + 20 + 1), "@beingabong", fill=(20, 15, 10, 220), font=handle_font)
    draw.text((tx, wy + 20), "@beingabong", fill=(255, 215, 100, 255), font=handle_font)
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
    title_font = ImageFont.truetype(font_path, 60)
    sub_font = ImageFont.truetype(font_path, 46)
    line_spacing = 76
    total_text_h = (len(lines) - 1) * line_spacing + 60
    start_y = int(height * 0.81) - (total_text_h // 2)
    draw = ImageDraw.Draw(base)

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else title_font
        bbox = draw.textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)
        draw.text((x + 3, y + 4), line, font=active_font, fill=(15, 20, 30, 255), stroke_width=5, stroke_fill=(15, 20, 30, 255))
        draw.text((x, y), line, font=active_font, fill=(30, 45, 60, 255), stroke_width=3, stroke_fill=(30, 45, 60, 255))
        palette = GRADIENT_PALETTES[min(i, len(GRADIENT_PALETTES) - 1)]
        grad_layer = create_vertical_gradient_text_mask(text_w + 20, text_h + 20, line, active_font, palette[0], palette[1])
        base.paste(grad_layer, (x, y), grad_layer)
    return base

# Build composite overview grid
def build_composite_grid(generated_files: list, out_grid: str):
    valid_imgs = [Image.open(f) for f in generated_files if os.path.exists(f)]
    if not valid_imgs:
        return
    count = len(valid_imgs)
    cols = 2
    rows = (count + 1) // 2
    cell_w, cell_h = 960, 540
    grid = Image.new("RGB", (cols * cell_w, rows * cell_h), (10, 12, 18))

    for idx, img in enumerate(valid_imgs):
        r = idx // cols
        c = idx % cols
        grid.paste(img.resize((cell_w, cell_h), Image.Resampling.LANCZOS), (c * cell_w, r * cell_h))

    grid.save(out_grid, "JPEG", quality=95)
    print(f"\n[✓] Composite Grid saved -> {out_grid}", flush=True)

# ==================== MAIN EXECUTION ====================
def main():
    print("=" * 70)
    print(" BATCH RUNNING 7 REFERENCE-STYLE GENERATIONS ON CLOUDFLARE FLUX")
    print(" (Zero wait cooldowns — Instant sequential generation)")
    print("=" * 70)

    final_images = []

    for idx, case in enumerate(REFERENCE_TEST_CASES, 1):
        case_id = case["id"]
        out_jpg = os.path.join(OUT_DIR, f"{case_id}.jpg")
        raw_png = os.path.join(OUT_DIR, f"{case_id}_raw.png")

        print(f"\n[{idx}/7] Firing Cloudflare FLUX for: {case['title'][0]}")
        print(f"      Prompt: \"{case['prompt'][:100]}...\"")

        success = call_cloudflare_flux(case["prompt"], raw_png)

        if success and os.path.exists(raw_png):
            img = Image.open(raw_png).convert("RGBA")
            img = fit_crop_and_sharpen_1080p(img)
            img = apply_lower_third_vignette(img)
            img = stamp_channel_watermark(img)
            img = stamp_3d_metallic_flame_typography(img, case["title"])
            img.convert("RGB").save(out_jpg, "JPEG", quality=98)

            try:
                os.remove(raw_png)
            except OSError:
                pass

            print(f"      [✓] Finished and stylized -> {out_jpg}")
            final_images.append(out_jpg)
        else:
            print(f"      [!] Failed to generate {case_id}")

    grid_path = os.path.join(OUT_DIR, "ALL_7_REFERENCES_GRID.jpg")
    build_composite_grid(final_images, grid_path)

    print("\n" + "=" * 70)
    print(" RUN COMPLETE! Inspect your results in:")
    print(f" {os.path.abspath(OUT_DIR)}")
    print("=" * 70)

if __name__ == "__main__":
    main()
