"""Fungsi bersama: pengaturan, parser kalimat produk, penurunan hook, varian."""
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STYLE_ORDER = ["cinema", "promo", "elegan"]
STYLES = {
    "cinema": {"label": "Sinematik", "zoom": 0.15, "trans": "fadeblack", "tdur": 0.7,
               "bars": True, "cap_size": 58, "cap_color": "white", "cap_box": "black@0.55"},
    "promo": {"label": "Promo cepat", "zoom": 0.10, "trans": "slideleft", "tdur": 0.3,
              "bars": False, "cap_size": 66, "cap_color": "0xffe600", "cap_box": "black@0.45"},
    "elegan": {"label": "Elegan", "zoom": 0.08, "trans": "fade", "tdur": 0.9,
               "bars": False, "cap_size": 54, "cap_color": "0xfff8e8", "cap_box": "0x140e06@0.6"},
}

PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp")
CLIP_EXT = (".mp4", ".mov", ".webm", ".m4v")
MUSIC_EXT = (".mp3", ".m4a", ".wav", ".ogg", ".aac")


def load_settings():
    with open(os.path.join(ROOT, "config", "settings.json"), encoding="utf8") as f:
        return json.load(f)


def wib_today():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")


def fmt_rp(n):
    return "Rp " + f"{int(round(n)):,}".replace(",", ".")


URL_RE = re.compile(r"https?://\S+", re.I)


def parse_sentence(s):
    """Ambil nama, link, dan harga dari satu kalimat."""
    s = s or ""
    m = URL_RE.search(s)
    url = m.group(0).rstrip(".,;)") if m else ""
    rest = URL_RE.sub(" ", s)
    price = ""
    pm = re.search(r"(?:rp\.?|harga\s*[:=]?)\s*(\d[\d.,]*)", rest, re.I)
    if pm:
        dg = re.sub(r",\d{1,2}$", "", pm.group(1))
        dg = re.sub(r"[.,]", "", dg)
        if dg:
            price = fmt_rp(int(dg))
        rest = rest.replace(pm.group(0), " ")
    # Teks tombol Bagikan Shopee: "Cek <nama> dengan harga Rp... Dapatkan di Shopee sekarang!"
    rest = re.sub(r"\bdengan\s+harga\b", " ", rest, flags=re.I)
    rest = re.sub(r"\bdapatkan\s+di\s+shopee.*$", " ", rest, flags=re.I | re.S)
    rest = re.sub(r"^\s*(?:cek|lihat|intip)\s+", "", rest, flags=re.I)
    name = re.sub(r"\b(link|tautan|judul|nama\s+produk|nama|affiliate|afiliasi)\b\s*[:=-]?", " ",
                  rest, flags=re.I)
    name = re.sub(r"[|;]+", " ", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"^[\s:,.-]+|[\s:,.-]+$", "", name)
    if not name and url:
        seg = unquote(urlparse(url).path.rstrip("/").split("/")[-1])
        if re.search(r"-i\.\d+\.\d+", seg):
            name = re.sub(r"[-_]+", " ", re.sub(r"-i\.\d+\.\d+.*$", "", seg)).strip()
    return {"name": name, "url": url, "price": price}


def short_name(name):
    w = name.split(" ")
    return " ".join(w[:6]) if len(name) > 48 else name


def derive(name):
    """Hook, kelebihan, dan hashtag hanya dari kata di nama produk (tanpa klaim tambahan)."""
    b = []
    lw = name.lower()
    pk = re.search(r"\b(?:paket|bundling|bundle|isi|set)\b[^\d]{0,12}(\d+)\s*"
                   r"(botol|pcs|pack|buah|pasang|set|box|lembar|pc)?", name, re.I)
    unit = (pk.group(2) or "").lower() if pk else ""
    if pk:
        b.append("Isi " + pk.group(1) + (" " + unit if unit else "")
                 + (", lebih hemat" if re.search(r"hemat|bundl|paket", lw) else ""))
    sz = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|gr|gram|kg|liter|cm|mm|watt|mah|gb)\b", name, re.I)
    if sz:
        b.append("Ukuran " + sz.group(1) + " " + sz.group(2).lower() + (" per " + unit if unit else ""))
    first = re.sub(r"[^a-z0-9]", "", (name.split(" ")[0] if name else "").lower())
    tags = "#shopee #rekomendasi #racunshopee" + (" #" + first if len(first) >= 3 else "")
    return {"hook": "Cek " + short_name(name) + "!", "benefits": b, "tags": tags}


def make_variants(name, hook, benefits, per, n_media, count):
    """Tiga varian: gaya, kalimat pembuka, tombol akhir, durasi foto, dan urutan adegan berbeda."""
    sn = short_name(name)
    hooks = [hook or ("Cek " + sn + "!"),
             (benefits[0] + "!") if benefits else "Ini dia " + sn + "!",
             "Intip " + sn + " dari dekat"]
    ctas = ["CEK KERANJANG KUNING", "KLIK KERANJANG KUNING", "LIHAT DI KERANJANG"]
    pers = [per, max(2.5, round(per * 0.8 * 2) / 2), min(6.0, round(per * 1.2 * 2) / 2)]
    out = []
    for v in range(min(3, max(1, count))):
        out.append({
            "label": "Varian " + "ABC"[v],
            "style": STYLE_ORDER[v % 3],
            "hook": hooks[v],
            "cta": ctas[v],
            "per": pers[v],
            "rotate": (v % n_media) if n_media else 0,
        })
    return out


def slugify(text, maxlen=40):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:maxlen].strip("-")
    return s or "video"


def build_caption(name, hook, benefits, tags, url, ada_klip):
    lines = [name + (" | " + hook if hook else ""), ""]
    lines += ["- " + b for b in benefits]
    lines += ["", "Cek keranjang kuning di video ini ya!"]
    if tags:
        lines += ["", tags]
    if url:
        lines += ["", "Link affiliate: " + url]
    lines += ["", "INGAT sebelum Posting di Shopee:",
              "1. Aktifkan LABEL AI di aplikasi Shopee.",
              "2. Pastikan produk di video sama dengan produk asli."]
    if ada_klip:
        lines.append("3. Klip AI sudah ditonton dan bentuk, logo, label produk tidak berubah.")
    return "\n".join(lines) + "\n"


def probe(path):
    """Kembalikan dict width, height, duration (detik, 0 bila tidak ada)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height:format=duration",
                        "-of", "json", path], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    s = (d.get("streams") or [{}])[0]
    dur = (d.get("format") or {}).get("duration")
    try:
        dur = float(dur)
    except (TypeError, ValueError):
        dur = 0.0
    return {"width": int(s.get("width") or 0), "height": int(s.get("height") or 0), "duration": dur}
