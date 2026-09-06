from weakref import WeakKeyDictionary

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.config import settings

_channel_url_cache: WeakKeyDictionary[Bot, dict[str, str | None]] = (
    WeakKeyDictionary()
)


def _public_channel_url(channel: str) -> str | None:
    if channel.startswith("@"):
        username = channel[1:].strip()
        return f"https://t.me/{username}" if username else None
    return None


async def resolve_required_channel_url(bot: Bot) -> str | None:
    configured_channel = settings.required_channel_id
    if configured_channel is None or not configured_channel.strip():
        return None

    channel = configured_channel.strip()
    public_url = _public_channel_url(channel)
    if public_url is not None:
        return public_url

    bot_cache = _channel_url_cache.setdefault(bot, {})
    if channel in bot_cache:
        return bot_cache[channel]

    try:
        chat = await bot.get_chat(chat_id=channel)
    except TelegramAPIError:
        return None

    username = getattr(chat, "username", None)
    if username:
        url = f"https://t.me/{username.lstrip('@')}"
    else:
        invite_link = getattr(chat, "invite_link", None)
        url = invite_link.strip() if invite_link and invite_link.strip() else None

    bot_cache[channel] = url
    return url