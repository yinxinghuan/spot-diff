#!/usr/bin/env python3
"""
Generate vintage detective noir style portrait cards for each character
using the online img2img API with character avatars as reference images.

Usage:
  ~/miniconda3/bin/python3 generate_cards.py          # all 7
  ~/miniconda3/bin/python3 generate_cards.py --only 1  # card 1 only
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

R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET = "aigram"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHARS_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "chars")
CARDS_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "cards")
POSTER_PATH = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "poster_new.png")

TARGET_SIZE = (512, 512)

CARDS = [
    {
        "id": "algram",
        "ref": os.path.join(CHARS_DIR, "algram.png"),
        "out": os.path.join(CARDS_DIR, "algram.png"),
        "prompt": (
            "vintage sepia detective noir portrait, young man with spiky hair "
            "holding guitar, side profile, moody lighting, old paper texture, "
            "muted brown tones, magnifying glass motif, retro illustration style"
        ),
    },
    {
        "id": "jenny",
        "ref": os.path.join(CHARS_DIR, "jenny.png"),
        "out": os.path.join(CARDS_DIR, "jenny.png"),
        "prompt": (
            "vintage sepia detective noir portrait, young woman with glasses "
            "and brown hair wearing hoodie, side profile, moody lighting, "
            "old paper texture, muted brown tones, magnifying glass motif, "
            "retro illustration style"
        ),
    },
    {
        "id": "jmf",
        "ref": os.path.join(CHARS_DIR, "jmf.png"),
        "out": os.path.join(CARDS_DIR, "jmf.png"),
        "prompt": (
            "vintage sepia detective noir portrait, mature man with glasses "
            "and black hair wearing dark jacket, side profile, moody lighting, "
            "old paper texture, muted brown tones, magnifying glass motif, "
            "retro illustration style"
        ),
    },
    {
        "id": "ghostpixel",
        "ref": os.path.join(CHARS_DIR, "ghostpixel.png"),
        "out": os.path.join(CARDS_DIR, "ghostpixel.png"),
        "prompt": (
            "vintage sepia detective noir portrait, mysterious ghost figure "
            "with white sheet, side profile, moody lighting, old paper texture, "
            "muted brown tones, magnifying glass motif, retro illustration style"
        ),
    },
    {
        "id": "isaya",
        "ref": os.path.join(CHARS_DIR, "isaya.png"),
        "out": os.path.join(CARDS_DIR, "isaya.png"),
        "prompt": (
            "vintage sepia detective noir portrait, young woman with long blue "
            "hair wearing headphones and dark hoodie, side profile, moody "
            "lighting, old paper texture, muted brown tones, magnifying glass "
            "motif, retro illustration style"
        ),
    },
    {
        "id": "isabel",
        "ref": os.path.join(CHARS_DIR, "isabel.png"),
        "out": os.path.join(CARDS_DIR, "isabel.png"),
        "prompt": (
            "vintage sepia detective noir portrait, elegant woman with silver "
            "hair, side profile, moody lighting, old paper texture, muted "
            "brown tones, magnifying glass motif, retro illustration style"
        ),
    },
    {
        "id": "poster",
        "ref": os.path.join(CHARS_DIR, "algram.png"),
        "out": POSTER_PATH,
        "prompt": (
            "vintage detective novel cover illustration, large magnifying glass "
            "in center revealing hidden clues, six character silhouettes around "
            "the edges, sepia brown tones, old paper texture, text SPOT THE "
            "DIFFERENCE at top, retro mystery book cover style"
        ),
    },
]


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_to_r2(path):
    """Upload image to Cloudflare R2 -> public CDN URL."""
    print(f"  ↑ Uploading {os.path.basename(path)} to R2…")
    with open(path, "rb") as f:
        data = f.read()

    obj_key = "refs/spot-diff/cards_" + os.path.basename(path)
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


def resize_to_square(path, size=TARGET_SIZE):
    """Resize image to exact square dimensions."""
    from PIL import Image
    img = Image.open(path)
    if img.size != size:
        print(f"  ✂ Resizing {img.size} → {size}")
        img = img.resize(size, Image.LANCZOS)
        img.save(path, "PNG", optimize=True)


def prepare_square_ref(ref_path):
    """Create a temporary square version of the ref image for upload."""
    from PIL import Image
    img = Image.open(ref_path)
    if img.size == TARGET_SIZE:
        return ref_path  # already square and correct size

    # Create temp square version
    tmp_path = ref_path + ".square_tmp.png"
    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    img.save(tmp_path, "PNG", optimize=True)
    print(f"  ✂ Prepared square ref {img.size} → {TARGET_SIZE}")
    return tmp_path


def generate_card(card):
    ref_path = card["ref"]
    out_path = card["out"]

    if not os.path.exists(ref_path):
        print(f"\n  ⏭ Skipping {card['id']} — no ref image at {ref_path}")
        return False

    print(f"\n{'='*60}")
    print(f"Generating card for: {card['id']}")
    print(f"  Ref: {ref_path}")
    print(f"  Out: {out_path}")
    print(f"{'='*60}")

    # Resize ref to square before uploading (API output matches input aspect ratio)
    square_ref = prepare_square_ref(ref_path)
    try:
        ref_url = upload_to_r2(square_ref)
    finally:
        # Clean up temp file if we created one
        if square_ref != ref_path and os.path.exists(square_ref):
            os.remove(square_ref)

    # Call API with ref
    while True:
        try:
            result_url = call_api(ref_url, card["prompt"])
        except RuntimeError as e:
            if str(e) == "rate_limit":
                print(f"  ⏳ Rate limited — waiting {RATE_LIMIT_S}s…")
                time.sleep(RATE_LIMIT_S)
                continue
            raise
        break

    if not result_url:
        print(f"  ✗ Failed to generate card for {card['id']}")
        return False

    download_image(result_url, out_path)

    # Resize output to 512x512
    try:
        resize_to_square(out_path)
    except ImportError:
        print("  ⚠ PIL not available, skipping resize")

    return True


def main():
    parser = argparse.ArgumentParser(description="Generate detective noir portrait cards via img2img API")
    parser.add_argument("--only", type=int, help="Generate only card N (1-7)")
    args = parser.parse_args()

    cards = CARDS
    if args.only:
        idx = args.only - 1
        if idx < 0 or idx >= len(CARDS):
            sys.exit(f"ERROR: --only must be 1-{len(CARDS)}")
        cards = [CARDS[idx]]

    # Ensure output directories exist
    os.makedirs(CARDS_DIR, exist_ok=True)

    success = 0
    for i, card in enumerate(cards):
        ok = generate_card(card)
        if ok:
            success += 1
        if i < len(cards) - 1:
            print(f"\n  ⏳ Waiting {RATE_LIMIT_S}s for rate limit…")
            time.sleep(RATE_LIMIT_S)

    print(f"\n{'='*60}")
    print(f"Done: {success}/{len(cards)} card images generated")
    print(f"  Cards saved to: {CARDS_DIR}")
    if any(c["id"] == "poster" for c in cards):
        print(f"  Poster saved to: {POSTER_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
