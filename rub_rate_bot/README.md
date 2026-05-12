# RUB Rate Bot

Telegram bot that reads RUB-related source rates through Telethon, calculates a partner rate with `Decimal`, and serves it through aiogram.

## Create A Bot

1. Open Telegram and start [@BotFather](https://t.me/BotFather).
2. Send `/newbot`.
3. Choose a display name and username for the bot.
4. BotFather will return `BOT_TOKEN`. Put it into `.env` as `TELEGRAM_BOT_TOKEN`.

## Telegram API Credentials

Telethon needs user API credentials:

1. Open [my.telegram.org](https://my.telegram.org).
2. Log in with the Telegram account that will read source channels.
3. Open `API development tools`.
4. Create an app.
5. Copy `api_id` to `TELEGRAM_API_ID`.
6. Copy `api_hash` to `TELEGRAM_API_HASH`.

## Configure .env

Create `.env` from the example:

```bash
copy .env.example .env
```

Fill the main values:

```env
TELEGRAM_BOT_TOKEN=123456:bot-token
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
TELETHON_SESSION_NAME=rub_rate_bot

NOBITEX_SOURCE=@nobitexprices
RAPIRA_SOURCE=@USDT_Rapira_bot
MARGIN_PERCENT=3.56
START_POLLING=true

RATE_REFRESH_MODE=aligned_5min
RATE_REFRESH_EVERY_MINUTES=5
RATE_REFRESH_DELAY_SECONDS=15
FETCH_LAST_MESSAGES_LIMIT=10

ADMIN_USERNAMES=bruhmomenteverytime,moreforsure
ADMIN_IDS=547486189, 7711077335
```

## Rate Refresh Logic

The default refresh mode is aligned to 5-minute source updates. With `RATE_REFRESH_DELAY_SECONDS=15`, planned refreshes happen at:

```text
00:15, 05:15, 10:15, 15:15, 20:15, 25:15,
30:15, 35:15, 40:15, 45:15, 50:15, 55:15
```

Every scheduled refresh calls Telegram through Telethon. It reads the latest `FETCH_LAST_MESSAGES_LIMIT` messages from each source, takes the newest parseable Nobitex and Rapira messages, calculates a new `RateSnapshot`, and stores source `message_id`, `message_date`, `created_at`, and `refresh_reason`.

The user `Обновить` button forces a real source refresh with `refresh_reason=manual_button`; it does not simply redisplay the last DB value. The user-facing message stays compact and does not show calculation details:

```text
Актуальный курс:

1 RUB = 2 277 TOMAN

Биткоин: 80,653 $
USDT: 180,400 تومان
Унция золота: 4,692 $
Нефть: 107,53 $

Обновлено: 12.05.2026 11:36:00
```

Admin `/admin_rate` forces a refresh with `refresh_reason=admin_manual` and may show calculation/debug details. Admin `/admin_sources` shows the latest 3 messages visible to Telethon and what each parser extracted.

## Run Locally

```bash
pip install -r requirements.txt
python -m src.main
```

## Run With Docker

```bash
docker compose up -d --build
```

`docker-compose.yml` stores SQLite at `/app/data/bot.db` and the Telethon session at `/app/telethon/rub_rate_bot.session`.

## First Telethon Login

The first Telethon run needs Telegram user authorization. Locally:

```bash
python scripts/telethon_login.py
```

Enter your phone number, Telegram code, and 2FA password if prompted. This creates `rub_rate_bot.session`.

For Docker, run an interactive login once:

```bash
docker compose run --rm bot python scripts/telethon_login.py
```

The session is saved into the `./telethon` volume.

## Add Admins

Admins can be configured by username, Telegram ID, or both:

```env
ADMIN_USERNAMES=bruhmomenteverytime,moreforsure
ADMIN_IDS=547486189, 7711077335
```

The bot marks a user as admin when they run `/start` or `/admin` and match one of these values.

## Check The Bot

Open the bot in Telegram and run:

```text
/start
/admin
/rate
/admin_rate
/admin_sources
```

`/admin`, `/admin_rate`, and `/admin_sources` are available only to admins. `/rate` is available to admins and approved users.

## Verify

```bash
python -m pytest -q
docker compose config
```
