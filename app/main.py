import asyncio

from aiogram import Bot, Dispatcher

from app.config import settings
from app.database.database import init_db
from app.router.admin import admins
from app.router.user import users

dp = Dispatcher()

dp.include_router(admins)
dp.include_router(users)


async def main() -> None:
    await init_db()

    bot = Bot(token=settings.bot_token)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
