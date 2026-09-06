from aiogram import F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.services.content_service import (
    SUPPORTED_CONTENT_TYPES,
    UnsupportedContentError,
    create_content_upload,
)

from .callbacks import AdminNav, AdminNavAction
from .keyboards import back_keyboard, dashboard_keyboard
from .router import admins

UNSUPPORTED_CONTENT_REPLY = "این نوع پیام پشتیبانی نمی‌شود."
INVALID_REQUEST_REPLY = "درخواست نامعتبر."

DASHBOARD_TEXT = (
    "🎛 پنل مدیریت دانو\n"
    "\n"
    "مدیریت محتوای آموزشی و فایل‌های ربات"
)

UPLOAD_PROMPT_TEXT = (
    "📤 افزودن محتوا\n"
    "\n"
    "فایل، ویدیو یا محتوای موردنظر را ارسال کنید.\n"
    "پس از ذخیره، لینک دسترسی ساخته می‌شود."
)

MANAGE_HINT_TEXT = (
    "📚 مدیریت محتوا\n"
    "\n"
    "برای مشاهده و مدیریت محتوا از دستور /list استفاده کنید."
)

ADMIN_HELP_TEXT = (
    "❓ راهنمای مدیریت\n"
    "\n"
    "• افزودن محتوا: فایل را مستقیم ارسال کنید یا از دکمه 📤 استفاده کنید.\n"
    "• مشاهده محتوا: /list\n"
    "• فعال یا غیرفعال کردن: /activate و /deactivate\n"
    "• حذف محتوا: /delete (با تأیید)\n"
    "• تنظیم انقضا: /expire"
)


async def _show_screen(
    query: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None
) -> None:
    if query.message is not None:
        try:
            await query.message.edit_text(text, reply_markup=reply_markup)
        except TelegramAPIError:
            pass
    await query.answer()


@admins.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    await message.answer(DASHBOARD_TEXT, reply_markup=dashboard_keyboard())


@admins.message(F.content_type.in_(SUPPORTED_CONTENT_TYPES))
async def content_upload_handler(message: Message) -> None:
    bot_username = message.bot.username if message.bot is not None else None

    try:
        result = await create_content_upload(
            source_chat_id=message.chat.id,
            source_message_id=message.message_id,
            content_type=message.content_type,
            bot_username=bot_username,
        )
    except UnsupportedContentError:
        await message.answer(UNSUPPORTED_CONTENT_REPLY)
        return

    await message.answer(
        "محتوا با موفقیت ذخیره شد.\n"
        f"لینک دسترسی:\n{result.deep_link}"
    )


@admins.message(~F.text.startswith("/"))
async def unsupported_content_handler(message: Message) -> None:
    await message.answer(UNSUPPORTED_CONTENT_REPLY)


@admins.callback_query(AdminNav.filter())
async def admin_navigation_callback(
    query: CallbackQuery, callback_data: AdminNav
) -> None:
    if callback_data.action == AdminNavAction.DASHBOARD:
        await _show_screen(query, DASHBOARD_TEXT, dashboard_keyboard())
    elif callback_data.action == AdminNavAction.UPLOAD:
        await _show_screen(query, UPLOAD_PROMPT_TEXT, back_keyboard())
    elif callback_data.action == AdminNavAction.MANAGE:
        await _show_screen(query, MANAGE_HINT_TEXT, back_keyboard())
    elif callback_data.action == AdminNavAction.HELP:
        await _show_screen(query, ADMIN_HELP_TEXT, back_keyboard())
    else:
        await query.answer(INVALID_REQUEST_REPLY)
