import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup

from src.config import get_settings
from src.db import async_session_maker
from src.repositories.users import UserRepository


logger = logging.getLogger(__name__)


async def notify_admins(
    bot: Bot | None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if bot is None:
        logger.warning("Cannot notify admins: aiogram Bot is not initialized.")
        return

    for admin_id in await _get_admin_telegram_ids():
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup)
        except TelegramAPIError:
            logger.exception("Failed to notify admin %s.", admin_id)


async def notify_user(bot: Bot | None, telegram_id: int, text: str) -> None:
    if bot is None:
        logger.warning("Cannot notify user %s: aiogram Bot is not initialized.", telegram_id)
        return

    try:
        await bot.send_message(telegram_id, text)
    except TelegramAPIError:
        logger.exception("Failed to notify user %s.", telegram_id)


async def notify_parse_error(
    bot: Bot | None,
    source: str,
    message_text: str,
    error: str,
) -> None:
    text = (
        f"Ошибка парсинга источника: {source}\n\n"
        f"Сообщение:\n{message_text}\n\n"
        f"Ошибка:\n{error}"
    )
    await notify_admins(bot, text)


async def _get_admin_telegram_ids() -> list[int]:
    settings = get_settings()
    async with async_session_maker() as session:
        db_admins = await UserRepository(session).list_admins()

    return sorted(set(settings.admin_ids + [admin.telegram_id for admin in db_admins]))
