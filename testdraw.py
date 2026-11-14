import math
import os
import random
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
FPS = 30
DURATION = 10.0
TOTAL_FRAMES = int(FPS * DURATION)
OUT_WEBM = os.path.join("assets", "hud_overlay_10s.webm")
TEMP_DIR = "_temp_hud_frames"


def load_font(size: int, serif: bool = False) -> ImageFont.FreeTypeFont:
    serif_candidates = [
        "C:/Windows/Fonts/georgiab.ttf",
        "C:/Windows/Fonts/timesbd.ttf",
        "C:/Windows/Fonts/palab.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ]
    sans_candidates = [
        "C:/Windows/Fonts/seguisb.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates = (serif_candidates + sans_candidates) if serif else sans_candidates
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_snow_particles(count: int = 65, seed: int = 42) -> list[dict]:
    """Creates deterministic snow particles that wrap seamlessly over TOTAL_FRAMES."""
    rng = random.Random(seed)
    flakes = []
    for _ in range(count):
        flakes.append({
            "x0": rng.uniform(0, WIDTH),
            "y0": rng.uniform(0, HEIGHT),
            "radius": rng.choice([2, 3, 3, 4]),
            "cycles_y": rng.choice([1, 1, 2]),
            "sway_amp": rng.uniform(14.0, 36.0),
            "sway_freq": rng.choice([1.0, 2.0]),
            "sway_phase": rng.uniform(0, 2.0 * math.pi),
            "alpha": rng.randint(120, 215),
        })
    return flakes


def generate_falling_leaves(count: int = 22, seed: int = 99) -> list[dict]:
    """Creates deterministic tumbling autumn/celestial leaves for a seamless 10s loop."""
    rng = random.Random(seed)
    leaf_palettes = [
        ((245, 158, 11), (180, 83, 9)),     # Celestial Amber-Gold
        ((217, 119, 6), (146, 64, 14)),     # Warm Maple Bronze
        ((225, 29, 72), (136, 19, 55)),     # Royal Crimson Leaf
        ((234, 179, 8), (161, 98, 7)),      # Gilded Ochre
    ]
    leaves = []
    for _ in range(count):
        fill_rgb, vein_rgb = rng.choice(leaf_palettes)
        leaves.append({
            "x0": rng.uniform(0, WIDTH),
            "y0": rng.uniform(0, HEIGHT),
            "scale": rng.uniform(0.75, 1.35),
            "cycles_y": rng.choice([1, 1, 2]),
            "drift_x": rng.choice([-1, 0, 1]) * WIDTH,  # Integer screen wraps for seamless loop
            "sway_amp": rng.uniform(35.0, 85.0),
            "sway_freq": rng.choice([1.0, 2.0]),
            "rot_freq": rng.choice([1.0, 2.0, 3.0]),
            "phase_off": rng.uniform(0, 2.0 * math.pi),
            "fill_rgb": fill_rgb,
            "vein_rgb": vein_rgb,
            "alpha": rng.randint(185, 240),
        })
    return leaves


def draw_falling_snow(draw: ImageDraw.ImageDraw, t_norm: float, phase: float, flakes: list[dict]) -> None:
    """Renders slow, softly drifting snowflakes across the full 1920x1080 frame."""
    for f in flakes:
        y = (f["y0"] + t_norm * HEIGHT * f["cycles_y"]) % HEIGHT
        x = (f["x0"] + f["sway_amp"] * math.sin(phase * f["sway_freq"] + f["sway_phase"])) % WIDTH
        r = f["radius"]
        a = f["alpha"]

        draw.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1], fill=(210, 230, 255, a // 3))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))


def draw_falling_leaves(draw: ImageDraw.ImageDraw, t_norm: float, phase: float, leaves: list[dict]) -> None:
    """Renders gently tumbling, swaying leaves drifting across the scene."""
    for lf in leaves:
        cx = (lf["x0"] + t_norm * lf["drift_x"] + lf["sway_amp"] * math.sin(phase * lf["sway_freq"] + lf["phase_off"])) % WIDTH
        cy = (lf["y0"] + t_norm * HEIGHT * lf["cycles_y"]) % HEIGHT
        angle = phase * lf["rot_freq"] + lf["phase_off"]
        sc = lf["scale"]
        a = lf["alpha"]

        # Pointed leaf silhouette rotated in 2D with subtle flutter foreshortening
        flutter = 0.65 + 0.35 * abs(math.cos(angle * 0.5))
        local_pts = [
            (-16.0 * sc, 0.0),
            (-5.0 * sc, -8.5 * sc * flutter),
            (7.0 * sc, -6.5 * sc * flutter),
            (18.0 * sc, 0.0),
            (7.0 * sc, 6.5 * sc * flutter),
            (-5.0 * sc, 8.5 * sc * flutter),
        ]
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        def rot(px: float, py: float) -> tuple[float, float]:
            return (cx + px * cos_a - py * sin_a, cy + px * sin_a + py * cos_a)

        poly = [rot(px, py) for px, py in local_pts]
        stem_start = rot(-16.0 * sc, 0.0)
        stem_end = rot(-23.0 * sc, -2.5 * sc * flutter)
        tip = rot(15.0 * sc, 0.0)

        draw.polygon(poly, fill=(*lf["fill_rgb"], a), outline=(*lf["vein_rgb"], a))
        draw.line([stem_end, tip], fill=(*lf["vein_rgb"], a), width=max(1, int(2 * sc)))


def draw_origami_birds(draw: ImageDraw.ImageDraw, t_norm: float, phase: float) -> None:
    """
    Draws 3 distinct-colored folded-paper origami cranes/birds flying smoothly
    from right to left across the upper canvas.
    """
    birds = [
        (
            0.05, 175, 1.05, 5.0,
            {
                "body": (245, 158, 11, 245),       # Celestial Gold
                "wing_top": (254, 240, 138, 250),  # Champagne Gold facet
                "wing_bot": (180, 83, 9, 245),     # Deep Amber shadow facet
                "outline": (120, 53, 15, 255),
            },
        ),
        (
            0.38, 250, 0.92, 6.0,
            {
                "body": (225, 29, 72, 245),        # Royal Crimson
                "wing_top": (253, 164, 175, 250),  # Rose-Silk highlight facet
                "wing_bot": (136, 19, 55, 245),    # Deep Ruby shadow facet
                "outline": (76, 5, 25, 255),
            },
        ),
        (
            0.70, 320, 0.85, 5.0,
            {
                "body": (16, 185, 129, 245),       # Jade Emerald
                "wing_top": (167, 243, 208, 250),  # Mint-Jade highlight facet
                "wing_bot": (6, 95, 70, 245),      # Deep Forest shadow facet
                "outline": (2, 44, 34, 255),
            },
        ),
    ]

    span_x = WIDTH + 260
    for idx, (offset_t, base_y, sc, flap_freq, pal) in enumerate(birds):
        prog = (t_norm + offset_t) % 1.0
        cx = (WIDTH + 130) - prog * span_x
        cy = base_y + math.sin(phase * 2.0 + idx * 2.1) * 16.0
        flap = math.sin(phase * flap_freq + idx * 1.4)

        beak = (cx - 46 * sc, cy + 2 * sc)
        head_top = (cx - 28 * sc, cy - 12 * sc)
        neck_base = (cx - 16 * sc, cy + 4 * sc)
        chest = (cx - 8 * sc, cy + 14 * sc)
        belly = (cx + 18 * sc, cy + 12 * sc)
        tail_base = (cx + 24 * sc, cy + 2 * sc)
        tail_tip = (cx + 52 * sc, cy - 18 * sc)

        far_wing_tip = (cx + 10 * sc, cy - (26 + 24 * flap) * sc)
        near_wing_tip = (cx + 16 * sc, cy - (18 + 32 * flap) * sc)
        wing_fold = (cx + 4 * sc, cy + 2 * sc)

        draw.polygon([neck_base, far_wing_tip, tail_base], fill=pal["wing_bot"], outline=pal["outline"])
        draw.polygon([beak, head_top, neck_base, tail_base, tail_tip, belly, chest], fill=pal["body"], outline=pal["outline"])
        draw.line([neck_base, belly], fill=pal["outline"], width=2)
        draw.line([head_top, chest], fill=pal["outline"], width=2)
        draw.polygon([neck_base, near_wing_tip, wing_fold], fill=pal["wing_top"], outline=pal["outline"])
        draw.polygon([wing_fold, near_wing_tip, tail_base], fill=pal["body"], outline=pal["outline"])


def draw_unique_audiobook_crest(
    draw: ImageDraw.ImageDraw,
    phase: float,
    font: ImageFont.FreeTypeFont,
) -> None:
    """Renders the '◆ AUDIOBOOK ◆' obsidian-and-gold crest plaque above the open tome."""
    cx, cy = 285, 535
    pw, ph = 365, 52
    x0, y0 = cx - pw // 2, cy - ph // 2
    x1, y1 = cx + pw // 2, cy + ph // 2

    pulse = 0.5 + 0.5 * math.sin(phase * 2.0)
    gold_border = (234, 170, 46, int(215 + 40 * pulse))
    gold_bright = (254, 224, 130, 255)

    draw.rounded_rectangle([x0 + 5, y0 + 7, x1 + 5, y1 + 7], radius=ph // 2, fill=(8, 8, 14, 165))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=ph // 2, fill=(24, 16, 26, 245), outline=gold_border, width=3)
    draw.rounded_rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], radius=(ph - 10) // 2, outline=(217, 160, 54, 130), width=1)

    for dx in (x0 + 24, x1 - 24):
        r = 6
        draw.polygon([(dx, cy - r), (dx + r, cy), (dx, cy + r), (dx - r, cy)], fill=gold_bright)

    label = "A U D I O B O O K"
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx, ty = cx - tw // 2, cy - th // 2 - 2

    draw.text((tx + 2, ty + 2), label, font=font, fill=(10, 8, 12, 230))
    draw.text((tx, ty), label, font=font, fill=(254, 240, 185, 255))


def draw_book_and_headphones(draw: ImageDraw.ImageDraw, t_norm: float, phase: float) -> None:
    """
    1. Open leather-and-gold tome on the bottom-left with smoothly flipping pages.
    2. Over-ear obsidian-and-gold headphones beside the book on the right, with glowing
       audio waveforms rising smoothly out of the headphones into the air.
    """
    # =========================================================================
    # PART A: OPEN BOOK WITH FLIPPING PAGES (Bottom-Left)
    # =========================================================================
    bx, by = 75, 595
    bw, bh = 420, 255
    mid_x = bx + bw // 2

    # Soft ground shadow beneath the book
    draw.rounded_rectangle([bx + 8, by + 12, bx + bw + 8, by + bh + 12], radius=16, fill=(8, 8, 14, 165))

    # Outer deep obsidian-burgundy leather cover with antique gold border
    draw.rounded_rectangle(
        [bx, by, bx + bw, by + bh],
        radius=14,
        fill=(40, 16, 26, 250),
        outline=(217, 160, 54, 255),
        width=4,
    )

    # Gold corner brackets
    gold_accent = (245, 195, 80, 255)
    c_len = 20
    for cx, cy, dx, dy in [
        (bx + 6, by + 6, 1, 1),
        (bx + bw - 6, by + 6, -1, 1),
        (bx + 6, by + bh - 6, 1, -1),
        (bx + bw - 6, by + bh - 6, -1, -1),
    ]:
        draw.line([(cx, cy), (cx + dx * c_len, cy)], fill=gold_accent, width=3)
        draw.line([(cx, cy), (cx, cy + dy * c_len)], fill=gold_accent, width=3)

    # 3D stacked parchment page edges at bottom
    draw.polygon(
        [(bx + 14, by + bh - 15), (mid_x, by + bh - 11), (mid_x, by + bh - 4), (bx + 16, by + bh - 8)],
        fill=(206, 182, 138, 255),
        outline=(135, 108, 70, 255),
    )
    draw.polygon(
        [(mid_x, by + bh - 11), (bx + bw - 14, by + bh - 15), (bx + bw - 16, by + bh - 8), (mid_x, by + bh - 4)],
        fill=(196, 172, 128, 255),
        outline=(135, 108, 70, 255),
    )

    # Left & Right open parchment pages
    pad_x, pad_top, pad_bot = 15, 12, 15
    draw.polygon(
        [(bx + pad_x, by + pad_top), (mid_x - 2, by + pad_top + 5), (mid_x - 2, by + bh - pad_bot + 3), (bx + pad_x, by + bh - pad_bot)],
        fill=(248, 241, 224, 255),
        outline=(145, 118, 78, 255),
    )
    draw.polygon(
        [(mid_x + 2, by + pad_top + 5), (bx + bw - pad_x, by + pad_top), (bx + bw - pad_x, by + bh - pad_bot), (mid_x + 2, by + bh - pad_bot + 3)],
        fill=(241, 232, 212, 255),
        outline=(145, 118, 78, 255),
    )

    # Static ruled text lines on the base left & right pages
    ink_normal = (176, 158, 130, 200)
    for row in range(7):
        ly = by + 32 + row * 27
        l_x0 = bx + (48 if row < 3 else 30)
        l_x1 = mid_x - 18
        draw.line([(l_x0, ly), (l_x1, ly)], fill=ink_normal, width=2)

        r_x0 = mid_x + 18
        r_x1 = bx + bw - 30
        draw.line([(r_x0, ly), (r_x1, ly)], fill=ink_normal, width=2)

    # Spine crease & royal crimson silk bookmark ribbon
    draw.line([(mid_x, by + pad_top + 4), (mid_x, by + bh - pad_bot + 4)], fill=(95, 72, 48, 255), width=4)
    rx = bx + 42
    draw.polygon(
        [(rx, by + pad_top), (rx + 24, by + pad_top), (rx + 24, by + 95), (rx + 12, by + 78), (rx, by + 95)],
        fill=(185, 28, 44, 255),
        outline=(245, 195, 80, 255),
    )

    # Animated flipping parchment page (2 smooth page turns per 10s loop)
    turn_cycle = (phase * 2.0) % (2.0 * math.pi)
    flip_cos = math.cos(turn_cycle)
    page_span = int((bw // 2 - 22) * flip_cos)
    lift_y = int(32 * math.sin(turn_cycle))

    if abs(page_span) > 4:
        p_x = mid_x + page_span
        poly = [
            (mid_x, by + pad_top + 4),
            (p_x, by + pad_top + 2 - lift_y),
            (p_x, by + bh - pad_bot - 2 - lift_y),
            (mid_x, by + bh - pad_bot + 2),
        ]
        shade = 252 if flip_cos >= 0 else 233
        draw.polygon(poly, fill=(shade, shade - 7, shade - 22, 248), outline=(145, 118, 78, 255))

        # Printed lines moving across with the flipping page
        x_left = min(mid_x, p_x) + 12
        x_right = max(mid_x, p_x) - 12
        if x_right - x_left > 14:
            for row in range(6):
                ly_f = by + 36 + row * 28 - int(lift_y * 0.55)
                draw.line([(x_left, ly_f), (x_right, ly_f)], fill=(168, 150, 122, 195), width=2)

    # =========================================================================
    # PART B: OVER-EAR HEADPHONES BESIDE THE BOOK + RISING AUDIO WAVEFORMS
    # =========================================================================
    hx = 615
    hy = 755
    pulse = 0.5 + 0.5 * math.sin(phase * 4.0)

    # Ground shadow under headphones
    draw.ellipse([hx - 95, hy + 68, hx + 95, hy + 104], fill=(8, 8, 14, 165))

    # Outer & inner padded headband arch
    arch_box = [hx - 78, hy - 115, hx + 78, hy + 45]
    draw.arc(arch_box, start=180, end=360, fill=(28, 24, 36, 255), width=16)
    draw.arc(arch_box, start=180, end=360, fill=(234, 170, 46, 255), width=3)
    # Inner gold-stitched headband cushion
    inner_box = [hx - 64, hy - 101, hx + 64, hy + 31]
    draw.arc(inner_box, start=192, end=348, fill=(58, 24, 36, 255), width=8)

    # Metallic gold yokes connecting headband to earcups
    draw.line([(hx - 76, hy - 35), (hx - 72, hy + 12)], fill=(234, 170, 46, 255), width=5)
    draw.line([(hx + 76, hy - 35), (hx + 72, hy + 12)], fill=(234, 170, 46, 255), width=5)

    # Left Earcup (obsidian shell + gold rim + memory-foam cushion)
    draw.rounded_rectangle([hx - 92, hy - 8, hx - 48, hy + 76], radius=20, fill=(32, 22, 34, 255), outline=(234, 170, 46, 255), width=3)
    draw.rounded_rectangle([hx - 54, hy - 2, hx - 36, hy + 70], radius=10, fill=(54, 24, 34, 255), outline=(180, 130, 50, 255), width=2)
    # Glowing acoustic ring on left cup
    draw.ellipse([hx - 82, hy + 16, hx - 58, hy + 52], outline=(254, 224, 130, int(170 + 85 * pulse)), width=2)

    # Right Earcup (obsidian shell + gold rim + memory-foam cushion)
    draw.rounded_rectangle([hx + 48, hy - 8, hx + 92, hy + 76], radius=20, fill=(32, 22, 34, 255), outline=(234, 170, 46, 255), width=3)
    draw.rounded_rectangle([hx + 36, hy - 2, hx + 54, hy + 70], radius=10, fill=(54, 24, 34, 255), outline=(180, 130, 50, 255), width=2)
    # Glowing acoustic ring on right cup
    draw.ellipse([hx + 58, hy + 16, hx + 82, hy + 52], outline=(254, 224, 130, int(170 + 85 * pulse)), width=2)

    # Glowing Audio Waveforms Rising From the Headphones (NOT the book)
    wave_streams = [
        # (offset_t, start_x, start_y, drift_x, lift_h, core_rgb, glow_rgb)
        (0.00, hx - 58, hy - 18, -32, 275, (254, 243, 199), (245, 158, 11)),
        (0.20, hx, hy - 112, 0, 255, (254, 240, 138), (234, 170, 46)),
        (0.40, hx + 58, hy - 18, 36, 280, (255, 251, 235), (217, 119, 6)),
        (0.60, hx - 32, hy - 78, -18, 265, (209, 250, 229), (16, 185, 129)),
        (0.80, hx + 32, hy - 78, 22, 270, (254, 226, 226), (225, 29, 72)),
    ]

    for idx_w, (off_t, sx, sy, t_dx, lift_h, core_rgb, glow_rgb) in enumerate(wave_streams):
        # 2 seamless rise cycles per 10-second loop
        u = (t_norm * 2.0 + off_t) % 1.0

        if u < 0.16:
            alpha = int(255 * (u / 0.16))
        elif u > 0.72:
            alpha = int(255 * max(0.0, (1.0 - u) / 0.28))
        else:
            alpha = 255

        if alpha <= 8:
            continue

        cur_x = sx + t_dx * (u ** 1.1) + 18.0 * math.sin(u * 2.0 * math.pi + idx_w)
        cur_y = sy - lift_h * (u ** 0.92)
        scale_env = 0.55 + 0.55 * math.sin(u * math.pi)

        mini_bars = 9
        mb_w = 4
        mb_gap = 4
        tot_mw = mini_bars * mb_w + (mini_bars - 1) * mb_gap
        mx0 = cur_x - tot_mw / 2.0

        for b_i in range(mini_bars):
            c_w = 1.0 - abs(b_i - 4) / 5.0
            osc = 0.30 + 0.70 * abs(math.sin(phase * 8.0 + b_i * 1.05 + idx_w) * math.cos(phase * 5.0 - b_i * 0.8))
            bh_m = max(4.0, 34.0 * c_w * scale_env * osc)
            bx_i = mx0 + b_i * (mb_w + mb_gap)

            # Soft outer glow
            draw.rounded_rectangle(
                [bx_i - 2, cur_y - bh_m / 2.0 - 2, bx_i + mb_w + 2, cur_y + bh_m / 2.0 + 2],
                radius=3,
                fill=(*glow_rgb, max(6, alpha // 3)),
            )
            # Luminous waveform bar core
            draw.rounded_rectangle(
                [bx_i, cur_y - bh_m / 2.0, bx_i + mb_w, cur_y + bh_m / 2.0],
                radius=2,
                fill=(*core_rgb, alpha),
            )


def draw_voice_meter(draw: ImageDraw.ImageDraw, phase: float) -> None:
    """9 vertical Celestial Gold & Warm Amber pill bars centered at bottom."""
    num_bars = 9
    bar_w = 18
    gap = 20
    total_w = num_bars * bar_w + (num_bars - 1) * gap
    start_x = (WIDTH - total_w) // 2
    center_y = 850

    envelope = 0.35 + 0.65 * abs(math.sin(phase * 3.0) * math.cos(phase * 2.0 + 0.6))

    for i in range(num_bars):
        center_weight = 1.0 - (abs(i - (num_bars - 1) / 2.0) / 5.5)
        wave = abs(math.sin(phase * 7.0 + i * 0.95) * 0.6 + math.cos(phase * 11.0 - i * 1.3) * 0.4)
        bar_h = int(24 + (145 * center_weight * envelope * wave))
        x0 = start_x + i * (bar_w + gap)
        y0 = center_y - bar_h // 2
        y1 = center_y + bar_h // 2

        draw.rounded_rectangle([x0 - 3, y0 - 3, x0 + bar_w + 3, y1 + 3], radius=(bar_w + 6) // 2, fill=(12, 12, 18, 175))
        draw.rounded_rectangle([x0, y0, x0 + bar_w, y1], radius=bar_w // 2, fill=(234, 154, 28, 242))
        draw.rounded_rectangle([x0 + 4, y0 + 4, x0 + bar_w - 4, y1 - 4], radius=(bar_w - 8) // 2, fill=(254, 240, 165, 215))


def draw_cta_stack(draw: ImageDraw.ImageDraw, phase: float, font: ImageFont.FreeTypeFont) -> None:
    items = [
        ("LIKE", 0.0),
        ("SHARE", 0.35),
        ("SUBSCRIBE", 0.70),
    ]
    base_x = 1465
    base_y = 585
    row_h = 84
    row_gap = 20
    icon_box = 84

    raw_wave = math.sin(phase - 0.5)
    reveal_master = max(0.0, min(1.0, (raw_wave + 0.35) * 1.4))

    gold_border = (234, 170, 46, 255)
    gold_icon = (252, 211, 77, 255)
    obsidian_fill = (18, 16, 26, 240)

    for idx, (label, delay) in enumerate(items):
        y = base_y + idx * (row_h + row_gap)
        item_prog = max(0.0, min(1.0, (reveal_master - delay * 0.35) / 0.65))
        drawer_w = int(285 * item_prog)

        if drawer_w > 10:
            draw.rounded_rectangle(
                [base_x + icon_box - 12, y + 6, base_x + icon_box + drawer_w, y + row_h - 6],
                radius=12,
                fill=(14, 13, 20, 225),
                outline=gold_border,
                width=2,
            )
            visible_chars = max(0, int(len(label) * item_prog))
            if visible_chars > 0:
                draw.text(
                    (base_x + icon_box + 18, y + 21),
                    label[:visible_chars],
                    font=font,
                    fill=(254, 243, 199, 255),
                )

        draw.rounded_rectangle(
            [base_x, y, base_x + icon_box, y + icon_box],
            radius=16,
            fill=obsidian_fill,
            outline=gold_border,
            width=3,
        )

        cx, cy = base_x + icon_box // 2, y + icon_box // 2
        if label == "LIKE":
            draw.rectangle([cx - 19, cy - 4, cx - 10, cy + 17], fill=gold_icon)
            draw.polygon(
                [
                    (cx - 8, cy - 4),
                    (cx - 2, cy - 19),
                    (cx + 5, cy - 19),
                    (cx + 3, cy - 6),
                    (cx + 19, cy - 6),
                    (cx + 15, cy + 17),
                    (cx - 8, cy + 17),
                ],
                fill=gold_icon,
            )
        elif label == "SHARE":
            p1, p2, p3 = (cx - 14, cy), (cx + 14, cy - 14), (cx + 14, cy + 14)
            draw.line([p1, p2], fill=gold_icon, width=5)
            draw.line([p1, p3], fill=gold_icon, width=5)
            for px, py in (p1, p2, p3):
                draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=gold_icon)
        else:
            draw.rounded_rectangle([cx - 21, cy - 14, cx + 21, cy + 14], radius=6, outline=gold_icon, width=3)
            draw.polygon([(cx - 5, cy - 7), (cx - 5, cy + 7), (cx + 10, cy)], fill=gold_icon)


def build_hud_webm() -> None:
    os.makedirs("assets", exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    crest_font = load_font(24, serif=True)
    cta_font = load_font(34, serif=False)
    snow_flakes = generate_snow_particles(count=65, seed=42)
    leaves = generate_falling_leaves(count=22, seed=99)

    print(f"[HUD Generator] Rendering {TOTAL_FRAMES} transparent frames (10s @ {FPS}fps)...", flush=True)
    for f_idx in range(TOTAL_FRAMES):
        t_norm = f_idx / TOTAL_FRAMES
        phase = 2.0 * math.pi * t_norm
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        draw_falling_snow(draw, t_norm, phase, snow_flakes)
        draw_falling_leaves(draw, t_norm, phase, leaves)
        draw_origami_birds(draw, t_norm, phase)
        draw_book_and_headphones(draw, t_norm, phase)
        draw_unique_audiobook_crest(draw, phase, crest_font)
        draw_voice_meter(draw, phase)
        draw_cta_stack(draw, phase, cta_font)

        frame.save(os.path.join(TEMP_DIR, f"hud_{f_idx:04d}.png"), "PNG")

    print("[HUD Generator] Encoding transparent VP9 WebM overlay...", flush=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(FPS),
            "-i", os.path.join(TEMP_DIR, "hud_%04d.png"),
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-b:v", "1.5M",
            OUT_WEBM,
        ],
        check=True,
    )
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print(f"[HUD Generator] [OK] Saved reusable HUD loop: {OUT_WEBM}", flush=True)


if __name__ == "__main__":
    build_hud_webm()