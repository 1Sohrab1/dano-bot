from aiogram import F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.models import Content, ContentState
from app.router.admin.content.callbacks import ContentUx, ContentUxAction
from app.router.admin.content.keyboards import (
    confirmation_keyboard,
    content_detail_keyboard,
    content_list_keyboard,
    delete_confirm_keyboard,
    expiration_keyboard,
)
from app.router.admin.content.router import content_admin
from app.router.admin.content.states import ExpirationStates
from app.router.admin.router import admins
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
INVALID_EXPIRATION_INPUT_REPLY = "لطفاً تعداد روزهای اعتبار را به‌صورت عدد وارد کنید."
INVALID_EXPIRATION_VALUE_REPLY = "مقدار انقضا نامعتبر است."
LIST_EMPTY_REPLY = "📭 محتوایی برای نمایش وجود ندارد."
EXPIRATION_PROMPT_TEXT = (
    "🗓 تنظیم انقضا\n"
    "\n"
    "تعداد روزهای اعتبار را ارسال کنید.\n"
    "\n"
    "برای حذف انقضا:"
)
DELETE_CONFIRM_TEXT = (
    "⚠️ حذف محتوا\n"
    "\n"
    "این عملیات غیرقابل بازگشت است.\n"
    "\n"
    "آیا مطمئن هستید؟"
)
CANCEL_REPLY = "عملیات لغو شد."
SUCCESS_EXPIRATION_CLEARED_REPLY = "انقضای محتوا حذف شد."

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


def _expiration_label(content: Content) -> str:
    if content.expires_at is None:
        return "بدون انقضا"
    return content.expires_at.strftime("%Y-%m-%d %H:%M")


def _confirmation_text(action: str, content: Content) -> str:
    if action == "delete":
        return DELETE_CONFIRM_TEXT

    lines = [
        f"کد: `{content.code}`",
        f"نوع: {content.content_type}",
        f"وضعیت: {_state_label(content.state)}",
    ]
    if action == "activate":
        lines.insert(0, "آیا می‌خواهید محتوا را فعال کنید؟")
    else:
        lines.insert(0, "آیا می‌خواهید محتوا را غیرفعال کنید؟")
    return "\n".join(lines)


def format_content_list(result: ContentPage) -> str:
    if not result.items:
        return LIST_EMPTY_REPLY

    lines = [
        "📚 مدیریت محتوا",
        "",
        f"صفحه {result.page} از {result.total_pages}",
    ]
    for item in result.items:
        lines.append(
            f"`{item.code}` | {item.content_type} | {_state_label(item.state)} | {_expiration_label(item)}"
        )
    return "\n".join(lines)


def format_content_detail(content: Content) -> str:
    return "\n".join(
        [
            "📄 اطلاعات محتوا",
            "",
            f"کد: {content.code}",
            f"نوع: {content.content_type}",
            f"وضعیت: {_state_label(content.state)}",
            f"انقضا: {_expiration_label(content)}",
        ]
    )


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
        format_content_list(result),
        reply_markup=content_list_keyboard(result),
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


async def _edit_text(
    query: CallbackQuery,
    text: str,
    reply_markup=None,
) -> None:
    if query.message is None:
        return
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramAPIError:
        pass


async def _clear_message(query: CallbackQuery, text: str) -> None:
    await _edit_text(query, text)


async def _render_page(query: CallbackQuery, page_value: int | str) -> None:
    try:
        page = int(page_value)
    except ValueError:
        await query.answer(INVALID_PAGE_REPLY)
        return

    result = await content_management_service.list_content(page)
    await _edit_text(
        query,
        format_content_list(result),
        content_list_keyboard(result),
    )
    await query.answer()


async def _render_detail(query: CallbackQuery, code: str, page: int) -> bool:
    try:
        content = await content_management_service.preview_content(code)
    except InvalidContentCodeError:
        await query.answer(INVALID_CODE_REPLY)
        return False
    except ContentNotFoundError:
        await query.answer(CONTENT_NOT_FOUND_REPLY)
        return False

    await _edit_text(
        query,
        format_content_detail(content),
        content_detail_keyboard(content, page),
    )
    return True


async def _render_delete_confirm(query: CallbackQuery, code: str, page: int) -> bool:
    try:
        content = await content_management_service.preview_content(code)
    except InvalidContentCodeError:
        await query.answer(INVALID_CODE_REPLY)
        return False
    except ContentNotFoundError:
        await query.answer(CONTENT_NOT_FOUND_REPLY)
        return False

    await _edit_text(
        query,
        DELETE_CONFIRM_TEXT,
        delete_confirm_keyboard(content.code, page),
    )
    return True


async def _run_state_mutation(
    query: CallbackQuery, action: str, code: str, page: int
) -> None:
    actor = query.from_user.id if query.from_user is not None else 0
    try:
        updated = await _MUTATORS[action](code, actor=actor)
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
    await _edit_text(
        query,
        format_content_detail(updated),
        content_detail_keyboard(updated, page),
    )


