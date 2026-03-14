#!/usr/bin/env python3
"""
Generate 6 base scene images for spot-diff game using online img2img API.

Usage:
  ~/miniconda3/bin/python3 generate_scenes.py          # generate all 6
  ~/miniconda3/bin/python3 generate_scenes.py --only 1  # generate level 1 only
  ~/miniconda3/bin/python3 generate_scenes.py --only 3  # generate level 3 only

After generating base images, manually create diff versions:
  - Copy base.png → diff.png
  - Edit diff.png to add 5 differences per level
  - Update coordinates in src/SpotDiff/levels/index.ts
"""

import argparse
import datetime
import hashlib
import hmac
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

API_URL = "http://aiservice.wdabuliu.com:8019/genl_image"
API_TIMEOUT = 360
RATE_LIMIT_S = 78
USER_ID = 123456

# Cloudflare R2
R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET = "aigram"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")
REF_DIR = os.path.join(SCRIPT_DIR, "ref")

# Target: 780×560 (2x retina for 390×280 display)
REF_W, REF_H = 780, 560

SCENES = [
    {
        "id": "algram",
        "prompt": (
            "anime illustration of a cozy music studio room interior, "
            "electric guitar leaning on wall, guitar amplifier with glowing knobs, "
            "vinyl record player with spinning black vinyl, sheet music on stand, "
            "guitar pedals on floor with LED lights, warm ambient lighting, "
            "posters on wall, wooden floor, cables and headphones, "
            "detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "jenny",
        "prompt": (
            "anime illustration of a programmer desk workspace interior, "
            "dual monitor setup with code on screens, mechanical keyboard with RGB lighting, "
            "coffee mug with steam, colorful sticky notes on monitor, "
            "small potted plant, desk lamp, stack of tech books, "
            "cat sleeping on desk corner, USB cables, figurines, "
            "cozy night atmosphere, detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "jmf",
        "prompt": (
            "anime illustration of a dark hacker room interior, "
            "multiple monitors showing green terminal text and code, "
            "server rack with blinking LED lights, dim blue and green ambient light, "
            "energy drink cans, tangled ethernet cables, keyboard and mouse, "
            "dark curtains, neon accent lights, cyberpunk atmosphere, "
            "detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "ghostpixel",
        "prompt": (
            "anime illustration of a spooky haunted mansion study room interior, "
            "old wooden desk with glowing crystal ball, floating books and papers, "
            "blue candles in silver candelabra, mysterious purple portal on wall, "
            "dusty bookshelves with ancient tomes, raven perching on skull, "
            "cobwebs in corners, cracked window with moonlight, ornate dark rug, "
            "ghostly mist floating near floor, old globe on stand, "
            "detailed anime background art style, gothic atmosphere, no people"
        ),
    },
    {
        "id": "isaya",
        "prompt": (
            "anime illustration of an artist bedroom studio interior, "
            "wooden easel with half-finished abstract painting, scattered art supplies, "
            "black cat sitting on windowsill watching sunset, headphones on desk, "
            "stacked sketchbooks, warm fairy lights on wall, cozy bed with plushies, "
            "paint palette with bright colors, jar of paintbrushes, warm sunset light, "
            "small potted plants on shelf, vinyl record player, coffee cup, "
            "detailed anime background art style, warm cozy atmosphere, no people"
        ),
    },
    {
        "id": "isabel",
        "prompt": (
            "anime illustration of an elegant floral vanity room interior, "
            "ornate gold mirror on wall, flower vases with roses and lilies, "
            "open jewelry box with necklaces and earrings, perfume bottles, "
            "makeup brushes and cosmetics on table, lace curtains, soft pink lighting, "
            "dried flower bouquets, ribbon and hairpins, vintage chair, "
            "small framed photos, candle holder, porcelain figurines, "
            "detailed anime background art style, romantic atmosphere, no people"
        ),
    },
]


def create_ref_image():
    """Create a simple reference image at target aspect ratio using PIL."""
    ref_path = os.path.join(REF_DIR, "ref_780x560.png")
    if os.path.exists(ref_path):
        print(f"  Reference image exists: {ref_path}")
        return ref_path

    os.makedirs(REF_DIR, exist_ok=True)
    try:
        from PIL import Image
        img = Image.new("RGB", (REF_W, REF_H), (80, 80, 120))
        img.save(ref_path)
        print(f"  Created reference image: {ref_path}")
    except ImportError:
        # Fallback: create a simple PPM and convert with sips
        ppm_path = ref_path.replace(".png", ".ppm")
        with open(ppm_path, "wb") as f:
            f.write(f"P6\n{REF_W} {REF_H}\n255\n".encode())
            f.write(bytes([80, 80, 120] * REF_W * REF_H))
        subprocess.run(["sips", "-s", "format", "png", ppm_path, "--out", ref_path],
                       check=True, capture_output=True)
        os.remove(ppm_path)
        print(f"  Created reference image: {ref_path}")
    return ref_path


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_to_r2(path):
    """Upload image to Cloudflare R2 → public CDN URL."""
    print(f"  ↑ Uploading {os.path.basename(path)} to R2…")
    with open(path, "rb") as f:
        data = f.read()

    obj_key = "refs/spot-diff/" + os.path.basename(path)
    host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = "auto"
    service = "s3"

    content_type = "image/png"
    content_hash = hashlib.sha256(data).hexdigest()
    canon_uri = "/" + R2_BUCKET + "/" + urllib.parse.quote(obj_key, safe="/")

    canon_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{content_hash}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"

    canon_req = "\n".join([
        "PUT", canon_uri, "",
        canon_headers, signed_headers, content_hash,
    ])

    cred_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    str_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, cred_scope,
        hashlib.sha256(canon_req.encode()).hexdigest(),
    ])

    k_date = _sign(("AWS4" + R2_SECRET_KEY).encode(), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, str_to_sign.encode(), hashlib.sha256).hexdigest()

    auth = (
        f"AWS4-HMAC-SHA256 Credential={R2_ACCESS_KEY}/{cred_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    url = f"https://{host}/{R2_BUCKET}/{urllib.parse.quote(obj_key, safe='/')}"
    req = urllib.request.Request(url, data=data, method="PUT", headers={
        "Content-Type": content_type,
        "Host": host,
        "x-amz-content-sha256": content_hash,
        "x-amz-date": amz_date,
        "Authorization": auth,
    })

    with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
        resp.read()

    public_url = f"https://images.aiwaves.tech/{obj_key}"
    print(f"  ✓ Uploaded → {public_url}")
    return public_url


def call_api(ref_url, prompt):
    payload = json.dumps({
        "query": "",
        "params": {
            "url": ref_url,
            "prompt": prompt,
            "user_id": USER_ID,
        },
    }).encode()

    req = urllib.request.Request(
        API_URL, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            result = json.loads(body)
        except Exception:
            sys.exit(f"ERROR: HTTP {e.code} — {body}")

    code = result.get("code")
    if code == 200:
        return result["url"]
    if code == 429:
        raise RuntimeError("rate_limit")
    print(f"  ✗ API returned code={code}")
    return None


def download_image(url, out_path):
    print(f"  ↓ Downloading result…")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    src_ext = os.path.splitext(url.split("?")[0])[1].lower()
    dst_ext = os.path.splitext(out_path)[1].lower()
    tmp_path = out_path if src_ext == dst_ext else out_path + src_ext

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:
        data = resp.read()
    with open(tmp_path, "wb") as f:
        f.write(data)

    if src_ext != dst_ext and dst_ext in (".png", ".jpg", ".jpeg"):
        fmt = "png" if dst_ext == ".png" else "jpeg"
        subprocess.run(["sips", "-s", "format", fmt, tmp_path, "--out", out_path],
                       check=True, capture_output=True)
        os.remove(tmp_path)
        print(f"  ✓ Converted {src_ext} → {dst_ext}")
    elif tmp_path != out_path:
        os.rename(tmp_path, out_path)

    size_kb = os.path.getsize(out_path) // 1024
    print(f"  ✓ Saved → {out_path}  ({size_kb} KB)")


def generate_scene(scene, ref_url):
    out_dir = os.path.join(IMG_DIR, scene["id"])
    out_path = os.path.join(out_dir, "base.png")

    if os.path.exists(out_path):
        print(f"\n  ⏭ Skipping {scene['id']} — base.png already exists")
        return True

    print(f"\n{'='*60}")
    print(f"Generating: {scene['id']} ({scene['prompt'][:60]}…)")
    print(f"{'='*60}")

    while True:
        try:
            result_url = call_api(ref_url, scene["prompt"])
        except RuntimeError as e:
            if str(e) == "rate_limit":
                print(f"  ⏳ Rate limited — waiting {RATE_LIMIT_S}s…")
                time.sleep(RATE_LIMIT_S)
                continue
            raise
        break

    if not result_url:
        print(f"  ✗ Failed to generate {scene['id']}")
        return False

    download_image(result_url, out_path)
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate spot-diff scene images")
    parser.add_argument("--only", type=int, help="Generate only level N (1-6)")
    args = parser.parse_args()

    scenes = SCENES
    if args.only:
        idx = args.only - 1
        if idx < 0 or idx >= len(SCENES):
            sys.exit(f"ERROR: --only must be 1-{len(SCENES)}")
        scenes = [SCENES[idx]]

    print("Creating reference image…")
    ref_path = create_ref_image()
    ref_url = upload_to_r2(ref_path)

    success = 0
    for i, scene in enumerate(scenes):
        ok = generate_scene(scene, ref_url)
        if ok:
            success += 1
        if i < len(scenes) - 1:
            print(f"\n  ⏳ Waiting {RATE_LIMIT_S}s for rate limit…")
            time.sleep(RATE_LIMIT_S)

    print(f"\n{'='*60}")
    print(f"Done: {success}/{len(scenes)} scenes generated")
    print(f"Next steps:")
    print(f"  1. Review generated images in {IMG_DIR}/*/base.png")
    print(f"  2. Copy each base.png → diff.png")
    print(f"  3. Edit diff.png to create 5 differences per level")
    print(f"  4. Update coordinates in src/SpotDiff/levels/index.ts")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
