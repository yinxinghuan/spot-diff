#!/usr/bin/env python3
"""
Post-process diff images: keep only the top N largest visible differences,
replace everything else with base image pixels. Eliminates subtle AI noise.

Usage:
  ~/miniconda3/bin/python3 clean_diffs.py                # clean all levels
  ~/miniconda3/bin/python3 clean_diffs.py --only algram   # clean one level
"""
import argparse
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")

# How many differences to keep per level
DIFF_COUNTS = {
    "algram": 3,
    "jenny": 3,
    "jmf": 3,
    "ghostpixel": 3,
    "isaya": 3,
    "isabel": 3,
}

THRESHOLD = 35       # pixel difference threshold
MIN_REGION_SIZE = 200  # minimum pixels to count as a region
MAX_REGION_SIZE = 200000  # skip regions larger than this (composition change, not detail)
EXPAND_PX = 15        # expand each kept region by this many pixels (feathered edge)


def clean_diff(level_id):
    n_keep = DIFF_COUNTS.get(level_id, 3)
    base_path = os.path.join(IMG_DIR, level_id, "base.png")
    diff_path = os.path.join(IMG_DIR, level_id, "diff.png")

    if not os.path.exists(base_path) or not os.path.exists(diff_path):
        print(f"  ⚠ Skipping {level_id}: missing base or diff")
        return

    base = Image.open(base_path).convert("RGB")
    diff = Image.open(diff_path).convert("RGB")
    if diff.size != base.size:
        diff = diff.resize(base.size, Image.LANCZOS)

    w, h = base.size
    ba = np.array(base, dtype=float)
    da = np.array(diff, dtype=float)

    # Find pixel differences
    delta = np.sqrt(np.sum((ba - da) ** 2, axis=2))
    mask = delta > THRESHOLD

    # Label connected regions
    labeled, num_features = ndimage.label(mask)
    regions = []
    oversized = 0
    for i in range(1, num_features + 1):
        region_mask = labeled == i
        size = np.sum(region_mask)
        if size < MIN_REGION_SIZE:
            continue
        if size > MAX_REGION_SIZE:
            oversized += 1
            continue  # skip composition-level changes
        ys, xs = np.where(region_mask)
        cy = np.mean(ys) / h
        cx = np.mean(xs) / w
        regions.append((size, i, cx, cy))

    regions.sort(reverse=True)
    kept = regions[:n_keep]

    if oversized:
        print(f"  ⚠ Skipped {oversized} oversized regions (>{MAX_REGION_SIZE}px)")
    print(f"  {level_id}: {len(regions)} usable regions found, keeping top {len(kept)}:")
    for sz, idx, cx, cy in kept:
        print(f"    size={sz:6d}  cx={cx:.3f}  cy={cy:.3f}")

    # Build a mask of pixels to keep from diff image
    keep_mask = np.zeros((h, w), dtype=bool)
    for _, idx, _, _ in kept:
        keep_mask |= (labeled == idx)

    # Expand the kept regions with dilation for smooth edges
    struct = ndimage.generate_binary_structure(2, 2)
    keep_mask = ndimage.binary_dilation(keep_mask, structure=struct, iterations=EXPAND_PX)

    # Create gaussian feathered edge
    keep_float = keep_mask.astype(float)
    # Apply slight blur for soft transition
    from PIL import ImageFilter as IF
    keep_pil = Image.fromarray((keep_float * 255).astype(np.uint8), mode='L')
    keep_pil = keep_pil.filter(IF.GaussianBlur(radius=5))
    keep_float = np.array(keep_pil, dtype=float) / 255.0

    # Blend: where keep_mask=1 use diff, where keep_mask=0 use base
    keep_3d = keep_float[:, :, np.newaxis]
    result = ba * (1 - keep_3d) + da * keep_3d
    result = np.clip(result, 0, 255).astype(np.uint8)

    # Save
    Image.fromarray(result).save(diff_path, "PNG")
    print(f"  ✓ Cleaned diff saved: {diff_path}")

    # Output coordinates for levels/index.ts
    print(f"\n  // {level_id} coordinates:")
    for i, (sz, _, cx, cy) in enumerate(kept):
        r = 0.14 if sz > 10000 else 0.12 if sz > 3000 else 0.10
        print(f"  //   cx={cx:.3f}  cy={cy:.3f}  r={r}  size={sz}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Only clean this level")
    args = parser.parse_args()

    levels = [args.only] if args.only else list(DIFF_COUNTS.keys())

    for lvl in levels:
        print(f"\n{'='*50}")
        print(f"Cleaning: {lvl}")
        print(f"{'='*50}")
        clean_diff(lvl)

    print("\nDone! All noise removed, only clear differences remain.")


if __name__ == "__main__":
    main()
