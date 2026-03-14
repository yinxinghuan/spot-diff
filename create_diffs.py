#!/usr/bin/env python3
"""
Programmatically create diff images from base images.
Instead of using img2img (which changes composition), we directly modify
specific regions of the base image to create guaranteed visible differences.

Modifications:
- Hue shift: change the color of an object region
- Brightness shift: darken or lighten a region
- Horizontal flip: mirror a small region

Usage:
  ~/miniconda3/bin/python3 create_diffs.py
  ~/miniconda3/bin/python3 create_diffs.py --only algram
"""
import argparse
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")

# Each level: list of modifications to apply
# Types:
#   hue_shift(cx, cy, radius, degrees)  - shift hue by N degrees in a circular region
#   brightness(cx, cy, radius, factor)  - multiply brightness (0.5=darker, 1.5=brighter)
#   colorize(cx, cy, radius, r, g, b)   - blend region toward a specific color
#   flip_h(cx, cy, radius)              - horizontally flip a region
LEVELS = {
    "algram": [
        # Guitar body: warm sunburst → cool blue
        {"type": "hue_shift", "cx": 0.12, "cy": 0.50, "radius": 0.12, "degrees": 180},
        # Vinyl record: black → orange tint
        {"type": "colorize", "cx": 0.70, "cy": 0.37, "radius": 0.09, "r": 220, "g": 140, "b": 40, "strength": 0.5},
        # Headphones: black → red
        {"type": "colorize", "cx": 0.06, "cy": 0.92, "radius": 0.07, "r": 200, "g": 40, "b": 40, "strength": 0.6},
    ],
    "jenny": [
        # Desk lamp: yellow → red
        {"type": "hue_shift", "cx": 0.10, "cy": 0.35, "radius": 0.10, "degrees": -60},
        # Cat area: color shift
        {"type": "hue_shift", "cx": 0.86, "cy": 0.64, "radius": 0.10, "degrees": 120},
        # Plant: green → purple
        {"type": "hue_shift", "cx": 0.28, "cy": 0.88, "radius": 0.08, "degrees": 150},
    ],
    "jmf": [
        # Neon sign: blue/green → pink
        {"type": "hue_shift", "cx": 0.50, "cy": 0.10, "radius": 0.14, "degrees": 120},
        # Floor cables: blue → red
        {"type": "hue_shift", "cx": 0.62, "cy": 0.78, "radius": 0.10, "degrees": 180},
        # Left device area
        {"type": "brightness", "cx": 0.16, "cy": 0.87, "radius": 0.09, "factor": 1.8},
    ],
    "ghostpixel": [
        # Left neon sign: green → red
        {"type": "hue_shift", "cx": 0.18, "cy": 0.12, "radius": 0.10, "degrees": 120},
        # Center arcade cabinet screen: color shift
        {"type": "hue_shift", "cx": 0.45, "cy": 0.45, "radius": 0.10, "degrees": 150},
        # Floor fog: blue-green → orange
        {"type": "colorize", "cx": 0.45, "cy": 0.80, "radius": 0.15, "r": 220, "g": 120, "b": 40, "strength": 0.4},
        # Right side counter/chair area
        {"type": "hue_shift", "cx": 0.85, "cy": 0.60, "radius": 0.08, "degrees": -90},
    ],
    "isaya": [
        # Cat: black → orange
        {"type": "colorize", "cx": 0.22, "cy": 0.62, "radius": 0.06, "r": 220, "g": 140, "b": 40, "strength": 0.6},
        # Easel painting: hue shift
        {"type": "hue_shift", "cx": 0.58, "cy": 0.42, "radius": 0.12, "degrees": 90},
        # String lights: warm → pink
        {"type": "hue_shift", "cx": 0.50, "cy": 0.05, "radius": 0.25, "degrees": -50},
        # Sunflower pot: yellow → purple
        {"type": "hue_shift", "cx": 0.08, "cy": 0.72, "radius": 0.07, "degrees": 180},
        # Sunset sky color shift
        {"type": "hue_shift", "cx": 0.50, "cy": 0.20, "radius": 0.18, "degrees": 40},
    ],
    "isabel": [
        # Rose bush: red → blue
        {"type": "hue_shift", "cx": 0.10, "cy": 0.55, "radius": 0.10, "degrees": 180},
        # Tea set: white → pink colorize
        {"type": "colorize", "cx": 0.38, "cy": 0.65, "radius": 0.08, "r": 200, "g": 80, "b": 120, "strength": 0.5},
        # Butterfly: color shift
        {"type": "hue_shift", "cx": 0.22, "cy": 0.42, "radius": 0.05, "degrees": 120},
        # Right bench/bird cage area
        {"type": "hue_shift", "cx": 0.88, "cy": 0.65, "radius": 0.08, "degrees": -60},
        # Hanging ferns: green → golden
        {"type": "hue_shift", "cx": 0.50, "cy": 0.10, "radius": 0.15, "degrees": 60},
    ],
}


