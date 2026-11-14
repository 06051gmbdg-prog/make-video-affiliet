# make-video-affiliet

Pembuat video Shopee Affiliate otomatis. Kamu kirim satu kalimat (nama produk, harga, link) dan foto produk asli.
GitHub merender sampai 3 video vertikal 9:16 (1080x1920) dengan FFmpeg, memeriksa kualitasnya, lalu menaruhnya di
**Release** supaya mudah diunduh dari HP. Kamu menonton, memeriksa, dan menekan **Posting** sendiri di aplikasi Shopee.

## Aturan wajib

1. Produk di video harus sama dengan produk sebenarnya. Pakai foto dan klip produk asli.
2. Posting dilakukan manual setelah pengecekan.
3. Bila video memuat presenter atau klip buatan AI, aturan Shopee mewajibkan label AI saat posting.
   Video dari foto produk asli dan klip orang sungguhan tidak termasuk.

## Cara pakai dari HP (paling mudah)

1. Buka repo ini di Chrome atau aplikasi GitHub, pilih tab **Issues**, lalu **New issue**.
2. Pilih **Buat video affiliate**.
3. Isi **Kalimat produk** dalam satu kalimat, contoh:
   `Parfum Hodl Scent Edp 75ml Paket Hemat 2 Botol Rp175.106 https://s.shopee.co.id/xxxx`
4. Ketuk kotak **Foto dan klip produk**, lampirkan 3 sampai 8 foto produk asli. Urutan lampiran menentukan urutan adegan.
5. Ketuk **Submit new issue**.
6. Tunggu sekitar 3 sampai 6 menit. Balasan otomatis muncul di Issue berisi hasil QC, link unduh video, dan caption.
7. Unduh videonya, tonton sampai habis, lalu posting di Shopee.

Yang dibaca otomatis dari kalimat: nama, harga (harus ditulis dengan `Rp` atau kata `harga`), dan link.
Harga tidak bisa diambil dari link, jadi harus ada di kalimat. Cek dulu harga hari ini di Shopee.

## Satu produk menjadi 3 video

Tiga varian beda dalam gaya (Sinematik, Promo cepat, Elegan), kalimat pembuka, tombol akhir, kecepatan foto, dan urutan adegan.
Kalimat pembuka dan kelebihan dibuat hanya dari kata di nama produk (misalnya isi paket dan ukuran), tanpa klaim tambahan.

## Presenter UGC

Lampirkan klip orang sungguhan yang memegang atau memakai produk (HP, vertikal 9:16, 5 sampai 8 detik). Klip dipakai
penuh layar dengan teks, harga, dan tombol akhir di atasnya, jadi hasilnya seperti iklan UGC.

## Contoh iklan UGC: USEMO CI30 (30 detik)

Contoh ini memakai struktur video review hands-on: tampilkan produk, buktikan tiap fungsi dengan tangan sendiri, tutup dengan ajakan.
Naskah di bawah ditulis ulang sendiri. Jangan memakai rekaman atau caption video orang lain. Rekam produkmu sendiri.

Kalimat produk:
`Cek USEMO CI30 Jump Starter Pompa Ban dengan harga Rp621.300. Dapatkan di Shopee sekarang! https://s.shopee.co.id/9zzIj5pm1Z`

| Detik | Adegan (rekam vertikal 9:16) | Teks di layar |
|---|---|---|
| 0-3 | Pegang produk dekat kamera, layar digital menyala | Aki lemah? Ban kempes? |
| 3-8 | Jepit kabel ke aki mobil, tunjukkan klem terpasang | Starter darurat 12V |
| 8-14 | Sambung selang ke ban, layar menampilkan tekanan PSI | Pompa ban, tekanan terlihat di layar |
| 14-19 | Nyalakan lampu, tunjukkan mode terang | Lampu LED, cocok untuk keadaan darurat |
| 19-24 | Colok HP ke port USB, tunjukkan HP mengisi | Bisa jadi power bank |
| 24-28 | Tata isi paket di meja: produk, kabel, tas, selang | Isi paket lengkap |
| 28-30 | Produk di tangan, arahkan ke keranjang | Rp621.300, cek keranjang kuning |

Caption:

```
USEMO CI30: starter darurat, pompa ban, lampu, dan power bank dalam satu alat.
Cek keranjang kuning di video ini ya!
#shopee #rekomendasi #racunshopee #usemo
Link: https://s.shopee.co.id/9zzIj5pm1Z
```

Tips rekam:
- Satu adegan satu fungsi, 3 sampai 6 detik. Rekam sebelum jam gelap supaya layar produk terbaca.
- Tunjukkan fungsi yang benar-benar kamu coba. Jangan menyebut angka (mAh, waktu isi) yang tidak ada di deskripsi Shopee.
- Cocokkan harga di teks dengan harga Shopee hari ini sebelum posting.
- Lampirkan klip-klip itu di Issue bersama 3 sampai 8 foto, lalu pilih 3 varian.

## Klip dari Veo atau Higgsfield

- Lampirkan klip di Issue (maksimal 10 MB per klip), atau unggah ke folder `bahan/nama-produk/` lewat **Add file > Upload files**
  lalu isi kolom **Folder bahan di repo**.
- Klip dipakai maksimal 8 detik, tanpa suara aslinya. Tonton klipnya dulu: bentuk, logo, dan label produk tidak boleh berubah.

## Cara lain: dari folder

1. Unggah foto ke `bahan/nama-produk/` dengan nama berurutan (`01.jpg`, `02.jpg`, ...).
2. Tab **Actions** > **Buat video** > **Run workflow**, isi kalimat dan folder.
3. Hasil ada di **Releases** (dan di Artifact pada halaman run).

## Musik

Taruh satu file musik milik sendiri atau bebas hak cipta (`.mp3`, `.m4a`, `.wav`) di folder `musik/`.
File pertama (urut nama) dipakai untuk semua video. Kosongkan folder untuk video tanpa musik.

## Batas dan QC

- Maksimal **5 video per hari** (zona waktu WIB), dihitung di `data/hari.json`. Tiga varian memakai 3 jatah.
- QC otomatis: format 9:16, durasi 10 sampai 60 detik, ukuran file, frame tidak hitam, minimal 3 adegan,
  nama dan harga terisi. Hanya video yang lulus masuk Release.

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
| `config/settings.json` | Pengaturan (durasi, batas harian, pengaturan lain) |

## Uji di komputer

```bash
sudo apt-get install -y ffmpeg fonts-dejavu-core python3-pil
python3 -m unittest discover -s tests
python3 scripts/run.py --kalimat "Nama Produk Rp49.000 https://s.shopee.co.id/xxx" \
  --folder bahan/nama-produk --no-limit
```

Hasil ada di folder `out/`.
