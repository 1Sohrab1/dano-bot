import asyncio
import logging

from aiogram import Bot, Dispatcher

from app import logging as app_logging
from app.config import settings
from app.database.database import init_db
from app.router.admin import admins
from app.router.user import users
from app.services.health_service import (
    ApplicationStatus,
    application_status,
    check_database,
)

logger = logging.getLogger(__name__)

dp = Dispatcher()

dp.include_router(admins)
dp.include_router(users)


async def startup(status: ApplicationStatus = application_status) -> None:
    """Run startup initialization and mark the application ready.

    Raises on any failure so the application never starts in a broken
    state silently.
    """
    app_logging.configure_logging(settings.log_level)
    logger.info("event=application_starting")

    try:
        logger.info("event=database_initialization_starting")
        await init_db()
        logger.info("event=database_initialization_completed")

        if not await check_database():
            raise RuntimeError("startup database health check failed")

        status.mark_ready()
        logger.info("event=application_ready")
    except Exception:
        status.mark_failed()
        logger.exception("event=startup_failed")
        raise


async def main() -> None:
    await startup()

    bot = Bot(token=settings.bot_token)

    try:
        await bot.get_me()
        await dp.start_polling(bot)
    except Exception:
        logger.exception("event=unhandled_error")
        raise
    finally:
        await bot.session.close()
        logger.info("event=application_shutdown")


if __name__ == "__main__":
    asyncio.run(main())
