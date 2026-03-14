#!/usr/bin/env python3
"""
Generate diff images from base images by applying 5 visible modifications per level.

Modifications include: color shifts, object removal (fill with nearby color),
adding shapes, changing brightness in regions, etc.

Usage: ~/miniconda3/bin/python3 generate_diffs.py

This also outputs the exact normalized coordinates for each diff region,
which should be pasted into levels/index.ts.
"""

import os
import sys
import json

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    sys.exit("PIL not found. Use: ~/miniconda3/bin/python3 generate_diffs.py")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")

# Each level: list of 5 modifications
# Each mod: (norm_cx, norm_cy, norm_r, type, params, label_zh, label_en)
# Types: "hue_shift", "brighten", "darken", "add_circle", "add_rect", "remove"

LEVEL_MODS = {
    "algram": [
        (0.08, 0.45, 0.055, "hue_shift", {"shift": 80}, "吉他颜色", "Guitar color"),
        (0.35, 0.35, 0.050, "brighten", {"factor": 1.8}, "音箱指示灯", "Amp indicator"),
        (0.72, 0.28, 0.055, "hue_shift", {"shift": 120}, "唱片封面", "Vinyl cover"),
        (0.40, 0.85, 0.050, "darken", {"factor": 0.3}, "踏板灯", "Pedal light"),
        (0.88, 0.35, 0.045, "add_circle", {"color": (200, 50, 50)}, "谱架标记", "Sheet mark"),
    ],
    "jenny": [
        (0.28, 0.35, 0.055, "hue_shift", {"shift": 90}, "屏幕代码", "Screen code"),
        (0.38, 0.72, 0.050, "hue_shift", {"shift": 60}, "咖啡杯", "Coffee mug"),
        (0.35, 0.12, 0.050, "brighten", {"factor": 2.0}, "便签颜色", "Sticky note"),
        (0.50, 0.75, 0.050, "add_circle", {"color": (50, 200, 50)}, "键盘灯", "Keyboard LED"),
        (0.78, 0.55, 0.050, "hue_shift", {"shift": 100}, "猫咪颜色", "Cat color"),
    ],
    "jmf": [
        (0.20, 0.35, 0.055, "hue_shift", {"shift": 100}, "终端文字", "Terminal text"),
        (0.82, 0.40, 0.050, "brighten", {"factor": 2.5}, "服务器灯", "Server LED"),
        (0.50, 0.25, 0.050, "add_rect", {"color": (0, 255, 0)}, "屏幕图标", "Screen icon"),
        (0.45, 0.85, 0.050, "hue_shift", {"shift": 150}, "线缆颜色", "Cable color"),
        (0.70, 0.80, 0.050, "darken", {"factor": 0.2}, "能量饮料", "Energy drink"),
    ],
    "ghostpixel": [
        (0.18, 0.25, 0.055, "hue_shift", {"shift": 70}, "浮空书本", "Floating book"),
        (0.50, 0.45, 0.050, "brighten", {"factor": 2.5}, "传送门光芒", "Portal glow"),
        (0.65, 0.30, 0.050, "hue_shift", {"shift": 130}, "幽灵颜色", "Ghost color"),
        (0.12, 0.45, 0.055, "add_circle", {"color": (150, 100, 255)}, "镜中光点", "Mirror light"),
        (0.45, 0.90, 0.050, "darken", {"factor": 0.3}, "地毯花纹", "Rug pattern"),
    ],
    "isaya": [
        (0.18, 0.50, 0.055, "hue_shift", {"shift": 80}, "画板颜料", "Canvas paint"),
        (0.52, 0.30, 0.050, "hue_shift", {"shift": 100}, "黑猫颜色", "Cat color"),
        (0.58, 0.45, 0.050, "brighten", {"factor": 1.8}, "耳机颜色", "Headphone color"),
        (0.22, 0.85, 0.050, "add_circle", {"color": (255, 200, 50)}, "颜料色块", "Paint spot"),
        (0.82, 0.70, 0.045, "darken", {"factor": 0.3}, "床上物品", "Bed item"),
    ],
    "isabel": [
        (0.20, 0.65, 0.055, "hue_shift", {"shift": 90}, "玫瑰花色", "Rose color"),
        (0.48, 0.30, 0.050, "brighten", {"factor": 1.8}, "镜中倒影", "Mirror reflection"),
        (0.75, 0.45, 0.050, "hue_shift", {"shift": 120}, "百合花色", "Lily color"),
        (0.42, 0.60, 0.050, "add_circle", {"color": (255, 150, 200)}, "珠宝盒", "Jewelry box"),
        (0.70, 0.70, 0.045, "darken", {"factor": 0.3}, "香水瓶", "Perfume bottle"),
    ],
}


