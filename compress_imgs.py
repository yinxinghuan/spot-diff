#!/usr/bin/env python3
"""Compress level images to reduce bundle size. Target: ~200-400KB per image."""

import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("PIL not found. Use: ~/miniconda3/bin/python3 compress_imgs.py")

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "src", "SpotDiff", "img", "levels")

# Target max dimension (retina 2x for 390×280 display)
MAX_W, MAX_H = 780, 560
QUALITY = 85


def compress(path):
    img = Image.open(path)
    orig_size = os.path.getsize(path)

    # Resize if larger than target
    w, h = img.size
    if w > MAX_W or h > MAX_H:
        ratio = min(MAX_W / w, MAX_H / h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # Save as optimized PNG
    img.save(path, "PNG", optimize=True)
    new_size = os.path.getsize(path)
    saved = orig_size - new_size
    print(f"  {os.path.basename(os.path.dirname(path))}/{os.path.basename(path)}: "
          f"{orig_size//1024}KB → {new_size//1024}KB (saved {saved//1024}KB)")


def main():
    print("Compressing level images…")
    for level_dir in sorted(os.listdir(IMG_DIR)):
        level_path = os.path.join(IMG_DIR, level_dir)
        if not os.path.isdir(level_path):
            continue
        for fname in ["base.png", "diff.png"]:
            fpath = os.path.join(level_path, fname)
            if os.path.exists(fpath):
                compress(fpath)
    print("Done!")


if __name__ == "__main__":
    main()
