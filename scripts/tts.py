"""Suara narasi (voice-over) bahasa Indonesia.

Urutan mesin: edge-tts (suara jernih, perlu internet) lalu espeak-ng (cadangan, suara robot).
Gagal semua -> kembalikan "" dan video dibuat tanpa suara narasi.
Naskah hanya dari nama, harga, dan kalimat pembuka. Tidak ada klaim tambahan.
"""
import asyncio
import os
import re
import shutil
import subprocess

SUARA = {"perempuan": "id-ID-GadisNeural", "laki-laki": "id-ID-ArdiNeural"}
_SAT = ["nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"]


def terbilang(n):
    n = int(n)
    if n < 12:
        return _SAT[n]
    if n < 20:
        return terbilang(n - 10) + " belas"
    if n < 100:
        return terbilang(n // 10) + " puluh" + (" " + terbilang(n % 10) if n % 10 else "")
    if n < 200:
        return "seratus" + (" " + terbilang(n - 100) if n > 100 else "")
    if n < 1000:
        return terbilang(n // 100) + " ratus" + (" " + terbilang(n % 100) if n % 100 else "")
    if n < 2000:
        return "seribu" + (" " + terbilang(n - 1000) if n > 1000 else "")
    if n < 10**6:
        return terbilang(n // 1000) + " ribu" + (" " + terbilang(n % 1000) if n % 1000 else "")
    if n < 10**9:
        return terbilang(n // 10**6) + " juta" + (" " + terbilang(n % 10**6) if n % 10**6 else "")
    return terbilang(n // 10**9) + " miliar" + (" " + terbilang(n % 10**9) if n % 10**9 else "")


def harga_ucap(price):
    d = re.sub(r"\D", "", price or "")
    return (terbilang(int(d)) + " rupiah") if d else ""


def naskah(hook, benefits, price, cta):
    """Dua bagian: pembuka (di awal video) dan penutup (selaras kartu akhir)."""
    intro = [re.sub(r"[!?.]+$", "", hook or "").strip()] + [b for b in (benefits or [])]
    intro = ". ".join(x for x in intro if x) + "."
    hu = harga_ucap(price)
    outro = (f"Harganya {hu}. " if hu else "") + (cta or "cek keranjang kuning").lower() + \
        " di Shopee sekarang."
    return intro, outro


def _edge(teks, out, suara, rate):
    import edge_tts

    async def go():
        await edge_tts.Communicate(teks, suara, rate=rate).save(out)
    asyncio.run(go())


def _espeak(teks, out):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("espeak tidak ada")
    wav = out + ".wav"
    subprocess.run([exe, "-v", "id", "-s", "150", "-w", wav, teks], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "128k", out], check=True)
    os.remove(wav)


def buat_suara(teks, out, jenis="perempuan", rate="+0%"):
    """Tulis mp3 ke `out`. Kembalikan path, atau "" bila semua mesin gagal."""
    if not (teks or "").strip():
        return ""
    for nama, fn in (("edge-tts", lambda: _edge(teks, out, SUARA.get(jenis, SUARA["perempuan"]), rate)),
                     ("espeak-ng", lambda: _espeak(teks, out))):
        try:
            fn()
            if os.path.exists(out) and os.path.getsize(out) > 1000:
                return out
        except Exception as e:  # noqa: BLE001
            print(f"Suara {nama} gagal: {str(e)[:160]}")
    return ""
