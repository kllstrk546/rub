from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


ADMIN_PANEL_BUTTON = "Админ-панель"
PARTNER_RATE_BUTTON = "Партнёрский курс"
ADMIN_CURRENT_RATE_BUTTON = "Текущий курс"
ADMIN_REQUESTS_BUTTON = "Заявки"
ADMIN_APPROVED_USERS_BUTTON = "Одобренные пользователи"

APPROVE_REQUEST_PREFIX = "admin:approve:"
REJECT_REQUEST_PREFIX = "admin:reject:"
REVOKE_USER_PREFIX = "admin:revoke:"
REFRESH_RATE_CALLBACK = "rate:refresh"


def main_keyboard(*, is_admin: bool, is_approved: bool) -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    if not is_admin:
        return ReplyKeyboardRemove()

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ADMIN_PANEL_BUTTON)]],
        resize_keyboard=True,
        input_field_placeholder="Админ-панель",
    )


def admin_panel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_CURRENT_RATE_BUTTON)],
            [KeyboardButton(text=ADMIN_REQUESTS_BUTTON)],
            [KeyboardButton(text=ADMIN_APPROVED_USERS_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Админ-панель",
    )


def access_request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Одобрить",
                    callback_data=f"{APPROVE_REQUEST_PREFIX}{request_id}",
                ),
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"{REJECT_REQUEST_PREFIX}{request_id}",
                ),
            ]
        ]
    )


def approved_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отозвать доступ",
                    callback_data=f"{REVOKE_USER_PREFIX}{user_id}",
                )
            ]
        ]
    )


def rate_snapshot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Обновить", callback_data=REFRESH_RATE_CALLBACK)]
        ]
    )
