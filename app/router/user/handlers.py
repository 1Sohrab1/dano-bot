from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.services.access_service import (
    ContentExpiredError,
    ContentInactiveError,
    ContentNotFoundError,
    DeliveryError,
    InvalidContentCodeError,
    MembershipRequiredError,
    deliver_content,
)
from app.services.channel_service import resolve_required_channel_url
from app.services.identity_service import ensure_user

from .callbacks import MembershipCheck, UserNav, UserNavAction
from .keyboards import help_keyboard, membership_keyboard, welcome_keyboard
from .router import users

UNSUPPORTED_CODE_REPLY = "لینک دسترسی نامعتبر است."
CONTENT_NOT_FOUND_REPLY = "محتوا یافت نشد."
CONTENT_INACTIVE_REPLY = "این محتوا در دسترس نیست."
CONTENT_EXPIRED_REPLY = "این محتوا منقضی شده است"
MEMBERSHIP_REQUIRED_REPLY = "برای دریافت این محتوا ابتدا باید عضو کانال شوید."
MEMBERSHIP_PENDING_REPLY = "هنوز عضو کانال نشده‌اید. ابتدا در کانال عضو شوید."
MEMBERSHIP_RESOLVED_REPLY = "این محتوا برای شما ارسال شد."
DELIVERY_ERROR_REPLY = "دریافت محتوا با خطا مواجه شد. لطفاً بعداً تلاش کنید."
INVALID_REQUEST_REPLY = "درخواست نامعتبر."

WELCOME_TEXT = (
    "سلام 👋\n"
    "به دانو بات خوش اومدی 🎓\n"
    "\n"
    "از اینجا می‌تونی به محتواهای آموزشی دانو دسترسی داشته باشی؛\n"
    "کافیه روی لینک دسترسی یک محتوا بزنی تا برات ارسال بشه."
)

HELP_TEXT = (
    "❓ راهنمای دانو بات\n"
    "\n"
    "• برای دریافت یک محتوا، روی لینک دسترسی آن بزن.\n"
    "• اگر عضویت در کانال لازم باشد، ربات راهنماییت می‌کند.\n"
    "• برای شروع دوباره، دستور /start را بفرست."
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


@users.message(CommandStart(deep_link=False))
async def start_handler(message: Message) -> None:
    if message.from_user is not None:
        await ensure_user(message.from_user.id)

    await message.answer(WELCOME_TEXT, reply_markup=welcome_keyboard())


@users.message(CommandStart(deep_link=True))
async def content_deep_link_handler(message: Message, command: CommandObject) -> None:
    if message.from_user is None or message.bot is None:
        return

    await ensure_user(message.from_user.id)

    try:
        await deliver_content(
            message.bot,
            code=command.args or "",
            user_id=message.from_user.id,
        )
    except InvalidContentCodeError:
        await message.answer(UNSUPPORTED_CODE_REPLY)
    except ContentNotFoundError:
        await message.answer(CONTENT_NOT_FOUND_REPLY)
    except ContentInactiveError:
        await message.answer(CONTENT_INACTIVE_REPLY)
    except ContentExpiredError:
        await message.answer(CONTENT_EXPIRED_REPLY)
    except MembershipRequiredError:
        await message.answer(
            MEMBERSHIP_REQUIRED_REPLY,
            reply_markup=membership_keyboard(
                command.args or "",
                await resolve_required_channel_url(message.bot),
            ),
        )
    except DeliveryError:
        await message.answer(DELIVERY_ERROR_REPLY)


@users.callback_query(UserNav.filter())
async def user_navigation_callback(
    query: CallbackQuery, callback_data: UserNav
) -> None:
    if callback_data.action == UserNavAction.HELP:
        await _show_screen(query, HELP_TEXT, help_keyboard())
    elif callback_data.action == UserNavAction.START:
        await _show_screen(query, WELCOME_TEXT, welcome_keyboard())
    else:
        await query.answer(INVALID_REQUEST_REPLY)


async def _resolve_prompt(query: CallbackQuery, text: str) -> None:
    if query.message is not None:
        try:
            await query.message.edit_text(text)
        except TelegramAPIError:
            pass


@users.callback_query(MembershipCheck.filter())
async def membership_check_callback(
    query: CallbackQuery, callback_data: MembershipCheck, bot: Bot
) -> None:
    if query.from_user is None:
        return

    try:
        await deliver_content(
            bot,
            code=callback_data.code,
            user_id=query.from_user.id,
        )
    except MembershipRequiredError:
        await query.answer(MEMBERSHIP_PENDING_REPLY)
        return
    except InvalidContentCodeError:
        await query.answer(UNSUPPORTED_CODE_REPLY)
        await _resolve_prompt(query, UNSUPPORTED_CODE_REPLY)
        return
    except ContentNotFoundError:
        await query.answer(CONTENT_NOT_FOUND_REPLY)
        await _resolve_prompt(query, CONTENT_NOT_FOUND_REPLY)
        return
    except ContentInactiveError:
        await query.answer(CONTENT_INACTIVE_REPLY)
        await _resolve_prompt(query, CONTENT_INACTIVE_REPLY)
        return
    except ContentExpiredError:
        await query.answer(CONTENT_EXPIRED_REPLY)
        await _resolve_prompt(query, CONTENT_EXPIRED_REPLY)
        return
    except DeliveryError:
        await query.answer(DELIVERY_ERROR_REPLY)
        await _resolve_prompt(query, DELIVERY_ERROR_REPLY)
        return

    await query.answer(MEMBERSHIP_RESOLVED_REPLY)
    await _resolve_prompt(query, MEMBERSHIP_RESOLVED_REPLY)
