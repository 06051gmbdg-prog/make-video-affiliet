#!/usr/bin/env bash
# Kirim video yang lulus QC ke Telegram (video + caption).
# Perlu env TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID. Tanpa keduanya, langkah dilewati.
# Pemakaian: scripts/kirim_telegram.sh [folder, default out/siap_upload]
set -u
DIR="${1:-out/siap_upload}"
API="${TELEGRAM_API:-https://api.telegram.org}"

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "Telegram dilewati: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diisi."
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
ok=0; gagal=0

for f in "$DIR"/*.mp4; do
  [ -e "$f" ] || { echo "Tidak ada video di $DIR."; exit 0; }
  size=$(stat -c %s "$f")
  if [ "$size" -gt 50000000 ]; then
    echo "Dilewati (lebih dari 50 MB, batas bot Telegram): $(basename "$f")"; gagal=$((gagal+1)); continue
  fi
  # Caption maksimal 1024 karakter. Isi file dibaca dari file, tidak lewat shell.
  python3 - "${f%.mp4}.txt" "$tmp/caption.txt" <<'PY'
import sys
try:
    t = open(sys.argv[1], encoding="utf8").read()
except OSError:
    t = ""
open(sys.argv[2], "w", encoding="utf8").write(t[:1000])
PY
  resp=$(curl -sS --max-time 240 "$API/bot${TELEGRAM_BOT_TOKEN}/sendVideo" \
    -F "chat_id=${TELEGRAM_CHAT_ID}" -F "supports_streaming=true" \
    -F "caption=<$tmp/caption.txt" -F "video=@$f" 2>&1) || true
  if printf '%s' "$resp" | grep -q '"ok":true'; then
    echo "Terkirim: $(basename "$f")"; ok=$((ok+1))
  else
    # Jangan cetak seluruh respons: bisa memuat URL berisi token.
    desc=$(printf '%s' "$resp" | grep -o '"description":"[^"]*"' | head -1)
    echo "GAGAL kirim $(basename "$f") ${desc:-}"; gagal=$((gagal+1))
  fi
done
echo "Telegram: $ok terkirim, $gagal gagal."