def apply_hue_shift(img, cx, cy, radius, shift):
    """Shift hue in a circular region."""
    w, h = img.size
    px_cx, px_cy = int(cx * w), int(cy * h)
    px_r = int(radius * max(w, h))

    hsv = img.convert("HSV")
    pixels = hsv.load()

    for y in range(max(0, px_cy - px_r), min(h, px_cy + px_r)):
        for x in range(max(0, px_cx - px_r), min(w, px_cx + px_r)):
            dx, dy = x - px_cx, y - px_cy
            if dx * dx + dy * dy <= px_r * px_r:
                hh, s, v = pixels[x, y]
                pixels[x, y] = ((hh + shift) % 256, s, v)

    return hsv.convert("RGB")


def apply_brighten(img, cx, cy, radius, factor):
    """Brighten or darken a circular region."""
    w, h = img.size
    px_cx, px_cy = int(cx * w), int(cy * h)
    px_r = int(radius * max(w, h))

    pixels = img.load()
    for y in range(max(0, px_cy - px_r), min(h, px_cy + px_r)):
        for x in range(max(0, px_cx - px_r), min(w, px_cx + px_r)):
            dx, dy = x - px_cx, y - px_cy
            if dx * dx + dy * dy <= px_r * px_r:
                r, g, b = pixels[x, y][:3]
                pixels[x, y] = (
                    min(255, int(r * factor)),
                    min(255, int(g * factor)),
                    min(255, int(b * factor)),
                )
    return img


def apply_add_shape(img, cx, cy, radius, color, shape="circle"):
    """Add a colored shape."""
    w, h = img.size
    px_cx, px_cy = int(cx * w), int(cy * h)
    px_r = int(radius * max(w, h))

    draw = ImageDraw.Draw(img)
    if shape == "circle":
        draw.ellipse(
            [px_cx - px_r // 2, px_cy - px_r // 2, px_cx + px_r // 2, px_cy + px_r // 2],
            fill=color,
        )
    else:
        draw.rectangle(
            [px_cx - px_r // 2, px_cy - px_r // 3, px_cx + px_r // 2, px_cy + px_r // 3],
            fill=color,
        )
    return img


def process_level(level_id, mods):
    base_path = os.path.join(IMG_DIR, level_id, "base.png")
    diff_path = os.path.join(IMG_DIR, level_id, "diff.png")

    if not os.path.exists(base_path):
        print(f"  ⏭ Skipping {level_id} — no base.png")
        return None

    img = Image.open(base_path).convert("RGB")
    print(f"\n  Processing {level_id} ({img.size[0]}×{img.size[1]})")

    diffs = []
    for i, (cx, cy, r, mod_type, params, label_zh, label_en) in enumerate(mods):
        diff_id = f"{level_id[0]}{i+1}"
        print(f"    [{diff_id}] {mod_type} at ({cx:.2f}, {cy:.2f}) — {label_en}")

        if mod_type == "hue_shift":
            img = apply_hue_shift(img, cx, cy, r, params["shift"])
        elif mod_type == "brighten":
            img = apply_brighten(img, cx, cy, r, params["factor"])
        elif mod_type == "darken":
            img = apply_brighten(img, cx, cy, r, params["factor"])
        elif mod_type == "add_circle":
            img = apply_add_shape(img, cx, cy, r, params["color"], "circle")
        elif mod_type == "add_rect":
            img = apply_add_shape(img, cx, cy, r, params["color"], "rect")

        diffs.append({
            "id": diff_id,
            "cx": cx,
            "cy": cy,
            "r": r,
            "label_zh": label_zh,
            "label_en": label_en,
        })

    img.save(diff_path, "PNG")
    size_kb = os.path.getsize(diff_path) // 1024
    print(f"  ✓ Saved diff.png ({size_kb} KB)")

    return diffs


def main():
    print("Generating diff images from base images…")

    all_coords = {}
    for level_id, mods in LEVEL_MODS.items():
        result = process_level(level_id, mods)
        if result:
            all_coords[level_id] = result

    # Output coordinate data for levels/index.ts
    print(f"\n{'='*60}")
    print("Diff coordinates for levels/index.ts:")
    print(f"{'='*60}")
    for level_id, diffs in all_coords.items():
        print(f"\n// {level_id}")
        print("differences: [")
        for d in diffs:
            print(f"  {{ id: '{d['id']}', cx: {d['cx']}, cy: {d['cy']}, r: {d['r']}, "
                  f"label_zh: '{d['label_zh']}', label_en: '{d['label_en']}' }},")
        print("],")

    print(f"\n✓ Done: {len(all_coords)} diff images generated")


if __name__ == "__main__":
    main()
