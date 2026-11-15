"""Orkestrator: kalimat produk + bahan -> sampai 3 video, QC, caption, ringkasan.

Contoh lokal:
  python scripts/run.py --kalimat "Nama Produk Rp49.000 https://s.shopee.co.id/xxx" \
      --folder bahan/contoh --konfirmasi-asli --konfirmasi-ai
"""
import argparse
import json
import os
import shutil
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import limit  # noqa: E402
import pixabay  # noqa: E402
from common import (MUSIC_EXT, ROOT, STYLES, build_caption, derive, load_settings,  # noqa: E402
                    make_variants, parse_sentence, slugify)
from qc import qc_video  # noqa: E402
from render import Ctx, list_media, prepare, render_variant  # noqa: E402


GAGAL_UNDUH = []


def write_summary(out, lines):
    os.makedirs(out, exist_ok=True)
    if GAGAL_UNDUH:
        lines = list(lines) + ["", "### Lampiran yang tidak bisa dipakai"] + ["- " + g for g in GAGAL_UNDUH] + [
            "Gunakan foto JPG, PNG, atau WEBP dan klip MP4, MOV, atau WEBM."]
    with open(os.path.join(out, "ringkasan.md"), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


def fail(out, msg):
    write_summary(out, ["## Video belum dibuat", "", msg, "",
                        "Perbaiki lalu buka Issue baru, atau jalankan ulang."])
    print("GAGAL:", msg, file=sys.stderr)
    sys.exit(2)


def pick_music():
    d = os.path.join(ROOT, "musik")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(MUSIC_EXT):
                return os.path.join(d, f)
    return ""


def safe_folder(rel):
    """Folder bahan harus berada di dalam repo/bahan."""
    if not rel:
        return ""
    base = os.path.realpath(os.path.join(ROOT, "bahan"))
    p = os.path.realpath(os.path.join(ROOT, rel))
    if p != base and not p.startswith(base + os.sep):
        return None
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kalimat", default="")
    ap.add_argument("--folder", default="")
    ap.add_argument("--meta", default="")
    ap.add_argument("--varian", type=int, default=0)
    ap.add_argument("--suasana", default="", help="kata kunci klip suasana Pixabay (opsional)")
    ap.add_argument("--out", default="out")
    ap.add_argument("--repo", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--konfirmasi-asli", action="store_true")
    ap.add_argument("--konfirmasi-ai", action="store_true")
    ap.add_argument("--konfirmasi-klip", action="store_true")
    ap.add_argument("--no-limit", action="store_true")
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    settings = load_settings()

    kalimat, folder, varian, konf = a.kalimat, a.folder, a.varian, [False, False, False]
    suasana = a.suasana
    extra = []
    if a.meta:
        with open(a.meta, encoding="utf8") as f:
            meta = json.load(f)
        kalimat = kalimat or meta.get("kalimat", "")
        folder = folder or meta.get("folder", "")
        suasana = suasana or meta.get("suasana", "")
        varian = varian or int(meta.get("varian") or 0)
        konf = (list(meta.get("konfirmasi") or []) + [False] * 3)[:3]
        extra = meta.get("media") or []
        GAGAL_UNDUH.extend(meta.get("gagal_unduh") or [])
    konf[0] = konf[0] or a.konfirmasi_asli
    konf[1] = konf[1] or a.konfirmasi_ai
    konf[2] = konf[2] or a.konfirmasi_klip
    varian = varian or int(settings["varian_default"])

    # 1. produk dari satu kalimat
    prod = parse_sentence(kalimat)
    if not prod["name"]:
        fail(out, "Nama produk tidak terbaca dari kalimat. Tulis nama produk, harga (Rp...), lalu link.")
    if not prod["price"]:
        fail(out, "Harga belum ada. Tulis harga di kalimat, misalnya `Rp175.106`. "
                  "Cek dulu harga hari ini di Shopee.")
    d = derive(prod["name"])

    # 2. bahan: folder repo lalu lampiran
    items = []
    if folder:
        p = safe_folder(folder)
        if p is None or not os.path.isdir(p):
            fail(out, f"Folder bahan `{folder}` tidak ada. Folder harus berada di dalam `bahan/`.")
        items += list_media(p)
    items += [x for x in extra if os.path.exists(x.get("path", ""))]
    amax = int(settings["adegan_maks"])
    if len(items) > amax:
        items = items[:amax]
    if len(items) < int(settings["foto_min"]):
        fail(out, f"Bahan kurang: {len(items)} adegan, minimal {settings['foto_min']}. "
                  "Lampirkan foto produk asli atau isi folder bahan.")
    has_clip = any(x["kind"] == "clip" for x in items)

    # 2b. klip suasana dari Pixabay (opsional, hanya latar; produk tetap dari fotomu)
    broll = os.path.join(out, ".broll")
    if suasana:
        extra_b = pixabay.ambil_broll(suasana, broll, n=2)
        for pos, b in zip((1, 3), extra_b):
            items.insert(min(pos, len(items)), b)
        has_clip = has_clip or bool(extra_b)
        print(f"Pixabay: {len(extra_b)} klip suasana ('{suasana}')")

    # 3. batas harian
    count = varian
    if not a.no_limit:
        rem = limit.remaining()
        if rem <= 0:
            fail(out, f"Jatah {settings['video_per_hari']} video hari ini sudah habis. Lanjut besok.")
        count = min(varian, rem)

    # 4. render
    work = os.path.join(out, ".work")
    ctx = Ctx(work, settings)
    try:
        media = prepare(ctx, items)
        music = pick_music()
        variants = make_variants(prod["name"], d["hook"], d["benefits"], float(settings["per_foto"]),
                                 len(media), count)
        slug = slugify(prod["name"])
        os.makedirs(os.path.join(out, "siap_upload"), exist_ok=True)
        os.makedirs(os.path.join(out, "gagal_qc"), exist_ok=True)
        results = []
        for var in variants:
            n = len(media)
            rot = var["rotate"]
            order = media[rot:] + media[:rot]
            fname = f"{slug}-{var['label'].split()[-1].lower()}.mp4"
            tmp = os.path.join(out, fname)
            print("Render", var["label"], STYLES[var["style"]]["label"], flush=True)
            render_variant(ctx, order, var, {"name": prod["name"], "price": prod["price"],
                                             "benefits": d["benefits"]}, music, tmp)
            caption = build_caption(prod["name"], var["hook"], d["benefits"], d["tags"], prod["url"], has_clip)
            ok, checks = qc_video(tmp, {"name": prod["name"], "price": prod["price"], "n_scenes": n,
                                        "konfirmasi_asli": konf[0], "konfirmasi_ai": konf[1],
                                        "konfirmasi_klip": konf[2], "has_clip": has_clip,
                                        "caption": caption}, settings)
            dest = os.path.join(out, "siap_upload" if ok else "gagal_qc")
            shutil.move(tmp, os.path.join(dest, fname))
            with open(os.path.join(dest, fname[:-4] + ".txt"), "w", encoding="utf8") as f:
                f.write(caption)
            results.append({"label": var["label"], "style": STYLES[var["style"]]["label"], "file": fname,
                            "ok": ok, "checks": checks, "hook": var["hook"]})
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        fail(out, "Render gagal: " + str(e)[:900])
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(broll, ignore_errors=True)

    if not a.no_limit:
        limit.add(len(results))

    # 5. ringkasan
    base = f"https://github.com/{a.repo}/releases/download/{a.tag}/" if a.repo and a.tag else ""
    lines = [f"## {len(results)} video selesai: {prod['name']}", "",
             f"Harga: {prod['price']}  |  Adegan: {len(media)} (klip: {sum(1 for m in media if m['kind'] == 'clip')})", ""]
    for r in results:
        lines.append(f"### {r['label']} ({r['style']}): {'LULUS QC' if r['ok'] else 'GAGAL QC'}")
        lines.append(f"Kalimat pembuka: {r['hook']}")
        for c in r["checks"]:
            lines.append(f"- {'OK' if c['ok'] else 'XX'} {c['label']}")
        if r["ok"] and base:
            lines.append(f"- [Unduh video]({base}{r['file']}) | [Caption]({base}{r['file'][:-4]}.txt)")
        elif not r["ok"]:
            lines.append("- Video ini tidak masuk rilis. Ada di Artifact pada halaman Actions.")
        lines.append("")
    lines += ["### Sebelum menekan Posting di Shopee",
              "1. Tonton video sampai habis. Produk harus sama dengan yang dijual.",
              "2. Cocokkan harga di video dengan harga di Shopee hari ini.",
              "", f"Jatah hari ini terpakai: {settings['video_per_hari'] - limit.remaining()}"
              f" dari {settings['video_per_hari']} video."]
    write_summary(out, lines)
    with open(os.path.join(out, "hasil.json"), "w", encoding="utf8") as f:
        json.dump({"produk": prod, "hasil": results}, f, ensure_ascii=False, indent=2)
    ok_n = sum(1 for r in results if r["ok"])
    print(f"Selesai: {ok_n} lulus dari {len(results)}")
    if ok_n == 0:
        sys.exit(3)


if __name__ == "__main__":
    main()
