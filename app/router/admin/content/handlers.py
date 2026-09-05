from aiogram import F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.database.models import Content, ContentState
from app.router.admin.content.keyboards import (
    confirmation_keyboard,
    pagination_keyboard,
)
from app.router.admin.content.router import content_admin
from app.services import content_management_service
from app.services.content_management_service import (
    ContentAlreadyActiveError,
    ContentAlreadyInactiveError,
    ContentNotFoundError,
    ContentPage,
    InvalidContentCodeError,
    InvalidExpirationValueError,
)

INVALID_CODE_REPLY = "کد محتوا نامعتبر است."
CONTENT_NOT_FOUND_REPLY = "محتوا یافت نشد."
ALREADY_ACTIVE_REPLY = "این محتوا از قبل فعال است."
ALREADY_INACTIVE_REPLY = "این محتوا از قبل غیرفعال است."
INVALID_EXPIRATION_REPLY = (
    "مقدار انقضا نامعتبر است.\n"
    "از `/expire <code> <days>` یا `/expire <code> off` استفاده کنید."
)
INVALID_PAGE_REPLY = "شماره صفحه نامعتبر است."
INVALID_REQUEST_REPLY = "درخواست نامعتبر."

_MUTATORS = {
    "activate": content_management_service.activate_content,
    "deactivate": content_management_service.deactivate_content,
    "delete": content_management_service.delete_content,
}
_SUCCESS_REPLIES = {
    "activate": "محتوا فعال شد ✅",
    "deactivate": "محتوا غیرفعال شد ⛔",
    "delete": "محتوا حذف شد 🗑️",
}


def _state_label(state: str) -> str:
    return "فعال" if state == ContentState.ACTIVE else "غیرفعال"


def _confirmation_text(action: str, content: Content) -> str:
    lines = [
        f"کد: `{content.code}`",
        f"نوع: {content.content_type}",
        f"وضعیت: {_state_label(content.state)}",
    ]
    if action == "activate":
        lines.insert(0, "آیا می‌خواهید محتوا را فعال کنید؟")
    elif action == "deactivate":
        lines.insert(0, "آیا می‌خواهید محتوا را غیرفعال کنید؟")
    else:
        lines.insert(0, "⚠️ حذف محتوا غیرقابل بازگشت است.\nآیا مطمئن هستید؟")
    return "\n".join(lines)


def _format_content_list(result: ContentPage) -> str:
    if not result.items:
        return "محتویی یافت نشد."

    lines = [f"صفحه {result.page} از {result.total_pages}"]
    for item in result.items:
        expiry = (
            item.expires_at.strftime("%Y-%m-%d %H:%M")
            if item.expires_at is not None
            else "بدون انقضا"
        )
        lines.append(
            f"`{item.code}` | {item.content_type} | {_state_label(item.state)} | {expiry}"
        )
    return "\n".join(lines)


@content_admin.message(Command("list"))
async def list_handler(message: Message, command: CommandObject) -> None:
    page = 1
    if command.args:
        try:
            page = int(command.args)
        except ValueError:
            await message.answer(INVALID_PAGE_REPLY)
            return

    result = await content_management_service.list_content(page)
    await message.answer(
        _format_content_list(result),
        reply_markup=pagination_keyboard(result.page, result.total_pages),
    )


async def _confirm_command(message: Message, command: CommandObject, action: str) -> None:
    code = command.args or ""
    try:
        content = await content_management_service.preview_content(code)
    except InvalidContentCodeError:
        await message.answer(INVALID_CODE_REPLY)
        return
    except ContentNotFoundError:
        await message.answer(CONTENT_NOT_FOUND_REPLY)
        return

    if action == "activate" and content.state == ContentState.ACTIVE:
        await message.answer(ALREADY_ACTIVE_REPLY)
        return
    if action == "deactivate" and content.state == ContentState.INACTIVE:
        await message.answer(ALREADY_INACTIVE_REPLY)
        return

    await message.answer(
        _confirmation_text(action, content),
        reply_markup=confirmation_keyboard(action, code),
    )


