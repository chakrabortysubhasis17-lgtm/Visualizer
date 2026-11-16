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
            "drift_x": rng.choice([-1, 0, 1]) * WIDTH,
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
        stem_end = rot(-23.0 * sc, -2.5 * sc * flutter)
        tip = rot(15.0 * sc, 0.0)

        draw.polygon(poly, fill=(*lf["fill_rgb"], a), outline=(*lf["vein_rgb"], a))
        draw.line([stem_end, tip], fill=(*lf["vein_rgb"], a), width=max(1, int(2 * sc)))


def draw_origami_birds(draw: ImageDraw.ImageDraw, t_norm: float, phase: float) -> None:
    """
    Draws 3 distinct-colored folded-paper origami cranes/birds flying smoothly
    from right to left across the upper-left/center canvas without colliding with the right HUD.
    """
    birds = [
        (
            0.05, 115, 0.98, 5.0,
            {
                "body": (245, 158, 11, 245),       # Celestial Gold
                "wing_top": (254, 240, 138, 250),  # Champagne Gold facet
                "wing_bot": (180, 83, 9, 245),     # Deep Amber shadow facet
                "outline": (120, 53, 15, 255),
            },
        ),
        (
            0.38, 175, 0.88, 6.0,
            {
                "body": (225, 29, 72, 245),        # Royal Crimson
                "wing_top": (253, 164, 175, 250),  # Rose-Silk highlight facet
                "wing_bot": (136, 19, 55, 245),    # Deep Ruby shadow facet
                "outline": (76, 5, 25, 255),
            },
        ),
        (
            0.70, 235, 0.82, 5.0,
            {
                "body": (16, 185, 129, 245),       # Jade Emerald
                "wing_top": (167, 243, 208, 250),  # Mint-Jade highlight facet
                "wing_bot": (6, 95, 70, 245),      # Deep Forest shadow facet
                "outline": (2, 44, 34, 255),
            },
        ),
    ]

    span_x = 1150
    for idx, (offset_t, base_y, sc, flap_freq, pal) in enumerate(birds):
        prog = (t_norm + offset_t) % 1.0
        cx = 1020 - prog * span_x
        cy = base_y + math.sin(phase * 2.0 + idx * 2.1) * 15.0
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


# =============================================================================
# SEMI-TRANSPARENT 3D-ANGLED HOLOGRAPHIC STATS HUD (DOCKED RIGHT)
# =============================================================================

def _find_perspective_coeffs(src_pts: list[tuple[float, float]], dst_pts: list[tuple[float, float]]) -> list[float]:
    """Solves 8x8 linear system for PIL Image.Transform.PERSPECTIVE (dst -> src mapping)."""
    matrix = []
    for (sx, sy), (dx, dy) in zip(src_pts, dst_pts):
        matrix.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy])
        matrix.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy])

    rhs = [coord for pt in src_pts for coord in pt]
    n = 8
    aug = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]

    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[piv] = aug[piv], aug[col]
        div = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= div
        for r in range(n):
            if r != col and aug[r][col] != 0:
                factor = aug[r][col]
                for j in range(col, n + 1):
                    aug[r][j] -= factor * aug[col][j]

    return [aug[i][n] for i in range(n)]


def draw_translucent_holo_card(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    accent: tuple[int, int, int],
    pulse: float,
    fill_alpha: int = 72,
) -> None:
    """Draws a semi-transparent glowing holographic glass card with double neon borders."""
    glow_a = int(42 + 28 * pulse)
    border_a = int(195 + 55 * pulse)
    inner_a = int(95 + 45 * pulse)
    bright = (min(255, accent[0] + 75), min(255, accent[1] + 75), min(255, accent[2] + 75), border_a)

    # Soft outer holographic aura
    draw.rounded_rectangle([x0 - 5, y0 - 5, x1 + 5, y1 + 5], radius=14, outline=(*accent, glow_a), width=5)
    # Semi-transparent glass fill (low alpha so background art shows clearly through)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(8, 22, 34, fill_alpha), outline=bright, width=2)
    # Inner double-frame hairline
    draw.rounded_rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], radius=7, outline=(*accent, inner_a), width=1)

    # Glowing corner L-accents
    cl = 16
    for cx, cy, dx, dy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        draw.line([(cx, cy), (cx + dx * cl, cy)], fill=bright, width=3)
        draw.line([(cx, cy), (cx, cy + dy * cl)], fill=bright, width=3)


