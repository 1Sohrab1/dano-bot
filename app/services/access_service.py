import logging
from datetime import UTC, datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.database.models import ContentState
from app.database.repositories import get_content_by_code
from app.services.content_service import is_deep_link_safe_code
from app.services.membership_service import is_member

logger = logging.getLogger(__name__)


class InvalidContentCodeError(Exception):
    pass


class ContentNotFoundError(Exception):
    pass


class ContentInactiveError(Exception):
    pass


class ContentExpiredError(Exception):
    pass


class MembershipRequiredError(Exception):
    pass


class DeliveryError(Exception):
    pass


async def deliver_content(bot: Bot, *, code: str, user_id: int) -> None:
    if not is_deep_link_safe_code(code):
        logger.info(
            "event=access_denied reason=malformed user_id=%s code=%s",
            user_id,
            code,
        )
        raise InvalidContentCodeError(code)

    content = await get_content_by_code(code)
    if content is None:
        logger.info(
            "event=access_denied reason=not_found user_id=%s code=%s",
            user_id,
            code,
        )
        raise ContentNotFoundError(code)

    if content.state != ContentState.ACTIVE:
        logger.info(
            "event=access_denied reason=inactive user_id=%s code=%s content_id=%s",
            user_id,
            code,
            content.id,
        )
        raise ContentInactiveError(code)

    if content.expires_at is not None and datetime.now(UTC) > content.expires_at:
        logger.info(
            "event=access_denied reason=expired user_id=%s code=%s content_id=%s",
            user_id,
            code,
            content.id,
        )
        raise ContentExpiredError(code)

    if not await is_member(bot, user_id=user_id):
        logger.info(
            "event=access_denied reason=not_member user_id=%s code=%s content_id=%s",
            user_id,
            code,
            content.id,
        )
        raise MembershipRequiredError(code)

    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=content.source_chat_id,
            message_id=content.source_message_id,
        )
    except TelegramAPIError as error:
        logger.warning(
            "event=delivery_failed user_id=%s code=%s content_id=%s error_type=%s",
            user_id,
            code,
            content.id,
            error.__class__.__name__,
        )
        raise DeliveryError(code) from error

    logger.info(
        "event=delivery_success user_id=%s code=%s content_id=%s",
        user_id,
        code,
        content.id,
    )