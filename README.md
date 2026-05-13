# RUB Rate Bot

Public Telegram bot for showing the current RUB/TOMAN partner rate.

The bot uses:

- aiogram for Telegram bot polling
- Telethon for reading source Telegram channels
- SQLAlchemy async with SQLite
- Decimal-only rate calculations

Any user can run `/start` or `/rate` and receive the latest calculated rate with one inline button: `Обновить`.

## Environment

Create `.env` from `.env.example`:

```bash
copy .env.example .env
```

Required variables:

```env
TELEGRAM_BOT_TOKEN=123456:bot-token
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
TELETHON_SESSION_NAME=rub_rate_bot
START_POLLING=true

NOBITEX_SOURCE=@nobitexprices
RAPIRA_SOURCE=@USDT_Rapira_bot
MARGIN_PERCENT=3.56
```

`BOT_TOKEN` is also supported as a backward-compatible alias for `TELEGRAM_BOT_TOKEN`.

## Local Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run a startup check:

```bash
python src/main.py
```

Run the live bot with polling enabled:

```bash
python src/main.py
```

Make sure `.env` contains `START_POLLING=true`.

## First Telethon Login

Telethon needs a user session before it can read source channels.

Run:

```bash
python scripts/telethon_login.py
```

Enter your phone number, Telegram code, and 2FA password if Telegram asks for it. This creates the local `rub_rate_bot.session` file.

Do not commit real `.env`, SQLite databases, logs, or Telethon session files to GitHub. Configure environment variables on the deployment platform instead.

## Docker

Build and run locally:

```bash
docker compose up -d --build
```

The compose file stores SQLite data in `./data` and Telethon session files in `./telethon`.

## Deployment

Use this start command on Railway, Render, Relay-like platforms, or any worker host:

```bash
python src/main.py
```

A `Procfile` is included:

```Procfile
worker: python src/main.py
```

Docker deploys can use the included `Dockerfile`.

## Checks

Run tests:

```bash
python -m pytest -q
```

Validate Docker Compose:

```bash
docker compose config --quiet
```
