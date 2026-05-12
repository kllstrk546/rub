from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import REFRESH_RATE_CALLBACK, rate_snapshot_keyboard
from src.db import async_session_maker
from src.repositories.rates import RateRepository
from src.services.telegram_sources import TelegramSourcesService
from src.utils.formatting import format_rate_snapshot


router = Router(name="user")


@router.message(CommandStart())
async def handle_start(
    message: Message,
    telegram_sources: TelegramSourcesService | None = None,
) -> None:
    snapshot = await _get_public_rate_snapshot(
        telegram_sources=telegram_sources,
        reason="user_start",
    )
    if snapshot is None:
        await message.answer("Курс пока недоступен")
        return

    await message.answer(format_rate_snapshot(snapshot), reply_markup=rate_snapshot_keyboard())


@router.message(Command("rate"))
async def handle_rate(
    message: Message,
    telegram_sources: TelegramSourcesService | None = None,
) -> None:
    snapshot = await _get_public_rate_snapshot(
        telegram_sources=telegram_sources,
        reason="user_start",
    )
    if snapshot is None:
        await message.answer("Курс пока недоступен")
        return

    await message.answer(format_rate_snapshot(snapshot), reply_markup=rate_snapshot_keyboard())


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer("Команды:\n/start - показать актуальный курс\n/rate - обновить курс")


@router.callback_query(F.data == REFRESH_RATE_CALLBACK)
async def handle_refresh_rate(
    callback: CallbackQuery,
    telegram_sources: TelegramSourcesService | None = None,
) -> None:
    snapshot = await _get_public_rate_snapshot(
        telegram_sources=telegram_sources,
        reason="manual_button",
    )
    if snapshot is None:
        await callback.answer("Курс пока недоступен.", show_alert=True)
        return

    if callback.message is not None:
        try:
            await callback.message.edit_text(
                format_rate_snapshot(snapshot),
                reply_markup=rate_snapshot_keyboard(),
            )
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).casefold():
                await callback.answer("Курс уже актуален")
                return
            await callback.message.answer(
                format_rate_snapshot(snapshot),
                reply_markup=rate_snapshot_keyboard(),
            )
        except TelegramAPIError:
            await callback.message.answer(
                format_rate_snapshot(snapshot),
                reply_markup=rate_snapshot_keyboard(),
            )

    await callback.answer("Обновлено")


async def _get_public_rate_snapshot(
    *,
    telegram_sources: TelegramSourcesService | None,
    reason: str,
):
    if telegram_sources is not None:
        return await telegram_sources.force_refresh_rate(reason=reason)

    async with async_session_maker() as session:
        return await RateRepository(session).get_latest_snapshot()