def draw_isometric_pagoda_wireframe(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    phase: float,
) -> None:
    """Draws the glowing golden 3D-projected multi-tiered pagoda with blueprint callout lines."""
    rot = phase * 1.0
    bob = math.sin(phase * 2.0) * 4.0
    base_y = cy + bob

    gold_bright = (255, 232, 145, 235)
    gold_mid = (245, 185, 66, 185)
    cyan_line = (103, 232, 249, 145)

    # Base foundation platform diamond
    for plat_i, (pw, ph) in enumerate([(76, 26), (62, 21)]):
        py = base_y + 44 - plat_i * 7
        pts = []
        for k in range(4):
            a = rot + k * (math.pi / 2.0)
            pts.append((cx + pw * math.cos(a), py + ph * math.sin(a)))
        draw.polygon(pts, fill=(245, 185, 66, 26), outline=gold_mid)

    # 3 Rotating Pagoda Roof & Pillar Tiers
    tiers = [
        (22, 62, 21, 18, 16),
        (-4, 48, 16, 16, 14),
        (-28, 34, 12, 15, 12),
    ]
    for y_off, rx, ry, roof_h, wall_h in tiers:
        ty = base_y + y_off
        eaves = []
        walls = []
        for k in range(4):
            a = rot + k * (math.pi / 2.0) + math.pi / 4.0
            ex = cx + rx * math.cos(a)
            ey = ty + ry * math.sin(a)
            eaves.append((ex, ey))
            walls.append((cx + rx * 0.72 * math.cos(a), ty + ry * 0.72 * math.sin(a) + wall_h))

        apex = (cx, ty - roof_h)
        # Roof ribs + upturned eaves
        for k in range(4):
            nxt = (k + 1) % 4
            draw.line([eaves[k], eaves[nxt]], fill=gold_bright, width=2)
            draw.line([apex, eaves[k]], fill=gold_bright, width=2)
            draw.line([walls[k], walls[nxt]], fill=gold_mid, width=1)
            draw.line([eaves[k], walls[k]], fill=gold_mid, width=1)

    # Spire pinnacle
    draw.line([(cx, base_y - 43), (cx, base_y - 62)], fill=gold_bright, width=2)
    draw.ellipse([cx - 3, base_y - 66, cx + 3, base_y - 60], fill=(255, 250, 210, 245))

    # Holographic blueprint callout lines & telemetry micro-bars (matching reference center panel)
    draw.line([(cx + 42, base_y - 34), (cx + 76, base_y - 54), (cx + 124, base_y - 54)], fill=cyan_line, width=1)
    draw.line([(cx + 54, base_y + 10), (cx + 84, base_y - 6), (cx + 124, base_y - 6)], fill=cyan_line, width=1)
    for idx_b in range(5):
        w_bar = int(28 + 22 * abs(math.sin(phase * 2.0 + idx_b * 0.8)))
        by_line = int(base_y - 68 + idx_b * 7)
        draw.rectangle([cx - 122, by_line, cx - 122 + w_bar, by_line + 3], fill=(103, 232, 249, 135))


