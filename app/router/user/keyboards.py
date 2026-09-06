from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.router.user.callbacks import UserNav, UserNavAction

HELP_BUTTON = "❓ راهنما"
BACK_BUTTON = "← بازگشت"


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=HELP_BUTTON,
                    callback_data=UserNav(action=UserNavAction.HELP).pack(),
                )
            ]
        ]
    )


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=BACK_BUTTON,
                    callback_data=UserNav(action=UserNavAction.START).pack(),
                )
            ]
        ]
    )