async def _confirm_delete(query: CallbackQuery, code: str) -> None:
    actor = query.from_user.id if query.from_user is not None else 0
    try:
        await content_management_service.delete_content(code, actor=actor)
    except InvalidContentCodeError:
        await query.answer(INVALID_CODE_REPLY)
        return
    except ContentNotFoundError:
        await query.answer(CONTENT_NOT_FOUND_REPLY)
        return

    await query.answer(_SUCCESS_REPLIES["delete"])
    await _clear_message(query, _SUCCESS_REPLIES["delete"])


async def _start_expiration(
    query: CallbackQuery, state: FSMContext, code: str, page: int
) -> None:
    chat_id = query.message.chat.id if query.message is not None else None
    message_id = query.message.message_id if query.message is not None else None

    await state.set_state(ExpirationStates.awaiting_days)
    await state.update_data(
        code=code,
        page=page,
        chat_id=chat_id,
        message_id=message_id,
    )

    await _edit_text(query, EXPIRATION_PROMPT_TEXT, expiration_keyboard(code, page))
    await query.answer()


async def _clear_expiration(
    query: CallbackQuery, state: FSMContext, code: str, page: int
) -> None:
    await state.clear()

    actor = query.from_user.id if query.from_user is not None else 0
    try:
        updated = await content_management_service.set_content_expiration(
            code, None, actor=actor
        )
    except InvalidContentCodeError:
        await query.answer(INVALID_CODE_REPLY)
        return
    except ContentNotFoundError:
        await query.answer(CONTENT_NOT_FOUND_REPLY)
        return

    await query.answer(SUCCESS_EXPIRATION_CLEARED_REPLY)
    await _edit_text(
        query,
        format_content_detail(updated),
        content_detail_keyboard(updated, page),
    )


@content_admin.callback_query(ContentUx.filter())
async def content_ux_callback(
    query: CallbackQuery, callback_data: ContentUx, state: FSMContext
) -> None:
    action = callback_data.action
    code = callback_data.code
    page = callback_data.page

    if action == ContentUxAction.LIST:
        await _render_page(query, page)
        return
    if action == ContentUxAction.DETAIL:
        if await _render_detail(query, code, page):
            await query.answer()
        return
    if action == ContentUxAction.ACTIVATE:
        await _run_state_mutation(query, "activate", code, page)
        return
    if action == ContentUxAction.DEACTIVATE:
        await _run_state_mutation(query, "deactivate", code, page)
        return
    if action == ContentUxAction.DELETE_START:
        if await _render_delete_confirm(query, code, page):
            await query.answer()
        return
    if action == ContentUxAction.DELETE_CONFIRM:
        await _confirm_delete(query, code)
        return
    if action == ContentUxAction.EXPIRE:
        await _start_expiration(query, state, code, page)
        return
    if action == ContentUxAction.EXPIRE_OFF:
        await _clear_expiration(query, state, code, page)
        return
    if action == ContentUxAction.CANCEL:
        await state.clear()
        await query.answer(CANCEL_REPLY)
        await _render_detail(query, code, page)
        return

    await query.answer(INVALID_REQUEST_REPLY)


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


@content_admin.callback_query(F.data.startswith("content:"))
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
        await query.answer(CANCEL_REPLY)
        await _clear_message(query, CANCEL_REPLY)
        return
    if action == "list":
        await _render_page(query, payload)
        return
    if action not in _MUTATORS:
        await query.answer(INVALID_REQUEST_REPLY)
        return

    await _apply_mutation(query, action, payload)


async def _replace_prompt(message: Message, text: str, data: dict) -> None:
    bot = getattr(message, "bot", None)
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")

    if bot is None or not chat_id or not message_id or not hasattr(bot, "edit_message_text"):
        return
    try:
        await bot.edit_message_text(
            text, chat_id=chat_id, message_id=message_id
        )
    except TelegramAPIError:
        return


@admins.message(StateFilter(ExpirationStates.awaiting_days), F.text.isdigit())
async def expiration_days_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    code = data.get("code", "")

    if not code:
        await state.clear()
        await message.answer(CONTENT_NOT_FOUND_REPLY)
        return

    actor = message.from_user.id if message.from_user is not None else 0
    day_input = int(message.text or "0")
    try:
        updated = await content_management_service.set_content_expiration(
            code,
            day_input,
            actor=actor,
        )
    except InvalidContentCodeError:
        await state.clear()
        await message.answer(INVALID_CODE_REPLY)
        return
    except ContentNotFoundError:
        await state.clear()
        await message.answer(CONTENT_NOT_FOUND_REPLY)
        return
    except InvalidExpirationValueError:
        await message.answer(INVALID_EXPIRATION_VALUE_REPLY)
        return

    success = (
        f"انقضای محتوا روی "
        f"{updated.expires_at.strftime('%Y-%m-%d %H:%M')} تنظیم شد."
    )
    await _replace_prompt(message, success, data)
    await state.clear()
    await message.answer(success)


@admins.message(
    StateFilter(ExpirationStates.awaiting_days),
    ~F.text.startswith("/"),
    ~F.text.isdigit(),
)
async def expiration_invalid_handler(message: Message) -> None:
    await message.answer(INVALID_EXPIRATION_INPUT_REPLY)