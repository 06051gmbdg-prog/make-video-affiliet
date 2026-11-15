"""Ambil klip suasana (B-roll) dari Pixabay. Hanya suasana, bukan produk.

Perlu Secret PIXABAY_API_KEY (gratis di pixabay.com/api/docs). Tanpa kunci, langkah ini dilewati.
Lisensi Pixabay membolehkan pemakaian komersial tanpa atribusi. Klip diunduh ke folder kerja, bukan ditautkan.
"""
import json
import os
import re
import urllib.parse
import urllib.request

API = "https://pixabay.com/api/videos/"
MAKS_BYTE = 20 * 1024 * 1024
UA = {"User-Agent": "make-video-affiliet"}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (host tetap pixabay)
        return r.read()


def bersihkan(q):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s-]", " ", q or "")).strip()[:100]


def pilih(hits, n):
    """Pilih n klip: durasi >= 3 detik, ukuran wajar, ukuran 'medium' bila ada."""
    out = []
    for h in hits or []:
        if (h.get("duration") or 0) < 3:
            continue
        v = h.get("videos") or {}
        for key in ("medium", "small", "large", "tiny"):
            c = v.get(key) or {}
            if c.get("url") and 0 < (c.get("size") or 1) <= MAKS_BYTE:
                out.append({"id": h.get("id"), "url": c["url"]})
                break
        if len(out) >= n:
            break
    return out


def ambil_broll(query, dest, n=2, key=None):
    """Kembalikan daftar item {'path','kind':'clip'}. Gagal apa pun -> daftar kosong (video tetap dibuat)."""
    key = key or os.environ.get("PIXABAY_API_KEY", "")
    q = bersihkan(query)
    if not (key and q and n > 0):
        return []
    try:
        url = API + "?" + urllib.parse.urlencode({"key": key, "q": q, "per_page": 20, "safesearch": "true"})
        hits = json.loads(_get(url)).get("hits", [])
        os.makedirs(dest, exist_ok=True)
        items = []
        for c in pilih(hits, n):
            host = urllib.parse.urlparse(c["url"]).hostname or ""
            if not host.endswith("pixabay.com"):
                continue
            path = os.path.join(dest, f"pixabay-{c['id']}.mp4")
            with open(path, "wb") as f:
                f.write(_get(c["url"], timeout=90))
            items.append({"path": os.path.abspath(path), "kind": "clip"})
        return items
    except Exception as e:  # noqa: BLE001
        print("Pixabay dilewati:", str(e).replace(key, "***")[:200])
        return []