def draw_cyan_spirit_well_icon(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    scale: float,
    phase: float,
) -> None:
    """Draws the glowing cyan hexagonal Spirit Well shrine/gazebo wireframe."""
    rot = -phase * 0.8
    cyan_bright = (165, 243, 252, 235)
    cyan_mid = (34, 211, 238, 180)
    cyan_fill = (34, 211, 238, 34)

    rx = 46 * scale
    ry = 16 * scale
    top_y = cy - 18 * scale
    bot_y = cy + 28 * scale
    apex = (cx, cy - 42 * scale)

    top_pts = []
    bot_pts = []
    for k in range(6):
        a = rot + k * (math.pi / 3.0)
        top_pts.append((cx + rx * math.cos(a), top_y + ry * math.sin(a)))
        bot_pts.append((cx + rx * 0.88 * math.cos(a), bot_y + ry * 0.88 * math.sin(a)))

    draw.polygon(bot_pts, fill=cyan_fill, outline=cyan_mid)
    for k in range(6):
        nxt = (k + 1) % 6
        draw.line([top_pts[k], top_pts[nxt]], fill=cyan_bright, width=max(1, int(2 * scale)))
        draw.line([bot_pts[k], bot_pts[nxt]], fill=cyan_mid, width=max(1, int(2 * scale)))
        draw.line([top_pts[k], bot_pts[k]], fill=cyan_mid, width=max(1, int(2 * scale)))
        draw.line([apex, top_pts[k]], fill=cyan_bright, width=max(1, int(2 * scale)))


