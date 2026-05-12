import asyncio
import logging
import sys
from contextlib import suppress
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiogram import Bot, Dispatcher
from telethon import TelegramClient

from src.bot.router import router
from src.config import Settings, get_settings
from src.db import dispose_db, init_db
from src.services.telegram_sources import TelegramSourcesService


logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


def build_bot(settings: Settings) -> Bot | None:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set; aiogram Bot was not created.")
        return None

    return Bot(token=settings.telegram_bot_token)


def build_telethon_client(settings: Settings) -> TelegramClient | None:
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        logger.warning("TELEGRAM_API_ID or TELEGRAM_API_HASH is not set; Telethon client was not created.")
        return None

    return TelegramClient(
        settings.telethon_session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info("Initializing database.")
    await init_db()

    dispatcher = build_dispatcher()
    bot = build_bot(settings)
    telethon_client = build_telethon_client(settings)
    telegram_sources: TelegramSourcesService | None = None

    try:
        if telethon_client:
            telegram_sources = TelegramSourcesService(
                client=telethon_client,
                settings=settings,
                bot=bot,
            )
            await telegram_sources.start()
            dispatcher["telegram_sources"] = telegram_sources

        if bot:
            logger.info("aiogram Bot and Dispatcher initialized.")

        if settings.start_polling and bot:
            tasks = [dispatcher.start_polling(bot)]
            if telegram_sources and telethon_client and telethon_client.is_connected():
                tasks.append(telegram_sources.run_until_disconnected())

            logger.info("Starting aiogram polling and Telethon source reader.")
            await asyncio.gather(*tasks)
        else:
            logger.info("Startup check completed. Set START_POLLING=true to run polling.")
    finally:
        if telegram_sources:
            await telegram_sources.stop()
        elif telethon_client and telethon_client.is_connected():
            await telethon_client.disconnect()

        if bot:
            await bot.session.close()

        await dispose_db()


def main() -> None:
    with suppress(KeyboardInterrupt):
        asyncio.run(run())


if __name__ == "__main__":
    main()
