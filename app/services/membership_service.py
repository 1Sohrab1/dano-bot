import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError

from app.config import settings

logger = logging.getLogger(__name__)

ELIGIBLE_STATUSES: frozenset[ChatMemberStatus] = frozenset(
    {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.MEMBER,
    }
)


def _required_channel() -> str | None:
    channel = settings.required_channel_id
    if channel is None or not channel.strip():
        return None
    return channel.strip()


async def is_member(bot: Bot, *, user_id: int) -> bool:
    channel_id = _required_channel()
    if channel_id is None:
        return True

    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
    except TelegramAPIError as error:
        logger.warning(
            "event=membership_check_failed channel=%s user_id=%s error_type=%s",
            channel_id,
            user_id,
            error.__class__.__name__,
        )
        return False

    if member.status in ELIGIBLE_STATUSES:
        return True
    if member.status == ChatMemberStatus.RESTRICTED:
        return getattr(member, "is_member", False)

    return False