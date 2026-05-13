from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import (
    ADMIN_APPROVED_USERS_BUTTON,
    ADMIN_CURRENT_RATE_BUTTON,
    ADMIN_PANEL_BUTTON,
    ADMIN_REQUESTS_BUTTON,
    APPROVE_REQUEST_PREFIX,
    REJECT_REQUEST_PREFIX,
    REVOKE_USER_PREFIX,
    access_request_keyboard,
    admin_panel_keyboard,
    approved_user_keyboard,
    rate_snapshot_keyboard,
)
from src.bot.handlers_user import _format_user_identity, _sync_config_admin
from src.db import async_session_maker
from src.models import AccessRequest, User
from src.repositories.rates import RateRepository
from src.repositories.requests import AccessRequestRepository
from src.repositories.users import UserRepository
from src.services.notification_service import notify_user
from src.services.telegram_sources import TelegramSourcesService
from src.utils.formatting import format_datetime, format_rate_snapshot


router = Router(name="admin")


@router.message(Command("admin"))
@router.message(F.text == ADMIN_PANEL_BUTTON)
async def handle_admin_panel(message: Message) -> None:
    if not await _ensure_admin_message(message):
        return

    await message.answer("Админ-панель", reply_markup=admin_panel_keyboard())


@router.message(Command("admin_rate"))
@router.message(F.text == ADMIN_CURRENT_RATE_BUTTON)
async def handle_admin_current_rate(
    message: Message,
    telegram_sources: TelegramSourcesService | None = None,
) -> None:
    if not await _ensure_admin_message(message):
        return

    if telegram_sources is not None:
        snapshot = await telegram_sources.force_refresh_rate(reason="admin_manual")
    else:
        async with async_session_maker() as session:
            snapshot = await RateRepository(session).get_latest_snapshot()

    if snapshot is None:
        await message.answer("Курс пока недоступен")
        return

    await message.answer(
        format_rate_snapshot(snapshot),
        reply_markup=rate_snapshot_keyboard(),
    )


@router.message(Command("admin_sources"))
async def handle_admin_sources(
    message: Message,
    telegram_sources: TelegramSourcesService | None = None,
) -> None:
    if not await _ensure_admin_message(message):
        return

    if telegram_sources is None:
        await message.answer("Telethon source service недоступен.")
        return

    async with async_session_maker() as session:
        snapshot = await RateRepository(session).get_latest_snapshot()

    if snapshot is None:
        await message.answer("Источники подключены. Курс пока не сохранён.")
        return

    await message.answer(
        "Источники подключены.\n"
        f"Nobitex: {telegram_sources.settings.nobitex_source}\n"
        f"Rapira: {telegram_sources.settings.rapira_source}\n"
        f"Последнее обновление: {format_datetime(snapshot.created_at)}"
    )


@router.message(Command("admin_sources_debug"))
async def handle_admin_sources_debug(
    message: Message,
    telegram_sources: TelegramSourcesService | None = None,
) -> None:
    if not await _ensure_admin_message(message):
        return

    if telegram_sources is None:
        await message.answer("Telethon source service недоступен.")
        return

    await message.answer(await telegram_sources.describe_recent_sources(limit=3))


@router.message(F.text == ADMIN_REQUESTS_BUTTON)
async def handle_admin_requests(message: Message) -> None:
    if not await _ensure_admin_message(message):
        return

    async with async_session_maker() as session:
        pending_requests = await AccessRequestRepository(session).list_pending_requests()

    if not pending_requests:
        await message.answer("Pending-заявок нет.")
        return

    await message.answer(f"Pending-заявок: {len(pending_requests)}")
    for access_request in pending_requests:
        await message.answer(
            _format_access_request(access_request),
            reply_markup=access_request_keyboard(access_request.id),
        )


@router.message(F.text == ADMIN_APPROVED_USERS_BUTTON)
async def handle_admin_approved_users(message: Message) -> None:
    if not await _ensure_admin_message(message):
        return

    async with async_session_maker() as session:
        approved_users = await UserRepository(session).list_approved_users()

    if not approved_users:
        await message.answer("Одобренных пользователей нет.")
        return

    await message.answer(f"Одобренных пользователей: {len(approved_users)}")
    for user in approved_users:
        await message.answer(
            _format_approved_user(user),
            reply_markup=approved_user_keyboard(user.id),
        )


