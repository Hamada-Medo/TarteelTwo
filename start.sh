#!/bin/sh
set -e

mkdir -p /data/botapi

# Local Bot API server in the background
telegram-bot-api \
  --api-id="${TELEGRAM_API_ID}" \
  --api-hash="${TELEGRAM_API_HASH}" \
  --local \
  --http-port=8081 \
  --dir=/data/botapi &
API_PID=$!

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

if ! kill -0 "$API_PID" 2>/dev/null; then
  echo "telegram-bot-api failed to start (see error above)"
  exit 1
fi

exec python bot.py