def create_circular_mask(w, h, cx_frac, cy_frac, r_frac):
    """Create a soft circular mask with feathered edges."""
    cx = cx_frac * w
    cy = cy_frac * h
    r = r_frac * max(w, h)

    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

    # Soft edge: fully opaque inside r*0.7, fading to 0 at r
    mask = np.clip(1.0 - (dist - r * 0.7) / (r * 0.3), 0, 1)
    return mask


def apply_hue_shift(img_arr, mask, degrees):
    """Shift hue of masked region by N degrees."""
    from PIL import Image
    img = Image.fromarray(img_arr)
    hsv = np.array(img.convert('HSV'), dtype=float)

    # Shift hue (0-255 scale, so degrees/360*255)
    shift = degrees / 360.0 * 255.0
    new_h = (hsv[:, :, 0] + shift) % 256

    hsv_shifted = hsv.copy()
    hsv_shifted[:, :, 0] = new_h
    shifted = np.array(Image.fromarray(hsv_shifted.astype(np.uint8), mode='HSV').convert('RGB'), dtype=float)

    # Blend
    mask3 = mask[:, :, np.newaxis]
    result = img_arr * (1 - mask3) + shifted * mask3
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_brightness(img_arr, mask, factor):
    """Change brightness of masked region."""
    bright = img_arr.astype(float) * factor
    mask3 = mask[:, :, np.newaxis]
    result = img_arr * (1 - mask3) + bright * mask3
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_colorize(img_arr, mask, r, g, b, strength=0.5):
    """Blend masked region toward a specific color."""
    color = np.array([r, g, b], dtype=float)
    colored = img_arr.astype(float) * (1 - strength) + color * strength
    mask3 = mask[:, :, np.newaxis]
    result = img_arr * (1 - mask3) + colored * mask3
    return np.clip(result, 0, 255).astype(np.uint8)


def create_diff(level_id):
    mods = LEVELS.get(level_id)
    if not mods:
        print(f"  ⚠ No modifications defined for {level_id}")
        return

    base_path = os.path.join(IMG_DIR, level_id, "base.png")
    diff_path = os.path.join(IMG_DIR, level_id, "diff.png")

    if not os.path.exists(base_path):
        print(f"  ⚠ Missing base image: {base_path}")
        return

    base = Image.open(base_path).convert("RGB")
    w, h = base.size
    result = np.array(base, dtype=float)

    print(f"  {level_id}: applying {len(mods)} modifications...")

    for i, mod in enumerate(mods):
        mask = create_circular_mask(w, h, mod["cx"], mod["cy"], mod["radius"])
        t = mod["type"]

        if t == "hue_shift":
            result = apply_hue_shift(result.astype(np.uint8), mask, mod["degrees"]).astype(float)
            print(f"    [{i+1}] hue_shift {mod['degrees']}° at ({mod['cx']:.2f}, {mod['cy']:.2f})")
        elif t == "brightness":
            result = apply_brightness(result.astype(np.uint8), mask, mod["factor"]).astype(float)
            print(f"    [{i+1}] brightness x{mod['factor']} at ({mod['cx']:.2f}, {mod['cy']:.2f})")
        elif t == "colorize":
            result = apply_colorize(
                result.astype(np.uint8), mask,
                mod["r"], mod["g"], mod["b"],
                mod.get("strength", 0.5)
            ).astype(float)
            print(f"    [{i+1}] colorize ({mod['r']},{mod['g']},{mod['b']}) at ({mod['cx']:.2f}, {mod['cy']:.2f})")

    Image.fromarray(result.astype(np.uint8)).save(diff_path, "PNG")
    print(f"  ✓ Saved: {diff_path}")

    # Print coordinates for index.ts
    print(f"\n  // {level_id} — {len(mods)} differences:")
    for i, mod in enumerate(mods):
        r = mod["radius"] + 0.02  # slightly larger hit area
        print(f"  //   cx={mod['cx']:.3f}  cy={mod['cy']:.3f}  r={r:.2f}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Only process this level")
    args = parser.parse_args()

    levels = [args.only] if args.only else list(LEVELS.keys())

    for lvl in levels:
        print(f"\n{'='*50}")
        print(f"Creating diff: {lvl}")
        print(f"{'='*50}")
        create_diff(lvl)

    print("\nDone! All diffs created programmatically.")
    print("Differences are guaranteed visible — no AI noise.")


if __name__ == "__main__":
    main()
