from aiogram.filters import CommandStart
from aiogram.types import Message

from .router import users


@users.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "سلام 👋\n"
        "به دانو بات خوش اومدی 🤖"
    )
