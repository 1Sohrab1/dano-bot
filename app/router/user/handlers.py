from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

from app.services.access_service import (
    ContentExpiredError,
    ContentInactiveError,
    ContentNotFoundError,
    DeliveryError,
    InvalidContentCodeError,
    MembershipRequiredError,
    deliver_content,
)
from app.services.identity_service import ensure_user

from .router import users

UNSUPPORTED_CODE_REPLY = "لینک دسترسی نامعتبر است."
CONTENT_NOT_FOUND_REPLY = "محتوا یافت نشد."
CONTENT_INACTIVE_REPLY = "این محتوا در دسترس نیست."
CONTENT_EXPIRED_REPLY = "این محتوا منقضی شده است."
MEMBERSHIP_REQUIRED_REPLY = "برای دریافت این محتوا ابتدا در کانال عضو شوید."
DELIVERY_ERROR_REPLY = "دریافت محتوا با خطا مواجه شد. لطفاً بعداً تلاش کنید."


@users.message(CommandStart(deep_link=False))
async def start_handler(message: Message) -> None:
    if message.from_user is not None:
        await ensure_user(message.from_user.id)

    await message.answer(
        "سلام 👋\n"
        "به دانو بات خوش اومدی 🤖"
    )


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
        await message.answer(MEMBERSHIP_REQUIRED_REPLY)
    except DeliveryError:
        await message.answer(DELIVERY_ERROR_REPLY)
