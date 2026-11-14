"""Quality control video: format, durasi, ukuran, frame tidak hitam, dan konfirmasi wajib."""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import probe  # noqa: E402


def frame_brightness(path, t):
    r = subprocess.run(["ffmpeg", "-v", "info", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                        "-vf", "signalstats,metadata=print", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", r.stderr)
    return float(m.group(1)) if m else None


def qc_video(path, meta, settings):
    """Kembalikan (lulus, daftar cek). meta: name, price, n_scenes, konfirmasi, caption, has_clip."""
    info = probe(path)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    checks = []

    def add(ok, label):
        checks.append({"ok": bool(ok), "label": label})

    add(info["width"] == 1080 and info["height"] == 1920,
        f"Format vertikal 9:16 ({info['width']} x {info['height']})")
    dmin, dmax = settings["durasi_min"], settings["durasi_maks"]
    add(dmin <= info["duration"] <= dmax, f"Durasi {info['duration']:.1f} detik (batas {dmin} sampai {dmax})")
    add(size > 50000, f"Ukuran file wajar ({size / 1048576:.1f} MB)")
    ok_frames = True
    if info["duration"] > 1:
        for frac in (0.25, 0.6):
            y = frame_brightness(path, info["duration"] * frac)
            if y is not None and y < 12:
                ok_frames = False
    add(ok_frames, "Frame tidak hitam atau kosong")
    add(meta["n_scenes"] >= settings["foto_min"], f"Minimal {settings['foto_min']} adegan ({meta['n_scenes']} adegan)")
    add(bool(meta["name"]) and bool(meta["price"]), "Nama dan harga produk terisi")
    add(meta["konfirmasi_asli"] and meta["konfirmasi_ai"], "Produk asli dan label AI sudah dikonfirmasi")
    if meta["has_clip"]:
        add(meta["konfirmasi_klip"], "Klip AI dikonfirmasi sama dengan produk asli")
    add(len(meta["caption"]) > 20, "Caption dan hashtag siap")
    return all(c["ok"] for c in checks), checks
