# make-video-affiliet

Pembuat video Shopee Affiliate otomatis. Kamu kirim satu kalimat (nama produk, harga, link) dan foto produk asli.
GitHub merender sampai 3 video vertikal 9:16 (1080x1920) dengan FFmpeg, memeriksa kualitasnya, lalu menaruhnya di
**Release** supaya mudah diunduh dari HP. Kamu menonton, memeriksa, dan menekan **Posting** sendiri di aplikasi Shopee.

## Aturan wajib

1. Video yang memakai AI harus diberi **label AI** saat diposting lewat aplikasi Shopee.
2. Produk di video harus sama dengan produk sebenarnya. Pakai foto produk asli.
3. Posting dilakukan manual setelah pengecekan.

Form meminta dua konfirmasi pertama sebelum render jalan. Kalau ada klip AI, ada konfirmasi ketiga.

## Cara pakai dari HP (paling mudah)

1. Buka repo ini di Chrome atau aplikasi GitHub, pilih tab **Issues**, lalu **New issue**.
2. Pilih **Buat video affiliate**.
3. Isi **Kalimat produk** dalam satu kalimat, contoh:
   `Parfum Hodl Scent Edp 75ml Paket Hemat 2 Botol Rp175.106 https://s.shopee.co.id/xxxx`
4. Ketuk kotak **Foto dan klip produk**, lampirkan 3 sampai 8 foto produk asli. Urutan lampiran menentukan urutan adegan.
5. Centang konfirmasi, lalu **Submit new issue**.
6. Tunggu sekitar 3 sampai 6 menit. Balasan otomatis muncul di Issue berisi hasil QC, link unduh video, dan caption.
7. Unduh videonya, tonton sampai habis, lalu posting di Shopee dengan **label AI aktif**.

Yang dibaca otomatis dari kalimat: nama, harga (harus ditulis dengan `Rp` atau kata `harga`), dan link.
Harga tidak bisa diambil dari link, jadi harus ada di kalimat. Cek dulu harga hari ini di Shopee.

## Satu produk menjadi 3 video

Tiga varian beda dalam gaya (Sinematik, Promo cepat, Elegan), kalimat pembuka, tombol akhir, kecepatan foto, dan urutan adegan.
Kalimat pembuka dan kelebihan dibuat hanya dari kata di nama produk (misalnya isi paket dan ukuran), tanpa klaim tambahan.

## Klip dari Veo atau Higgsfield

- Lampirkan klip di Issue (maksimal 10 MB per klip), atau unggah ke folder `bahan/nama-produk/` lewat **Add file > Upload files**
  lalu isi kolom **Folder bahan di repo**.
- Klip dipakai maksimal 8 detik, tanpa suara aslinya. Tonton klipnya dulu: bentuk, logo, dan label produk tidak boleh berubah.

## Cara lain: dari folder

1. Unggah foto ke `bahan/nama-produk/` dengan nama berurutan (`01.jpg`, `02.jpg`, ...).
2. Tab **Actions** > **Buat video** > **Run workflow**, isi kalimat dan folder, centang konfirmasi.
3. Hasil ada di **Releases** (dan di Artifact pada halaman run).

## Musik

Taruh satu file musik milik sendiri atau bebas hak cipta (`.mp3`, `.m4a`, `.wav`) di folder `musik/`.
File pertama (urut nama) dipakai untuk semua video. Kosongkan folder untuk video tanpa musik.

## Batas dan QC

- Maksimal **5 video per hari** (zona waktu WIB), dihitung di `data/hari.json`. Tiga varian memakai 3 jatah.
- QC otomatis: format 9:16, durasi 10 sampai 60 detik, ukuran file, frame tidak hitam, minimal 3 adegan,
  nama dan harga terisi, konfirmasi lengkap. Hanya video yang lulus masuk Release.

## Keamanan

- Hanya Issue yang dibuat oleh pemilik repo yang diproses, jadi orang lain tidak bisa memakai jatah renderan.
- Repo publik berarti foto, video, dan link yang kamu kirim bisa dilihat siapa saja. Ubah ke privat di **Settings** bila perlu.

## Isi repo

| Lokasi | Fungsi |
|---|---|
| `.github/ISSUE_TEMPLATE/video.yml` | Form di HP |
| `.github/workflows/buat-video.yml` | Otomatisasi: render, Release, balasan di Issue |
| `scripts/run.py` | Alur utama: kalimat, bahan, render, QC, caption, ringkasan |
| `scripts/render.py` | Render FFmpeg: zoom foto, klip, transisi, teks, harga, kartu akhir, musik |
| `scripts/qc.py` | Pemeriksaan kualitas |
| `scripts/fetch_media.py` | Ambil kalimat dan lampiran dari Issue |
| `config/settings.json` | Pengaturan (durasi, batas harian, penanda AI) |

## Uji di komputer

```bash
sudo apt-get install -y ffmpeg fonts-dejavu-core python3-pil
python3 -m unittest discover -s tests
python3 scripts/run.py --kalimat "Nama Produk Rp49.000 https://s.shopee.co.id/xxx" \
  --folder bahan/nama-produk --konfirmasi-asli --konfirmasi-ai --no-limit
```

Hasil ada di folder `out/`.
