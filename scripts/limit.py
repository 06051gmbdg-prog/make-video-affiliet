"""Batas video per hari (zona waktu WIB). Pemakaian: limit.py remaining | add N"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, load_settings, wib_today  # noqa: E402

PATH = os.path.join(ROOT, "data", "hari.json")


def _load():
    try:
        with open(PATH, encoding="utf8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    if d.get("tanggal") != wib_today():
        d = {"tanggal": wib_today(), "jumlah": 0}
    return d


def remaining():
    return max(0, int(load_settings()["video_per_hari"]) - int(_load()["jumlah"]))


def add(n):
    d = _load()
    d["jumlah"] = int(d["jumlah"]) + int(n)
    with open(PATH, "w", encoding="utf8") as f:
        json.dump(d, f, indent=2)
        f.write("\n")
    return d["jumlah"]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "remaining"
    if cmd == "remaining":
        print(remaining())
    elif cmd == "add":
        print(add(int(sys.argv[2])))
    else:
        sys.exit("perintah: remaining | add N")