@router.callback_query(F.data.startswith(APPROVE_REQUEST_PREFIX))
async def handle_approve_request(callback: CallbackQuery, bot: Bot) -> None:
    if not await _ensure_admin_callback(callback):
        return

    request_id = _parse_callback_id(callback.data, APPROVE_REQUEST_PREFIX)
    if request_id is None:
        await callback.answer("Некорректная заявка.", show_alert=True)
        return

    async with async_session_maker() as session:
        users = UserRepository(session)
        admin = await users.create_or_update_from_telegram(callback.from_user)
        await _sync_config_admin(admin, users)
        access_request = await AccessRequestRepository(session).approve_request(
            request_id,
            processed_by_admin_id=admin.id,
        )
        if access_request is None:
            await session.commit()
            await callback.answer("Заявка не найдена.", show_alert=True)
            return

        user = await users.get_by_id(access_request.user_id)
        await session.commit()

    if user is not None:
        await notify_user(bot, user.telegram_id, "Ваша заявка одобрена.")

    await _edit_callback_message(callback, f"Заявка #{request_id} одобрена.")
    await callback.answer("Одобрено")


@router.callback_query(F.data.startswith(REJECT_REQUEST_PREFIX))
async def handle_reject_request(callback: CallbackQuery, bot: Bot) -> None:
    if not await _ensure_admin_callback(callback):
        return

    request_id = _parse_callback_id(callback.data, REJECT_REQUEST_PREFIX)
    if request_id is None:
        await callback.answer("Некорректная заявка.", show_alert=True)
        return

    async with async_session_maker() as session:
        users = UserRepository(session)
        admin = await users.create_or_update_from_telegram(callback.from_user)
        await _sync_config_admin(admin, users)
        access_request = await AccessRequestRepository(session).reject_request(
            request_id,
            processed_by_admin_id=admin.id,
        )
        if access_request is None:
            await session.commit()
            await callback.answer("Заявка не найдена.", show_alert=True)
            return

        user = await users.get_by_id(access_request.user_id)
        await session.commit()

    if user is not None:
        await notify_user(bot, user.telegram_id, "Ваша заявка отклонена.")

    await _edit_callback_message(callback, f"Заявка #{request_id} отклонена.")
    await callback.answer("Отклонено")


@router.callback_query(F.data.startswith(REVOKE_USER_PREFIX))
async def handle_revoke_user(callback: CallbackQuery) -> None:
    if not await _ensure_admin_callback(callback):
        return

    user_id = _parse_callback_id(callback.data, REVOKE_USER_PREFIX)
    if user_id is None:
        await callback.answer("Некорректный пользователь.", show_alert=True)
        return

    async with async_session_maker() as session:
        users = UserRepository(session)
        user = await users.get_by_id(user_id)
        if user is None:
            await callback.answer("Пользователь не найден.", show_alert=True)
            return

        user.is_approved = False
        await session.commit()

    await _edit_callback_message(callback, f"Доступ пользователя #{user_id} отозван.")
    await callback.answer("Доступ отозван")


async def _ensure_admin_message(message: Message) -> bool:
    if message.from_user is None:
        return False

    if await _is_admin(message.from_user):
        return True

    await message.answer("Команда доступна только администраторам.")
    return False


async def _ensure_admin_callback(callback: CallbackQuery) -> bool:
    if await _is_admin(callback.from_user):
        return True

    await callback.answer("Действие доступно только администраторам.", show_alert=True)
    return False


async def _is_admin(telegram_user: object) -> bool:
    async with async_session_maker() as session:
        users = UserRepository(session)
        user = await users.create_or_update_from_telegram(telegram_user)
        await _sync_config_admin(user, users)
        is_admin = user.is_admin
        await session.commit()
        return is_admin


def _format_access_request(access_request: AccessRequest) -> str:
    user = access_request.user
    created_at = access_request.created_at.strftime("%d.%m.%Y %H:%M")
    username = f"@{user.username}" if user.username else "-"
    return (
        f"Заявка #{access_request.id}\n"
        f"ID пользователя: {user.id}\n"
        f"Telegram ID: {user.telegram_id}\n"
        f"Username: {username}\n"
        f"First name: {user.first_name or '-'}\n"
        f"Дата заявки: {created_at}"
    )


def _format_approved_user(user: User) -> str:
    return (
        f"Пользователь #{user.id}\n"
        f"{_format_user_identity(user)}\n"
        f"Telegram ID: {user.telegram_id}"
    )


def _parse_callback_id(data: str | None, prefix: str) -> int | None:
    if data is None or not data.startswith(prefix):
        return None

    try:
        return int(data.removeprefix(prefix))
    except ValueError:
        return None


async def _edit_callback_message(callback: CallbackQuery, text: str) -> None:
    if callback.message is None:
        return

    await callback.message.edit_text(text)
