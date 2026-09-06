from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.router.user.callbacks import MembershipCheck, UserNav, UserNavAction

HELP_BUTTON = "❓ راهنما"
BACK_BUTTON = "← بازگشت"
JOIN_BUTTON = "عضویت در کانال"
CHECK_MEMBERSHIP_BUTTON = "بررسی عضویت"


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


def membership_keyboard(code: str, channel_url: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if channel_url:
        rows.append(
            [InlineKeyboardButton(text=JOIN_BUTTON, url=channel_url)]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=CHECK_MEMBERSHIP_BUTTON,
                callback_data=MembershipCheck(code=code).pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)