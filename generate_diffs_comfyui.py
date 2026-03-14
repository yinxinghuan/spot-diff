#!/usr/bin/env python3
"""
Generate diff images for spot-diff game using ComfyUI (Flux2 Klein edit workflow).
Uses the base image as both reference images + prompt conditioning for maximum consistency.

Requirements:
  - ComfyUI running at http://127.0.0.1:8188
  - User must start ComfyUI manually before running this script

Usage:
  ~/miniconda3/bin/python3 generate_diffs_comfyui.py
  ~/miniconda3/bin/python3 generate_diffs_comfyui.py --only ghostpixel
  ~/miniconda3/bin/python3 generate_diffs_comfyui.py --only ghostpixel --denoise 0.25
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
from PIL import Image

COMFYUI_URL = "http://127.0.0.1:8188"
COMFYUI_INPUT = "/Users/yin/ComfyUI/input"
COMFYUI_OUTPUT = "/Users/yin/ComfyUI/output"
WORKFLOW_PATH = "/Users/yin/ComfyUI/user/default/workflows/flux2_klein_edit_workflow.json"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")

# Diff prompts — describe the scene WITH the changes you want
# Keep as close to the base scene description as possible, only change specific items
DIFFS = {
    "ghostpixel": (
        "anime illustration of a dark game developer study room interior at night, "
        "triple monitor setup with dark code editor on screens, mechanical keyboard with RGB, "
        "anime figurines and collectible toys on shelves, LED strip lights in RED, "
        "ORANGE gaming headset on desk, stack of manga books, GREEN energy drink cans, "
        "small ghost plushie on monitor, dark curtains, ambient RED glow, "
        "posters of retro games on wall, cables everywhere, "
        "detailed anime background art style, moody atmosphere, no people"
    ),
    "isaya": (
        "anime illustration of a cozy Japanese style art studio room interior, "
        "wooden easel with half-finished LANDSCAPE painting, tatami mat floor, "
        "ORANGE tabby cat sleeping on cushion near low table, calligraphy brushes in jar, "
        "PINK paper lantern hanging from ceiling, sliding door with garden view, "
        "watercolor palette and paint tubes on table, tea cup, small bonsai tree, "
        "SUNFLOWER branch in vase, warm afternoon sunlight, "
        "detailed anime background art style, peaceful zen atmosphere, no people"
    ),
    "isabel": (
        "anime illustration of a charming French flower shop interior, "
        "wooden counter with wrapped bouquets, hanging dried flower bundles from ceiling, "
        "vintage cash register, GREEN ribbon spools and scissors on counter, "
        "large bucket of fresh YELLOW SUNFLOWERS, small potted orchids, "
        "GREEN lace curtains on window, BLUE vintage bicycle with flower basket outside window, "
        "chalkboard menu sign, fairy lights on shelves, PURPLE colored walls, "
        "detailed anime background art style, romantic atmosphere, no people"
    ),
}


def check_comfyui():
    """Check if ComfyUI is running."""
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3)
        return True
    except Exception:
        return False


def upload_image(src_path, name):
    """Copy image to ComfyUI input folder."""
    dst = os.path.join(COMFYUI_INPUT, name)
    shutil.copy2(src_path, dst)
    print(f"  ↑ Copied to ComfyUI input: {name}")
    return name


def build_prompt(workflow, image_name, text_prompt, denoise, seed):
    """Modify workflow for our img2img needs."""
    prompt = {"prompt": {}}

    for node in workflow["nodes"]:
        nid = str(node["id"])
        ct = node["type"]
        wv = list(node.get("widgets_values", []))
        inp = {}

        # Build inputs from links
        for link_info in node.get("inputs", []):
            link_id = link_info.get("link")
            if link_id is not None:
                # Find source node/slot
                for l in workflow["links"]:
                    if l[0] == link_id:
                        inp[link_info["name"]] = [str(l[1]), l[2]]
                        break

        if ct == "LoadImage":
            # Both reference images = our base image
            wv[0] = image_name
            prompt["prompt"][nid] = {
                "class_type": ct,
                "inputs": {"image": image_name, "upload": "image"}
            }
            continue

        if ct == "CLIPTextEncode":
            prompt["prompt"][nid] = {
                "class_type": ct,
                "inputs": {"clip": inp.get("clip", inp.get("CLIP")), "text": text_prompt}
            }
            continue

        if ct == "RandomNoise":
            prompt["prompt"][nid] = {
                "class_type": ct,
                "inputs": {"noise_seed": seed}
            }
            continue

        if ct == "Flux2Scheduler":
            # More steps + adjusted dimensions for better quality
            steps = max(4, int(4 / denoise)) if denoise < 1.0 else 4
            prompt["prompt"][nid] = {
                "class_type": ct,
                "inputs": {"steps": steps, "width": 1024, "height": 1024}
            }
            continue

        if ct == "EmptyFlux2LatentImage":
            prompt["prompt"][nid] = {
                "class_type": ct,
                "inputs": {"width": 1024, "height": 1024, "batch_size": 1}
            }
            continue

        if ct == "ImageScaleToTotalPixels":
            prompt["prompt"][nid] = {
                "class_type": ct,
                "inputs": {"image": inp.get("image"), "upscale_method": "lanczos", "megapixels": 0.25, "resolution_steps": 64}
            }
            continue

        # Generic node — pass through widgets + inputs
        node_inputs = dict(inp)

        if ct == "UNETLoader":
            node_inputs["unet_name"] = wv[0] if wv else "flux-2-klein-4b.safetensors"
            node_inputs["weight_dtype"] = wv[1] if len(wv) > 1 else "default"
        elif ct == "CLIPLoader":
            node_inputs["clip_name"] = wv[0] if wv else "qwen_3_4b.safetensors"
            node_inputs["type"] = wv[1] if len(wv) > 1 else "flux2"
            if len(wv) > 2:
                node_inputs["device"] = wv[2]
        elif ct == "VAELoader":
            node_inputs["vae_name"] = wv[0] if wv else "flux2-vae.safetensors"
        elif ct == "CFGGuider":
            node_inputs["cfg"] = 1.0
        elif ct == "KSamplerSelect":
            node_inputs["sampler_name"] = "euler"
        elif ct == "SaveImage":
            node_inputs["filename_prefix"] = "spot_diff"

        prompt["prompt"][nid] = {
            "class_type": ct,
            "inputs": node_inputs
        }

    return prompt


def queue_prompt(prompt_data):
    """Send prompt to ComfyUI and wait for result."""
    data = json.dumps(prompt_data).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    prompt_id = result.get("prompt_id")
    print(f"  ⏳ Queued: {prompt_id}")
    return prompt_id


def wait_for_result(prompt_id, timeout=300):
    """Poll ComfyUI history until our prompt is done."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=5)
            history = json.loads(resp.read())
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for nid, out in outputs.items():
                    images = out.get("images", [])
                    if images:
                        return images[0]  # {"filename": ..., "subfolder": ..., "type": ...}
        except Exception:
            pass
        time.sleep(2)
    return None


