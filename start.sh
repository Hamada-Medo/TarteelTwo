#!/bin/sh
set -e

mkdir -p /data

# Local Bot API server in the background
telegram-bot-api \
  --api-id="${TELEGRAM_API_ID}" \
  --api-hash="${TELEGRAM_API_HASH}" \
  --local \
  --http-port=8081 \
  --dir=/data/botapi &

# wait until the API server accepts connections (max ~30s)
python - <<'PY'
import socket, time
for _ in range(30):
    try:
        socket.create_connection(("localhost", 8081), 1).close()
        break
    except OSError:
        time.sleep(1)
PY

exec python bot.py
