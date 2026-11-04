# Stage 1: prebuilt Telegram Bot API server binary
FROM aiogram/telegram-bot-api:latest AS botapi

# Stage 2: the bot (Alpine to match the musl-linked binary)
FROM python:3.12-alpine

# libstdc++/libgcc: needed by telegram-bot-api and PyMuPDF (ffmpeg used to pull them in)
RUN apk add --no-cache ca-certificates libstdc++ libgcc

COPY --from=botapi /usr/local/bin/telegram-bot-api /usr/local/bin/telegram-bot-api

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

CMD ["./start.sh"]
