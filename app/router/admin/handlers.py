from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message

from app.services.content_service import (
    SUPPORTED_CONTENT_TYPES,
    UnsupportedContentError,
    create_content_upload,
)

from .dashboard.handlers import DASHBOARD_TEXT
from .keyboards import dashboard_keyboard
from .router import admins

UNSUPPORTED_CONTENT_REPLY = "این نوع پیام پشتیبانی نمی‌شود."


@admins.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    await message.answer(DASHBOARD_TEXT, reply_markup=dashboard_keyboard())


@admins.message(F.content_type.in_(SUPPORTED_CONTENT_TYPES))
async def content_upload_handler(message: Message) -> None:
    me = await message.bot.me()
    bot_username = me.username

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
