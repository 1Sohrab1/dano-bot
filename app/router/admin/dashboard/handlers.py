from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from app.router.admin.callbacks import AdminNav, AdminNavAction
from app.router.admin.content.handlers import format_content_list
from app.router.admin.content.keyboards import content_list_keyboard
from app.router.admin.dashboard.router import dashboard_admin
from app.router.admin.keyboards import back_keyboard, dashboard_keyboard
from app.services import content_management_service

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


@dashboard_admin.callback_query(AdminNav.filter())
async def admin_navigation_callback(
    query: CallbackQuery, callback_data: AdminNav
) -> None:
    if callback_data.action == AdminNavAction.DASHBOARD:
        await _show_screen(query, DASHBOARD_TEXT, dashboard_keyboard())
    elif callback_data.action == AdminNavAction.UPLOAD:
        await _show_screen(query, UPLOAD_PROMPT_TEXT, back_keyboard())
    elif callback_data.action == AdminNavAction.MANAGE:
        result = await content_management_service.list_content(1)
        await _show_screen(
            query,
            format_content_list(result),
            content_list_keyboard(result),
        )
    elif callback_data.action == AdminNavAction.HELP:
        await _show_screen(query, ADMIN_HELP_TEXT, back_keyboard())
    else:
        await query.answer(INVALID_REQUEST_REPLY)