def download_result(image_info, dst_path):
    """Download result image from ComfyUI."""
    fname = image_info["filename"]
    subfolder = image_info.get("subfolder", "")
    src = os.path.join(COMFYUI_OUTPUT, subfolder, fname)
    if os.path.exists(src):
        img = Image.open(src).convert("RGB")
        # Resize to match base image dimensions
        base_path = dst_path.replace("diff.png", "base.png")
        if os.path.exists(base_path):
            base = Image.open(base_path)
            img = img.resize(base.size, Image.LANCZOS)
        img.save(dst_path, "PNG")
        print(f"  ✓ Saved: {dst_path} ({img.size[0]}x{img.size[1]})")
        return True
    else:
        print(f"  ⚠ Output file not found: {src}")
        return False


def generate_diff(level_id, denoise=0.3):
    prompt_text = DIFFS.get(level_id)
    if not prompt_text:
        print(f"  ⚠ No prompt for {level_id}")
        return False

    base_path = os.path.join(IMG_DIR, level_id, "base.png")
    diff_path = os.path.join(IMG_DIR, level_id, "diff.png")

    if not os.path.exists(base_path):
        print(f"  ⚠ Missing base: {base_path}")
        return False

    # Upload base image to ComfyUI
    img_name = f"spot_diff_{level_id}_base.png"
    upload_image(base_path, img_name)

    # Load workflow
    with open(WORKFLOW_PATH) as f:
        workflow = json.load(f)

    # Build API prompt
    import random
    seed = random.randint(0, 2**32)
    prompt_data = build_prompt(workflow, img_name, prompt_text, denoise, seed)

    # Queue and wait
    prompt_id = queue_prompt(prompt_data)
    print(f"  ⏳ Generating (denoise={denoise})...")
    result = wait_for_result(prompt_id, timeout=300)

    if result:
        return download_result(result, diff_path)
    else:
        print(f"  ⚠ Timeout waiting for result")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Only generate this level")
    parser.add_argument("--denoise", type=float, default=0.3, help="Denoise strength (0.1=minimal change, 0.5=moderate)")
    args = parser.parse_args()

    if not check_comfyui():
        print("❌ ComfyUI is not running! Please start it first.")
        print("   Then run this script again.")
        sys.exit(1)

    print("✓ ComfyUI is running")

    levels = [args.only] if args.only else list(DIFFS.keys())

    for lvl in levels:
        print(f"\n{'='*50}")
        print(f"Generating diff: {lvl}")
        print(f"{'='*50}")
        ok = generate_diff(lvl, args.denoise)
        if not ok:
            print(f"  ❌ Failed for {lvl}")

    print("\nDone!")


if __name__ == "__main__":
    main()
