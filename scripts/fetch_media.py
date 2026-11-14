"""Ambil kalimat, pilihan, dan lampiran foto/klip dari sebuah Issue (dibuat lewat form).

Pemakaian: fetch_media.py --issue 12 --repo pemilik/repo --out work/issue --meta work/issue.json
Perlu `gh` dengan GH_TOKEN. Lampiran diambil dari body_html supaya repo privat juga bisa.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser

MAX_BYTES = 80 * 1024 * 1024


class MediaParser(HTMLParser):
    """Kumpulkan <img> dan <video> berurutan, sesuai urutan di Issue."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img":
            cls = a.get("class") or ""
            src = a.get("src") or ""
            if "emoji" in cls or "githubassets.com/images/icons" in src or not src:
                return
            self.items.append({"url": src, "hint": "photo"})
        elif tag == "video":
            src = a.get("src") or ""
            if src:
                self.items.append({"url": src, "hint": "clip"})
        elif tag == "source":
            src = a.get("src") or ""
            if src and self.items and self.items[-1]["hint"] == "clip" and self.items[-1].get("pending"):
                self.items[-1]["url"] = src


def parse_media(html):
    p = MediaParser()
    p.feed(html or "")
    return p.items


def parse_form(body):
    secs, cur = {}, None
    for line in (body or "").splitlines():
        if line.startswith("### "):
            cur = line[4:].strip()
            secs[cur] = []
        elif cur is not None:
            secs[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in secs.items()}


def field(secs, prefix):
    for k, v in secs.items():
        if k.lower().startswith(prefix.lower()):
            return "" if v.strip() == "_No response_" else v.strip()
    return ""


def sniff(data):
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg", "photo"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png", "photo"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp", "photo"
    if data[4:8] == b"ftyp":
        return (".mov" if data[8:12] == b"qt  " else ".mp4"), "clip"
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return ".webm", "clip"
    return None, None


def download(url, dest_base):
    req = urllib.request.Request(url, headers={"User-Agent": "make-video-affiliet"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise RuntimeError("file terlalu besar")
    ext, kind = sniff(data)
    if not ext:
        raise RuntimeError("format tidak dikenali (pakai JPG, PNG, WEBP, MP4, MOV, atau WEBM)")
    path = dest_base + ext
    with open(path, "wb") as f:
        f.write(data)
    return path, kind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", required=True, type=int)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--meta", required=True)
    a = ap.parse_args()

    r = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.full+json",
                        f"repos/{a.repo}/issues/{a.issue}"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("Gagal membaca Issue: " + r.stderr[-400:])
    issue = json.loads(r.stdout)
    secs = parse_form(issue.get("body") or "")
    kal = re.sub(r"\s+", " ", field(secs, "Kalimat produk"))
    folder = field(secs, "Folder bahan").strip()
    varian = field(secs, "Jumlah varian")
    konf = [bool(re.match(r"-\s*\[[xX]\]", ln.strip())) for ln in field(secs, "Konfirmasi").splitlines()
            if ln.strip().startswith("- [")]

    os.makedirs(a.out, exist_ok=True)
    media, gagal = [], []
    for i, it in enumerate(parse_media(issue.get("body_html") or "")):
        try:
            path, kind = download(it["url"], os.path.join(a.out, f"{i:02d}"))
            media.append({"path": os.path.abspath(path), "kind": kind})
        except Exception as e:  # noqa: BLE001
            gagal.append(f"lampiran {i + 1}: {e}")
    meta = {"kalimat": kal, "folder": folder, "varian": int(varian) if varian.isdigit() else 0,
            "konfirmasi": konf, "media": media, "gagal_unduh": gagal}
    os.makedirs(os.path.dirname(os.path.abspath(a.meta)), exist_ok=True)
    with open(a.meta, "w", encoding="utf8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Kalimat: {kal!r}; lampiran: {len(media)}; gagal: {len(gagal)}")


if __name__ == "__main__":
    main()
