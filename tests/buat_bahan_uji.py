"""Buat bahan sintetis untuk uji alur (bukan foto produk): 3 foto, 1 klip, dan meta.json.

Pemakaian: python3 tests/buat_bahan_uji.py DIR
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

d = sys.argv[1]
os.makedirs(d, exist_ok=True)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
except OSError:
    font = ImageFont.load_default()

media = []
for i, (c, sz) in enumerate([((190, 140, 60), (900, 1200)), ((60, 130, 190), (1200, 900)),
                             ((100, 170, 90), (1000, 1000))]):
    im = Image.new("RGB", sz, c)
    dr = ImageDraw.Draw(im)
    for k in range(0, sz[0], 80):
        dr.line([(k, 0), (k, sz[1])], fill=(255, 255, 255), width=2)
    dr.text((60, sz[1] // 2 - 45), f"UJI {i + 1}", font=font, fill=(255, 255, 255))
    p = os.path.join(d, f"f{i}.jpg")
    im.save(p)
    media.append({"path": os.path.abspath(p), "kind": "photo"})

clip = os.path.join(d, "klip.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                "testsrc2=duration=4:size=720x1280:rate=30", "-c:v", "libx264", "-pix_fmt", "yuv420p", clip],
               check=True)
media.append({"path": os.path.abspath(clip), "kind": "clip"})

meta = {"kalimat": "Produk Uji Sintetis 75ml Paket Hemat 2 Botol Rp10.000 https://s.shopee.co.id/uji",
        "folder": "", "varian": 3, "konfirmasi": [True, True, True], "media": media}
with open(os.path.join(d, "meta.json"), "w", encoding="utf8") as f:
    json.dump(meta, f, indent=2)
print("bahan uji siap:", len(media), "adegan")