@content_admin.message(Command("activate"))
async def activate_command_handler(message: Message, command: CommandObject) -> None:
    await _confirm_command(message, command, "activate")


@content_admin.message(Command("deactivate"))
async def deactivate_command_handler(message: Message, command: CommandObject) -> None:
    await _confirm_command(message, command, "deactivate")


@content_admin.message(Command("delete"))
async def delete_command_handler(message: Message, command: CommandObject) -> None:
    await _confirm_command(message, command, "delete")


@content_admin.message(Command("expire"))
async def expire_command_handler(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer(INVALID_EXPIRATION_REPLY)
        return

    parts = command.args.split(maxsplit=1)
    code = parts[0]
    value = parts[1].strip() if len(parts) > 1 else ""
    if value.lower() in {"off", "none"}:
        days = None
    else:
        try:
            days = int(value)
        except ValueError:
            await message.answer(INVALID_EXPIRATION_REPLY)
            return

    try:
        updated = await content_management_service.set_content_expiration(
            code,
            days,
            actor=message.from_user.id if message.from_user is not None else 0,
        )
    except InvalidContentCodeError:
        await message.answer(INVALID_CODE_REPLY)
        return
    except ContentNotFoundError:
        await message.answer(CONTENT_NOT_FOUND_REPLY)
        return
    except InvalidExpirationValueError:
        await message.answer(INVALID_EXPIRATION_REPLY)
        return

    if days is None:
        await message.answer("انقضای محتوا حذف شد.")
    else:
        await message.answer(
            f"انقضای محتوا روی {updated.expires_at.strftime('%Y-%m-%d %H:%M')} تنظیم شد."
        )


async def _apply_mutation(query: CallbackQuery, action: str, code: str) -> None:
    actor = query.from_user.id if query.from_user is not None else 0
    try:
        await _MUTATORS[action](code, actor=actor)
    except InvalidContentCodeError:
        await query.answer(INVALID_CODE_REPLY)
        return
    except ContentNotFoundError:
        await query.answer(CONTENT_NOT_FOUND_REPLY)
        return
    except ContentAlreadyActiveError:
        await query.answer(ALREADY_ACTIVE_REPLY)
        return
    except ContentAlreadyInactiveError:
        await query.answer(ALREADY_INACTIVE_REPLY)
        return

    await query.answer(_SUCCESS_REPLIES[action])
    await _clear_message(query, _SUCCESS_REPLIES[action])


async def _clear_message(query: CallbackQuery, text: str) -> None:
    if query.message is None:
        return
    try:
        await query.message.edit_text(text)
    except TelegramAPIError:
        return


async def _render_page(query: CallbackQuery, page_value: str) -> None:
    try:
        page = int(page_value)
    except ValueError:
        await query.answer(INVALID_PAGE_REPLY)
        return

    result = await content_management_service.list_content(page)
    if query.message is not None:
        await query.message.edit_text(
            _format_content_list(result),
            reply_markup=pagination_keyboard(result.page, result.total_pages),
        )
    await query.answer()


@content_admin.callback_query(F.data)
async def content_action_callback(query: CallbackQuery) -> None:
    if query.data is None:
        return

    parts = query.data.split(":", 2)
    if len(parts) != 3 or parts[0] != "content":
        await query.answer(INVALID_REQUEST_REPLY)
        return

    action = parts[1]
    payload = parts[2]

    if action == "cancel":
        await query.answer("عملیات لغو شد.")
        await _clear_message(query, "عملیات لغو شد.")
        return
    if action == "list":
        await _render_page(query, payload)
        return
    if action not in _MUTATORS:
        await query.answer(INVALID_REQUEST_REPLY)
        return

    await _apply_mutation(query, action, payload)