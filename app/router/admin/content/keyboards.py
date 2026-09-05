from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CONFIRM_LABELS = {
    "activate": "بله، فعال کن ✅",
    "deactivate": "بله، غیرفعال کن ⛔",
    "delete": "بله، حذف کن 🗑️",
}
CANCEL_LABEL = "انصراف ❌"


def confirmation_keyboard(action: str, code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=CONFIRM_LABELS[action],
                    callback_data=f"content:{action}:{code}",
                ),
                InlineKeyboardButton(
                    text=CANCEL_LABEL,
                    callback_data=f"content:cancel:{code}",
                ),
            ]
        ]
    )


def pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup | None:
    buttons: list[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="قبلی ◀️",
                callback_data=f"content:list:{page - 1}",
            )
        )
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="بعدی ▶️",
                callback_data=f"content:list:{page + 1}",
            )
        )

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=[buttons])