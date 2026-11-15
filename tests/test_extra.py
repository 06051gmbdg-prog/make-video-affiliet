import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import pixabay  # noqa: E402

HITS = {"hits": [
    {"id": 1, "duration": 2, "videos": {"medium": {"url": "https://cdn.pixabay.com/a.mp4", "size": 100}}},
    {"id": 2, "duration": 9, "videos": {"medium": {"url": "https://cdn.pixabay.com/b.mp4", "size": 99999999999}}},
    {"id": 3, "duration": 9, "videos": {"medium": {"url": "https://cdn.pixabay.com/c.mp4", "size": 1000}}},
    {"id": 4, "duration": 9, "videos": {"small": {"url": "https://evil.example.com/d.mp4", "size": 1000}}},
    {"id": 5, "duration": 9, "videos": {"small": {"url": "https://cdn.pixabay.com/e.mp4", "size": 1000}}},
]}


class TestPixabay(unittest.TestCase):
    def test_bersihkan(self):
        self.assertEqual(pixabay.bersihkan("  car; road&key=x  night "), "car road key x night")

    def test_pilih(self):
        got = pixabay.pilih(HITS["hits"], 5)
        self.assertEqual([g["id"] for g in got], [3, 4, 5])  # durasi pendek dan file terlalu besar dibuang

    def test_tanpa_kunci(self):
        self.assertEqual(pixabay.ambil_broll("car", tempfile.mkdtemp(), 2, key=""), [])

    def test_unduh_hanya_host_pixabay(self):
        calls = []

        def fake(url, timeout=30):
            calls.append(url)
            return json.dumps(HITS).encode() if "api/videos" in url else b"VIDEO"

        old = pixabay._get
        pixabay._get = fake
        try:
            d = tempfile.mkdtemp()
            items = pixabay.ambil_broll("car road", d, 3, key="K")
        finally:
            pixabay._get = old
        self.assertEqual([os.path.basename(i["path"]) for i in items],
                         ["pixabay-3.mp4", "pixabay-5.mp4"])  # host evil.example.com dilewati
        self.assertTrue(all(i["kind"] == "clip" for i in items))

    def test_gagal_tidak_menghentikan(self):
        def boom(url, timeout=30):
            raise OSError("jaringan putus KUNCI")
        old = pixabay._get
        pixabay._get = boom
        try:
            self.assertEqual(pixabay.ambil_broll("car", tempfile.mkdtemp(), 2, key="KUNCI"), [])
        finally:
            pixabay._get = old


class TestTelegram(unittest.TestCase):
    def test_kirim_dan_lewati(self):
        got = []

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                got.append((self.path, body))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ok":true}')

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "x.mp4"), "wb") as f:
            f.write(b"0" * 2048)
        with open(os.path.join(d, "x.txt"), "w", encoding="utf8") as f:
            f.write("Caption uji " + "a" * 2000)
        sh = os.path.join(ROOT, "scripts", "kirim_telegram.sh")
        env = dict(os.environ, TELEGRAM_BOT_TOKEN="TOK", TELEGRAM_CHAT_ID="123",
                   TELEGRAM_API=f"http://127.0.0.1:{srv.server_port}")
        r = subprocess.run(["bash", sh, d], env=env, capture_output=True, text=True)
        srv.shutdown()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 terkirim", r.stdout)
        self.assertNotIn("TOK", r.stdout + r.stderr)
        self.assertEqual(got[0][0], "/botTOK/sendVideo")
        self.assertIn(b"Caption uji", got[0][1])
        self.assertNotIn(b"a" * 1001, got[0][1])  # caption dipotong 1000 karakter

        env.pop("TELEGRAM_BOT_TOKEN")
        r = subprocess.run(["bash", sh, d], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("dilewati", r.stdout)


if __name__ == "__main__":
    unittest.main()
