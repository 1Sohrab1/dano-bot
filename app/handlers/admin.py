from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.admin_service import is_admin


router = Router()


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی ادمین ندارید.")
        return

    await message.answer("✅ شما ادمین هستید.")