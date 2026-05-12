import asyncio
import sys
from pathlib import Path

from telethon import TelegramClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings  # noqa: E402


async def main() -> None:
    settings = get_settings()
    client = TelegramClient(
        settings.telethon_session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )

    async with client:
        if await client.is_user_authorized():
            me = await client.get_me()
            username = f"@{me.username}" if me and me.username else "no username"
            print(f"Telethon already authorized as {username}.")
            return

        print("Telethon authorization is required.")
        print("Enter your phone number, Telegram code, and 2FA password if prompted.")
        await client.start()
        me = await client.get_me()
        username = f"@{me.username}" if me and me.username else "no username"
        print(f"Telethon authorized successfully as {username}.")


if __name__ == "__main__":
    asyncio.run(main())