def draw_docked_right_system_hud(
    canvas: Image.Image,
    t_norm: float,
    phase: float,
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    """
    Builds the 5-panel holographic stats & quest HUD matching the reference image,
    warps it with 3D perspective (angled inward from the right edge), and composites
    it semi-transparently onto the right side of the 1920x1080 frame.
    """
    src_w, src_h = 980, 560
    hud_src = Image.new("RGBA", (src_w, src_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(hud_src)

    cyan = (34, 211, 238)
    gold = (245, 190, 75)
    pulse = 0.5 + 0.5 * math.sin(phase * 2.0)

    # =========================================================================
    # 1. LEFT COLUMN: "Faction Stats" (Top) + "Construction Queue" (Bottom)
    # =========================================================================
    lx0, lx1 = 16, 304
    # Top-Left Panel: Faction Stats
    draw_translucent_holo_card(d, lx0, 36, lx1, 266, cyan, pulse, fill_alpha=76)
    d.text((lx0 + 62, 50), "Faction Stats", font=fonts["title"], fill=(235, 252, 255, 245))
    d.line([(lx0 + 18, 84), (lx1 - 18, 84)], fill=(34, 211, 238, 120), width=1)

    members = int(1500 + 25 * math.sin(phase))
    pwr = 8.5 + 0.2 * math.sin(phase * 2.0)
    d.text((lx0 + 20, 102), f"Members: {members:,}", font=fonts["body"], fill=(230, 248, 255, 240))
    d.text((lx0 + 20, 144), f"Power Level: {pwr:.1f}/10", font=fonts["body"], fill=(230, 248, 255, 240))
    d.text((lx0 + 20, 186), "Influence: Growing", font=fonts["body"], fill=(165, 243, 252, 240))

    # Bottom-Left Panel: Construction Queue
    draw_translucent_holo_card(d, lx0, 286, lx1, 514, cyan, pulse, fill_alpha=76)
    d.text((lx0 + 36, 300), "Construction Queue", font=fonts["title"], fill=(235, 252, 255, 245))
    d.line([(lx0 + 18, 334), (lx1 - 18, 334)], fill=(34, 211, 238, 120), width=1)

    # Mini isometric library wireframe on left + "Great Library / Tier 2" + progress bar
    draw_cyan_spirit_well_icon(d, lx0 + 74, 412, scale=0.82, phase=-phase)
    d.text((lx0 + 142, 368), "Great Library", font=fonts["sub"], fill=(235, 252, 255, 245))
    d.text((lx0 + 168, 396), "Tier 2", font=fonts["sub"], fill=(165, 243, 252, 235))
    cq_prog = 0.58 + 0.22 * (0.5 + 0.5 * math.sin(phase - 0.7))
    d.rounded_rectangle([lx0 + 138, 434, lx1 - 20, 448], radius=5, fill=(10, 32, 48, 140), outline=(34, 211, 238, 175), width=1)
    d.rounded_rectangle([lx0 + 140, 436, lx0 + 140 + int((lx1 - lx0 - 162) * cq_prog), 446], radius=4, fill=(103, 232, 249, 235))

    # =========================================================================
    # 2. CENTER TALL PANEL: Golden Wireframe Pagoda + Overlapping "Spirit Well Tier 2"
    # =========================================================================
    cx0, cx1 = 318, 636
    draw_translucent_holo_card(d, cx0, 14, cx1, 536, gold, pulse, fill_alpha=64)
    draw_isometric_pagoda_wireframe(d, (cx0 + cx1) // 2, 165, phase)

    # Sweeping vertical scanline across center panel
    scan_y = int(28 + (0.5 + 0.5 * math.sin(phase)) * 490)
    d.line([(cx0 + 8, scan_y), (cx1 - 8, scan_y)], fill=(254, 240, 138, 130), width=2)

    # Overlapping Bottom Sub-Card inside Center Panel: "Spirit Well Tier 2"
    draw_translucent_holo_card(d, cx0 + 14, 342, cx1 - 14, 522, cyan, pulse, fill_alpha=84)
    draw_cyan_spirit_well_icon(d, cx0 + 92, 428, scale=0.98, phase=phase)
    d.text((cx0 + 164, 384), "Spirit Well", font=fonts["title"], fill=(235, 252, 255, 245))
    d.text((cx0 + 186, 416), "Tier 2", font=fonts["sub"], fill=(165, 243, 252, 240))
    sw_prog = 0.44 + 0.26 * (0.5 + 0.5 * math.cos(phase))
    d.rounded_rectangle([cx0 + 158, 468, cx1 - 30, 482], radius=5, fill=(10, 32, 48, 140), outline=(34, 211, 238, 175), width=1)
    d.rounded_rectangle([cx0 + 160, 470, cx0 + 160 + int((cx1 - cx0 - 192) * sw_prog), 480], radius=4, fill=(103, 232, 249, 235))

    # =========================================================================
    # 3. RIGHT COLUMN: Two "Active Quests" Panels (Top Progress Cards + Bottom List)
    # =========================================================================
    rx0, rx1 = 650, 964
    # Top-Right Panel: Active Quests (2 quest cards with progress bars)
    draw_translucent_holo_card(d, rx0, 24, rx1, 308, cyan, pulse, fill_alpha=76)
    d.text((rx0 + 82, 38), "Active Quests", font=fonts["title"], fill=(235, 252, 255, 245))

    quest_cards = [
        ("Expand Territory", "Northward", 0.65 + 0.14 * (0.5 + 0.5 * math.sin(phase))),
        ("Spirit Well", "Tier 2", 0.32 + 0.16 * (0.5 + 0.5 * math.cos(phase))),
    ]
    for q_idx, (line1, line2, q_prog) in enumerate(quest_cards):
        qy0 = 78 + q_idx * 110
        qy1 = qy0 + 98
        d.rounded_rectangle([rx0 + 16, qy0, rx1 - 16, qy1], radius=8, fill=(12, 36, 54, 92), outline=(34, 211, 238, 150), width=1)

        # Mini cyan isometric shrine emblem on left of quest card
        draw_cyan_spirit_well_icon(d, rx0 + 54, qy0 + 48, scale=0.56, phase=phase + q_idx)
        d.text((rx0 + 96, qy0 + 12), line1, font=fonts["sub"], fill=(235, 252, 255, 245))
        d.text((rx0 + 96, qy0 + 36), line2, font=fonts["sub"], fill=(207, 250, 254, 240))

        # Progress bar + live percentage
        bx0, by0, bx1, by1 = rx0 + 96, qy0 + 68, rx1 - 74, qy0 + 80
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=4, fill=(8, 26, 42, 160), outline=(34, 211, 238, 150), width=1)
        fw = max(6, int((bx1 - bx0 - 2) * q_prog))
        d.rounded_rectangle([bx0 + 1, by0 + 1, bx0 + 1 + fw, by1 - 1], radius=3, fill=(103, 232, 249, 240))
        d.text((bx1 + 8, qy0 + 64), f"{int(q_prog * 100)}%", font=fonts["small"], fill=(224, 242, 254, 245))

    # Bottom-Right Panel: Active Quests (3 bulleted directives)
    draw_translucent_holo_card(d, rx0, 326, rx1, 526, cyan, pulse, fill_alpha=76)
    d.text((rx0 + 82, 340), "Active Quests", font=fonts["title"], fill=(235, 252, 255, 245))
    d.line([(rx0 + 18, 374), (rx1 - 18, 374)], fill=(34, 211, 238, 120), width=1)

    directives = [
        "Expand Territory Northward",
        "Diplomacy with Silent Peak",
        "Diplomacy with Strong Faction",
    ]
    for d_idx, d_txt in enumerate(directives):
        dy = 392 + d_idx * 40
        gx, gy = rx0 + 28, dy + 11
        blink = int(175 + 80 * math.sin(phase * 3.0 + d_idx))
        d.polygon([(gx, gy - 6), (gx + 6, gy), (gx, gy + 6), (gx - 6, gy)], fill=(103, 232, 249, blink))
        d.text((rx0 + 44, dy), d_txt, font=fonts["small"], fill=(235, 252, 255, 245))

    # Floating luminous cyan & gold spirit orbs drifting around the HUD
    orb_rng = random.Random(77)
    for o_i in range(18):
        ox0 = orb_rng.uniform(10, src_w - 10)
        oy0 = orb_rng.uniform(10, src_h - 10)
        orad = orb_rng.choice([3, 4, 5, 7])
        col = (103, 232, 249) if o_i % 3 != 0 else (254, 215, 102)
        u = (t_norm + o_i / 18.0) % 1.0
        ox = ox0 + 14.0 * math.sin(phase * 2.0 + o_i)
        oy = (oy0 - u * 95.0) % src_h
        oa = int(190 * (0.4 + 0.6 * abs(math.sin(phase * 2.0 + o_i * 1.1))))
        d.ellipse([ox - orad - 3, oy - orad - 3, ox + orad + 3, oy + orad + 3], fill=(*col, oa // 4))
        d.ellipse([ox - orad, oy - orad, ox + orad, oy + orad], fill=(*col, oa))

    # =========================================================================
    # 3D PERSPECTIVE WARP: Docked on Right Side & Angled Toward Viewer
    # =========================================================================
    # Left edge (closer to center screen) is slightly narrower vertically (foreshortened);
    # Right edge (docked along right side) is taller, creating an authentic 3D angled HUD plane.
    src_quad = [(0.0, 0.0), (float(src_w), 0.0), (float(src_w), float(src_h)), (0.0, float(src_h))]
    dst_quad = [
        (1005.0, 92.0),   # Top-Left (angled inward)
        (1885.0, 42.0),   # Top-Right (docked right, taller)
        (1885.0, 565.0),  # Bottom-Right (sits cleanly above LIKE/SHARE/SUBSCRIBE at y=585)
        (1005.0, 505.0),  # Bottom-Left (angled inward)
    ]
    coeffs = _find_perspective_coeffs(src_quad, dst_quad)
    warped = hud_src.transform(
        (WIDTH, HEIGHT),
        Image.Transform.PERSPECTIVE,
        coeffs,
        resample=Image.Resampling.BICUBIC,
    )
    canvas.alpha_composite(warped)


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
    bx, by = 75, 595
    bw, bh = 420, 255
    mid_x = bx + bw // 2

    draw.rounded_rectangle([bx + 8, by + 12, bx + bw + 8, by + bh + 12], radius=16, fill=(8, 8, 14, 165))
    draw.rounded_rectangle(
        [bx, by, bx + bw, by + bh],
        radius=14,
        fill=(40, 16, 26, 250),
        outline=(217, 160, 54, 255),
        width=4,
    )

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

    ink_normal = (176, 158, 130, 200)
    for row in range(7):
        ly = by + 32 + row * 27
        l_x0 = bx + (48 if row < 3 else 30)
        l_x1 = mid_x - 18
        draw.line([(l_x0, ly), (l_x1, ly)], fill=ink_normal, width=2)

        r_x0 = mid_x + 18
        r_x1 = bx + bw - 30
        draw.line([(r_x0, ly), (r_x1, ly)], fill=ink_normal, width=2)

    draw.line([(mid_x, by + pad_top + 4), (mid_x, by + bh - pad_bot + 4)], fill=(95, 72, 48, 255), width=4)
    rx = bx + 42
    draw.polygon(
        [(rx, by + pad_top), (rx + 24, by + pad_top), (rx + 24, by + 95), (rx + 12, by + 78), (rx, by + 95)],
        fill=(185, 28, 44, 255),
        outline=(245, 195, 80, 255),
    )

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

        x_left = min(mid_x, p_x) + 12
        x_right = max(mid_x, p_x) - 12
        if x_right - x_left > 14:
            for row in range(6):
                ly_f = by + 36 + row * 28 - int(lift_y * 0.55)
                draw.line([(x_left, ly_f), (x_right, ly_f)], fill=(168, 150, 122, 195), width=2)

    hx = 615
    hy = 755
    pulse = 0.5 + 0.5 * math.sin(phase * 4.0)

    draw.ellipse([hx - 95, hy + 68, hx + 95, hy + 104], fill=(8, 8, 14, 165))

    arch_box = [hx - 78, hy - 115, hx + 78, hy + 45]
    draw.arc(arch_box, start=180, end=360, fill=(28, 24, 36, 255), width=16)
    draw.arc(arch_box, start=180, end=360, fill=(234, 170, 46, 255), width=3)
    inner_box = [hx - 64, hy - 101, hx + 64, hy + 31]
    draw.arc(inner_box, start=192, end=348, fill=(58, 24, 36, 255), width=8)

    draw.line([(hx - 76, hy - 35), (hx - 72, hy + 12)], fill=(234, 170, 46, 255), width=5)
    draw.line([(hx + 76, hy - 35), (hx + 72, hy + 12)], fill=(234, 170, 46, 255), width=5)

    draw.rounded_rectangle([hx - 92, hy - 8, hx - 48, hy + 76], radius=20, fill=(32, 22, 34, 255), outline=(234, 170, 46, 255), width=3)
    draw.rounded_rectangle([hx - 54, hy - 2, hx - 36, hy + 70], radius=10, fill=(54, 24, 34, 255), outline=(180, 130, 50, 255), width=2)
    draw.ellipse([hx - 82, hy + 16, hx - 58, hy + 52], outline=(254, 224, 130, int(170 + 85 * pulse)), width=2)

    draw.rounded_rectangle([hx + 48, hy - 8, hx + 92, hy + 76], radius=20, fill=(32, 22, 34, 255), outline=(234, 170, 46, 255), width=3)
    draw.rounded_rectangle([hx + 36, hy - 2, hx + 54, hy + 70], radius=10, fill=(54, 24, 34, 255), outline=(180, 130, 50, 255), width=2)
    draw.ellipse([hx + 58, hy + 16, hx + 82, hy + 52], outline=(254, 224, 130, int(170 + 85 * pulse)), width=2)

    wave_streams = [
        (0.00, hx - 58, hy - 18, -32, 240, (254, 243, 199), (245, 158, 11)),
        (0.20, hx, hy - 112, 0, 220, (254, 240, 138), (234, 170, 46)),
        (0.40, hx + 58, hy - 18, 36, 245, (255, 251, 235), (217, 119, 6)),
        (0.60, hx - 32, hy - 78, -18, 230, (209, 250, 229), (16, 185, 129)),
        (0.80, hx + 32, hy - 78, 22, 235, (254, 226, 226), (225, 29, 72)),
    ]

    for idx_w, (off_t, sx, sy, t_dx, lift_h, core_rgb, glow_rgb) in enumerate(wave_streams):
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

            draw.rounded_rectangle(
                [bx_i - 2, cur_y - bh_m / 2.0 - 2, bx_i + mb_w + 2, cur_y + bh_m / 2.0 + 2],
                radius=3,
                fill=(*glow_rgb, max(6, alpha // 3)),
            )
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
    hud_fonts = {
        "title": load_font(22, serif=False),
        "sub": load_font(18, serif=False),
        "body": load_font(19, serif=False),
        "small": load_font(15, serif=False),
    }

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
        draw_docked_right_system_hud(frame, t_norm, phase, hud_fonts)
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
