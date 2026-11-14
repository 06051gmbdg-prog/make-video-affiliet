import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import common  # noqa: E402
import fetch_media  # noqa: E402
import limit  # noqa: E402
import run  # noqa: E402


class ParseSentence(unittest.TestCase):
    def test_nama_harga_link(self):
        p = common.parse_sentence("Parfum Hodl Scent Edp 75ml Paket Hemat 2 Botol Rp175.106 https://s.shopee.co.id/9V2xK7Ghfv")
        self.assertEqual(p["name"], "Parfum Hodl Scent Edp 75ml Paket Hemat 2 Botol")
        self.assertEqual(p["price"], "Rp 175.106")
        self.assertEqual(p["url"], "https://s.shopee.co.id/9V2xK7Ghfv")

    def test_link_dulu_dan_kata_harga(self):
        p = common.parse_sentence("https://s.shopee.co.id/abc Botol Minum 1 Liter Anti Bocor harga 35000")
        self.assertEqual(p["name"], "Botol Minum 1 Liter Anti Bocor")
        self.assertEqual(p["price"], "Rp 35.000")

    def test_teks_bagikan_shopee(self):
        p = common.parse_sentence("Cek USEMO CI30 Jump Starter Pompa Ban dengan harga Rp621.300. "
                                  "Dapatkan di Shopee sekarang! https://s.shopee.co.id/9zzIj5pm1Z")
        self.assertEqual(p["name"], "USEMO CI30 Jump Starter Pompa Ban")
        self.assertEqual(p["price"], "Rp 621.300")

    def test_tanpa_harga(self):
        p = common.parse_sentence("Sepatu Lari Pria https://s.shopee.co.id/abc")
        self.assertEqual(p["price"], "")

    def test_nama_dari_link_panjang(self):
        p = common.parse_sentence("https://shopee.co.id/Sepatu-Lari-Pria-Ringan-i.123456.7890123")
        self.assertEqual(p["name"], "Sepatu Lari Pria Ringan")

    def test_link_pendek_tidak_jadi_nama(self):
        self.assertEqual(common.parse_sentence("https://s.shopee.co.id/9V2xK7Ghfv")["name"], "")


class Derive(unittest.TestCase):
    def test_kelebihan_hanya_dari_nama(self):
        d = common.derive("Parfum Hodl Scent Edp 75ml Paket Hemat 2 Botol")
        self.assertEqual(d["benefits"], ["Isi 2 botol, lebih hemat", "Ukuran 75 ml per botol"])
        self.assertIn("#parfum", d["tags"])

    def test_nama_tanpa_angka(self):
        self.assertEqual(common.derive("Tas Kulit Pria")["benefits"], [])


class Variants(unittest.TestCase):
    def test_tiga_varian_berbeda(self):
        v = common.make_variants("Parfum X 75ml", "Cek Parfum X!", ["Isi 2 botol"], 3.5, 5, 3)
        self.assertEqual(len(v), 3)
        self.assertEqual(len({x["style"] for x in v}), 3)
        self.assertEqual(len({x["hook"] for x in v}), 3)
        self.assertEqual([x["rotate"] for x in v], [0, 1, 2])

    def test_jumlah_dibatasi(self):
        self.assertEqual(len(common.make_variants("A", "", [], 3.5, 3, 9)), 3)
        self.assertEqual(len(common.make_variants("A", "", [], 3.5, 3, 1)), 1)


class IssueParsing(unittest.TestCase):
    BODY = ("### Kalimat produk\n\nParfum Rp1.000 https://s.shopee.co.id/x\n\n"
            "### Foto dan klip produk\n\n![a](u)\n\n### Folder bahan di repo (opsional)\n\n_No response_\n\n"
            "### Jumlah varian\n\n2\n\n### Konfirmasi\n\n- [x] Semua foto\n- [X] Saya akan\n- [ ] Klip AI\n")

    def test_form(self):
        s = fetch_media.parse_form(self.BODY)
        self.assertEqual(fetch_media.field(s, "Folder bahan"), "")
        self.assertEqual(fetch_media.field(s, "Jumlah varian"), "2")
        lines = [x for x in fetch_media.field(s, "Konfirmasi").splitlines() if x.startswith("- [")]
        self.assertEqual(len(lines), 3)

    def test_media_berurutan(self):
        html = ('<p><img src="https://x/1?a=1&amp;b=2"></p><img class="emoji" src="https://e/1.png">'
                '<video src="https://x/clip"></video><img src="https://x/2">')
        it = fetch_media.parse_media(html)
        self.assertEqual([i["hint"] for i in it], ["photo", "clip", "photo"])
        self.assertEqual(it[0]["url"], "https://x/1?a=1&b=2")

    def test_sniff(self):
        self.assertEqual(fetch_media.sniff(b"\xff\xd8\xff\xe0")[1], "photo")
        self.assertEqual(fetch_media.sniff(b"\x00\x00\x00\x18ftypmp42")[1], "clip")
        self.assertEqual(fetch_media.sniff(b"<html>")[0], None)


class Safety(unittest.TestCase):
    def test_folder_hanya_di_bahan(self):
        self.assertIsNone(run.safe_folder("../../etc"))
        self.assertIsNone(run.safe_folder("scripts"))
        self.assertTrue(run.safe_folder("bahan/hodl").endswith(os.path.join("bahan", "hodl")))

    def test_batas_harian(self):
        old = limit.PATH
        with tempfile.TemporaryDirectory() as d:
            limit.PATH = os.path.join(d, "hari.json")
            try:
                self.assertEqual(limit.remaining(), 5)
                limit.add(3)
                self.assertEqual(limit.remaining(), 2)
                limit.add(4)
                self.assertEqual(limit.remaining(), 0)
            finally:
                limit.PATH = old


if __name__ == "__main__":
    unittest.main()
