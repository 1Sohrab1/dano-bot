from aiogram.filters import Command
from aiogram.types import Message

from .router import admins


@admins.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    await message.answer("✅ شما ادمین هستید.")
