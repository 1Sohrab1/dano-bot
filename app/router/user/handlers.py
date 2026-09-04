from aiogram.filters import CommandStart
from aiogram.types import Message

from app.services.identity_service import ensure_user

from .router import users


@users.message(CommandStart())
async def start_handler(message: Message) -> None:
    if message.from_user is not None:
        await ensure_user(message.from_user.id)

    await message.answer(
        "سلام 👋\n"
        "به دانو بات خوش اومدی 🤖"
    )
