#!/usr/bin/env python3
"""
Clean single-image generator via online API.
No caching, no reuse, fresh every time.

Usage:
  ~/miniconda3/bin/python3 gen_single.py --prompt "..." --output path/to/output.png
  ~/miniconda3/bin/python3 gen_single.py --prompt "..." --ref path/to/ref.png --output path/to/output.png
"""
import argparse
import datetime
import hashlib
import hmac
import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from PIL import Image

API_URL = "http://aiservice.wdabuliu.com:8019/genl_image"
API_TIMEOUT = 360
USER_ID = 123456

R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET = "aigram"

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

TARGET_W, TARGET_H = 780, 554


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_r2(local_path):
    """Upload to R2 with unique timestamped key."""
    with open(local_path, "rb") as f:
        data = f.read()

    ts = int(time.time() * 1000)
    name = os.path.basename(local_path)
    obj_key = f"refs/spot-diff/single_{ts}_{name}"
    host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = "auto"
    service = "s3"
    method = "PUT"
    content_type = "image/png"
    canon_uri = "/" + R2_BUCKET + "/" + urllib.parse.quote(obj_key, safe="/")
    canon_qs = ""
    canon_headers = (
        f"content-type:{content_type}\nhost:{host}\nx-amz-content-sha256:UNSIGNED-PAYLOAD\nx-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canon_req = f"{method}\n{canon_uri}\n{canon_qs}\n{canon_headers}\n{signed_headers}\nUNSIGNED-PAYLOAD"
    scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string2sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{scope}\n{hashlib.sha256(canon_req.encode()).hexdigest()}"
    k = _sign(_sign(_sign(_sign(("AWS4" + R2_SECRET_KEY).encode(), date_stamp), region), service), "aws4_request")
    sig = hmac.new(k, string2sign.encode(), hashlib.sha256).hexdigest()
    auth = f"AWS4-HMAC-SHA256 Credential={R2_ACCESS_KEY}/{scope}, SignedHeaders={signed_headers}, Signature={sig}"

    req = urllib.request.Request(
        f"https://{host}/{R2_BUCKET}/{urllib.parse.quote(obj_key, safe='/')}",
        data=data, method="PUT",
        headers={
            "Content-Type": content_type,
            "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
            "x-amz-date": amz_date,
            "Authorization": auth,
        },
    )
    urllib.request.urlopen(req, timeout=60, context=_SSL)
    url = f"https://images.aiwaves.tech/{obj_key}"
    print(f"  ↑ Uploaded → {url}")
    return url


def call_api(ref_url, prompt):
    payload = json.dumps({
        "query": "",
        "params": {"url": ref_url, "prompt": prompt, "user_id": USER_ID},
    }).encode()
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
    result = json.loads(resp.read())
    return result.get("image_url") or result.get("url") or result.get("result", {}).get("image_url", "")


def download(url, dst):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=60, context=_SSL)
            data = resp.read()
            with open(dst, "wb") as f:
                f.write(data)
            # Convert webp if needed
            if dst.endswith(".png"):
                img = Image.open(dst)
                if img.format == "WEBP":
                    img.save(dst, "PNG")
                    print("  ✓ Converted webp → png")
            return True
        except Exception as e:
            print(f"  ⚠ Download failed ({e}), retrying in 5s…")
            time.sleep(5)
    return False


def create_ref(w, h):
    """Create a simple gradient reference at target aspect ratio."""
    import numpy as np
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            arr[y, x] = [40 + x * 80 // w, 30 + y * 60 // h, 50]
    img = Image.fromarray(arr)
    tmp = "/tmp/spot_diff_ref.png"
    img.save(tmp, "PNG")
    return tmp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--ref", help="Reference image path (for img2img). If omitted, generates from scratch.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=TARGET_W)
    parser.add_argument("--height", type=int, default=TARGET_H)
    args = parser.parse_args()

    # Prepare reference
    if args.ref:
        ref_path = args.ref
        print(f"  Using ref: {ref_path}")
    else:
        ref_path = create_ref(args.width, args.height)
        print(f"  Created gradient ref: {args.width}x{args.height}")

    # Upload
    ref_url = upload_r2(ref_path)

    # Generate
    print(f"  Calling API...")
    result_url = call_api(ref_url, args.prompt)
    print(f"  ↓ Downloading result...")

    # Download
    tmp = args.output + ".tmp.png"
    if not download(result_url, tmp):
        print("  ❌ Download failed")
        sys.exit(1)

    # Resize to target
    img = Image.open(tmp).convert("RGB")
    img = img.resize((args.width, args.height), Image.LANCZOS)
    img.save(args.output, "PNG")
    os.remove(tmp)
    print(f"  ✓ Saved: {args.output} ({args.width}x{args.height})")


if __name__ == "__main__":
    main()
