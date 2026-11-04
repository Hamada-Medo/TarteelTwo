# Stage 1: prebuilt Telegram Bot API server binary
FROM aiogram/telegram-bot-api:latest AS botapi

# Stage 2: the bot (Alpine to match the musl-linked binary)
FROM python:3.12-alpine

RUN apk add --no-cache ca-certificates

COPY --from=botapi /usr/local/bin/telegram-bot-api /usr/local/bin/telegram-bot-api

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

CMD ["./start.sh"]
