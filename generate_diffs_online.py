#!/usr/bin/env python3
"""
Generate diff images by using base images as reference via online img2img API.
The API will produce a similar but subtly different version of each scene.

Usage:
  ~/miniconda3/bin/python3 generate_diffs_online.py          # all 6
  ~/miniconda3/bin/python3 generate_diffs_online.py --only 1  # level 1 only

After generation, use find_diffs.py to detect actual difference regions
and update coordinates in levels/index.ts.
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

R2_ACCOUNT_ID = os.environ["ALTERU_R2_ACCOUNT_ID"]
R2_ACCESS_KEY = os.environ["ALTERU_R2_ACCESS_KEY_ID"]
R2_SECRET_KEY = os.environ["ALTERU_R2_SECRET_ACCESS_KEY"]
R2_BUCKET = "aigram"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")

# Each scene: use same theme prompt but ask for small variations
SCENES = [
    {
        "id": "algram",
        "prompt": (
            "anime illustration of a cozy music studio room interior, "
            "BLUE electric guitar leaning on wall instead of sunburst guitar, "
            "vinyl turntable with ORANGE vinyl record instead of black record, "
            "RED headphones on floor instead of black headphones, "
            "guitar amplifier, guitar pedals, warm lighting, wooden floor, cables, "
            "posters on wall, detailed anime background art style, no people"
        ),
    },
    {
        "id": "jenny",
        "prompt": (
            "anime illustration of a programmer desk workspace interior, "
            "WHITE cat sleeping on desk corner instead of no cat, "
            "small CACTUS plant on desk instead of leafy potted plant, "
            "BRIGHT RED desk lamp instead of yellow desk lamp, "
            "dual monitors, keyboard, sticky notes, books, "
            "cozy night atmosphere, detailed anime background art style, no people"
        ),
    },
    {
        "id": "jmf",
        "prompt": (
            "anime illustration of a dark hacker room interior, "
            "BRIGHT PINK neon sign on ceiling instead of blue neon sign, "
            "extra PIZZA BOX on desk that was not there before, "
            "RED tangled cables on floor instead of blue cables, "
            "multiple monitors, server rack, dim ambient light, cyberpunk, "
            "detailed anime background art style, no people"
        ),
    },
    {
        "id": "ghostpixel",
        "prompt": (
            "anime illustration of a spooky haunted mansion study room interior, "
            "old wooden desk with glowing RED crystal ball instead of blue crystal ball, "
            "GREEN candles in silver candelabra instead of blue candles, "
            "mysterious RED and ORANGE portal on wall instead of purple portal, "
            "dusty bookshelves with ancient tomes, WHITE OWL perching on skull instead of raven, "
            "cobwebs in corners, cracked window with moonlight, ornate dark rug, "
            "ghostly mist floating near floor, old globe on stand, "
            "detailed anime background art style, gothic atmosphere, no people"
        ),
    },
    {
        "id": "isaya",
        "prompt": (
            "anime illustration of an artist bedroom studio interior, "
            "wooden easel with half-finished LANDSCAPE MOUNTAIN painting instead of abstract, "
            "ORANGE tabby cat sitting on windowsill instead of black cat, scattered art supplies, "
            "stacked sketchbooks, PINK fairy lights on wall instead of warm yellow, "
            "RED headphones on desk instead of no headphones, cozy bed with plushies, "
            "paint palette with bright colors, jar of paintbrushes, warm sunset light, "
            "SUNFLOWER in pot on shelf instead of small plant, vinyl record player, coffee cup, "
            "detailed anime background art style, warm cozy atmosphere, no people"
        ),
    },
    {
        "id": "isabel",
        "prompt": (
            "anime illustration of an elegant floral vanity room interior, "
            "ornate SILVER mirror on wall instead of gold mirror, "
            "flower vases with YELLOW SUNFLOWERS instead of roses and lilies, "
            "open jewelry box with PEARL NECKLACE draped on mirror, BLUE perfume bottles, "
            "makeup brushes and cosmetics on table, GREEN lace curtains instead of white, "
            "dried LAVENDER bouquets instead of flower bouquets, soft PURPLE lighting, "
            "ribbon and hairpins, vintage chair, small framed photos, candle holder, "
            "detailed anime background art style, romantic atmosphere, no people"
        ),
    },
]


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_to_r2(path):
    """Upload image to Cloudflare R2 → public CDN URL."""
    print(f"  ↑ Uploading {os.path.basename(path)} to R2…")
    with open(path, "rb") as f:
        data = f.read()

    # Add timestamp to key to bust CDN cache
    ts = int(time.time())
    obj_key = f"refs/spot-diff/{os.path.basename(os.path.dirname(path))}_{ts}_{os.path.basename(path)}"
    host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    now = datetime.datetime.now(datetime.UTC)
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

    # Retry up to 3 times with delay
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
                data = resp.read()
            break
        except urllib.error.HTTPError as e:
            if attempt < 2:
                print(f"  ⚠ Download failed ({e.code}), retrying in 5s…")
                time.sleep(5)
            else:
                raise

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


def resize_to_match(diff_path, base_path):
    """Resize diff image to match base image dimensions exactly."""
    from PIL import Image
    base = Image.open(base_path)
    diff = Image.open(diff_path)
    if diff.size != base.size:
        print(f"  ✂ Resizing diff {diff.size} → {base.size}")
        diff = diff.resize(base.size, Image.LANCZOS)
        diff.save(diff_path, "PNG", optimize=True)


def generate_diff(scene):
    base_path = os.path.join(IMG_DIR, scene["id"], "base.png")
    diff_path = os.path.join(IMG_DIR, scene["id"], "diff.png")

    if not os.path.exists(base_path):
        print(f"\n  ⏭ Skipping {scene['id']} — no base.png")
        return False

    print(f"\n{'='*60}")
    print(f"Generating diff for: {scene['id']}")
    print(f"  Using base.png as reference image")
    print(f"{'='*60}")

    # Upload base image as reference
    ref_url = upload_to_r2(base_path)

    # Call API with base as ref
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
        print(f"  ✗ Failed to generate diff for {scene['id']}")
        return False

    download_image(result_url, diff_path)

    # Ensure same dimensions as base
    try:
        resize_to_match(diff_path, base_path)
    except ImportError:
        print("  ⚠ PIL not available, skipping resize check")

    return True


def main():
    parser = argparse.ArgumentParser(description="Generate diff images via img2img API")
    parser.add_argument("--only", type=int, help="Generate only level N (1-6)")
    args = parser.parse_args()

    scenes = SCENES
    if args.only:
        idx = args.only - 1
        if idx < 0 or idx >= len(SCENES):
            sys.exit(f"ERROR: --only must be 1-{len(SCENES)}")
        scenes = [SCENES[idx]]

    success = 0
    for i, scene in enumerate(scenes):
        ok = generate_diff(scene)
        if ok:
            success += 1
        if i < len(scenes) - 1:
            print(f"\n  ⏳ Waiting {RATE_LIMIT_S}s for rate limit…")
            time.sleep(RATE_LIMIT_S)

    print(f"\n{'='*60}")
    print(f"Done: {success}/{len(scenes)} diff images generated")
    print(f"\nNext: run find_diffs.py to detect difference regions")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
