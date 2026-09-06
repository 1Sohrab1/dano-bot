from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import Content, ContentState
from app.router.admin.callbacks import AdminNav, AdminNavAction
from app.router.admin.content.callbacks import ContentUx, ContentUxAction
from app.services.content_management_service import ContentPage

CONFIRM_LABELS = {
    "activate": "بله، فعال کن ✅",
    "deactivate": "بله، غیرفعال کن ⛔",
    "delete": "🗑 بله، حذف کن",
}
CANCEL_LABEL = "لغو"

DEACTIVATE_BUTTON = "⛔ غیرفعال کردن"
ACTIVATE_BUTTON = "✅ فعال کردن"
EXPIRATION_BUTTON = "🗓 تنظیم انقضا"
DELETE_BUTTON = "🗑 حذف محتوا"
BACK_DETAILS_BUTTON = "← بازگشت"
BACK_DASHBOARD_BUTTON = "← بازگشت به پنل"
DELETE_CONFIRM_BUTTON = "🗑 بله، حذف کن"
NO_EXPIRATION_BUTTON = "بدون انقضا"
PREVIOUS_BUTTON = "قبلی ◀️"
NEXT_BUTTON = "بعدی ▶️"


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


def content_list_keyboard(result: ContentPage) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"📄 {item.code}",
                callback_data=ContentUx(
                    action=ContentUxAction.DETAIL,
                    code=item.code,
                    page=result.page,
                ).pack(),
            )
        ]
        for item in result.items
    ]

    pagination: list[InlineKeyboardButton] = []
    if result.page > 1:
        pagination.append(
            InlineKeyboardButton(
                text=PREVIOUS_BUTTON,
                callback_data=ContentUx(
                    action=ContentUxAction.LIST,
                    page=result.page - 1,
                ).pack(),
            )
        )
    if result.page < result.total_pages:
        pagination.append(
            InlineKeyboardButton(
                text=NEXT_BUTTON,
                callback_data=ContentUx(
                    action=ContentUxAction.LIST,
                    page=result.page + 1,
                ).pack(),
            )
        )
    if pagination:
        rows.append(pagination)

    rows.append(
        [
            InlineKeyboardButton(
                text=BACK_DASHBOARD_BUTTON,
                callback_data=AdminNav(action=AdminNavAction.DASHBOARD).pack(),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def content_detail_keyboard(content: Content, page: int) -> InlineKeyboardMarkup:
    if content.state == ContentState.ACTIVE:
        state_action = (
            ContentUxAction.DEACTIVATE,
            DEACTIVATE_BUTTON,
        )
    else:
        state_action = (
            ContentUxAction.ACTIVATE,
            ACTIVATE_BUTTON,
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=state_action[1],
                    callback_data=ContentUx(
                        action=state_action[0],
                        code=content.code,
                        page=page,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=EXPIRATION_BUTTON,
                    callback_data=ContentUx(
                        action=ContentUxAction.EXPIRE,
                        code=content.code,
                        page=page,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=DELETE_BUTTON,
                    callback_data=ContentUx(
                        action=ContentUxAction.DELETE_START,
                        code=content.code,
                        page=page,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=BACK_DETAILS_BUTTON,
                    callback_data=ContentUx(
                        action=ContentUxAction.LIST,
                        page=page,
                    ).pack(),
                )
            ],
        ]
    )


def delete_confirm_keyboard(code: str, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=DELETE_CONFIRM_BUTTON,
                    callback_data=ContentUx(
                        action=ContentUxAction.DELETE_CONFIRM,
                        code=code,
                        page=page,
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=CANCEL_LABEL,
                    callback_data=ContentUx(
                        action=ContentUxAction.CANCEL,
                        code=code,
                        page=page,
                    ).pack(),
                ),
            ]
        ]
    )


def expiration_keyboard(code: str, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=NO_EXPIRATION_BUTTON,
                    callback_data=ContentUx(
                        action=ContentUxAction.EXPIRE_OFF,
                        code=code,
                        page=page,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=CANCEL_LABEL,
                    callback_data=ContentUx(
                        action=ContentUxAction.CANCEL,
                        code=code,
                        page=page,
                    ).pack(),
                )
            ],
        ]
    )