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

# wait until it answers (max ~15s) instead of a blind sleep
for i in 1 2 3 4 5 6 7 8 9 10; do
  nc -z localhost 8081 2>/dev/null && break
  sleep 1.5
done

exec python bot.py
