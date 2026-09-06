from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.router.admin.callbacks import AdminNav, AdminNavAction

UPLOAD_BUTTON = "📤 افزودن محتوا"
MANAGE_BUTTON = "📚 مدیریت محتوا"
HELP_BUTTON = "❓ راهنما"
BACK_BUTTON = "← بازگشت به پنل"


def dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=UPLOAD_BUTTON,
                    callback_data=AdminNav(action=AdminNavAction.UPLOAD).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=MANAGE_BUTTON,
                    callback_data=AdminNav(action=AdminNavAction.MANAGE).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=HELP_BUTTON,
                    callback_data=AdminNav(action=AdminNavAction.HELP).pack(),
                )
            ],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=BACK_BUTTON,
                    callback_data=AdminNav(action=AdminNavAction.DASHBOARD).pack(),
                )
            ]
        ]
    )
