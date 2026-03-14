#!/usr/bin/env python3
"""
Generate a poster for spot-diff game by compositing scene thumbnails
into a grid with title overlay.

Usage: ~/miniconda3/bin/python3 generate_poster.py
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("PIL not found. Use: ~/miniconda3/bin/python3 generate_poster.py")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")
OUT_PATH = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "poster.png")

# Poster: 1:1 square, 1024×1024
POSTER_W, POSTER_H = 1024, 1024
LEVELS = ["algram", "jenny", "jmf", "ghostpixel", "isaya", "isabel"]


def main():
    # Load base images
    imgs = []
    for level_id in LEVELS:
        path = os.path.join(IMG_DIR, level_id, "base.png")
        if not os.path.exists(path):
            print(f"  Missing: {path}")
            return
        imgs.append(Image.open(path).convert("RGB"))

    # Create poster canvas
    poster = Image.new("RGB", (POSTER_W, POSTER_H), (15, 15, 30))
    draw = ImageDraw.Draw(poster)

    # Layout: 3×2 grid of scene thumbnails, with dark overlay + title
    cols, rows = 3, 2
    pad = 6
    cell_w = (POSTER_W - pad * (cols + 1)) // cols
    cell_h = (POSTER_H - 200 - pad * (rows + 1)) // rows  # leave 200px for title area
    title_h = 200

    # Draw scene grid below title area
    for i, img in enumerate(imgs):
        col = i % cols
        row = i // cols
        x = pad + col * (cell_w + pad)
        y = title_h + pad + row * (cell_h + pad)

        # Resize to fill cell
        thumb = img.copy()
        thumb = thumb.resize((cell_w, cell_h), Image.LANCZOS)
        poster.paste(thumb, (x, y))

        # Slight border
        draw.rectangle([x - 1, y - 1, x + cell_w, y + cell_h], outline=(60, 60, 100), width=2)

    # Dark gradient overlay at top for title
    for y in range(title_h):
        alpha = int(220 * (1 - y / title_h))
        draw.line([(0, y), (POSTER_W, y)], fill=(15, 15, 35, alpha))

    # Title text - use basic font since custom fonts may not be available
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
        sub_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # Draw title
    title = "SPOT THE DIFFERENCE"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((POSTER_W - tw) // 2, 40), title, font=title_font, fill=(255, 255, 255))

    # Subtitle
    sub = "6 Scenes  •  30 Differences  •  Find Them All"
    bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
    sw = bbox2[2] - bbox2[0]
    draw.text(((POSTER_W - sw) // 2, 130), sub, font=sub_font, fill=(180, 180, 220))

    # Magnifying glass emoji area (simple circle)
    cx, cy = POSTER_W // 2, title_h - 10
    draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], outline=(100, 150, 255), width=3)
    draw.line([(cx + 18, cy + 18), (cx + 35, cy + 35)], fill=(100, 150, 255), width=3)

    poster.save(OUT_PATH, "PNG", optimize=True)
    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"✓ Poster saved: {OUT_PATH} ({size_kb} KB)")


if __name__ == "__main__":
    main()
