import re
import secrets
import string
from dataclasses import dataclass

from aiogram.enums import ContentType

from app.database.repositories import (
    ContentCodeCollisionError,
    create_content,
)

SUPPORTED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        ContentType.ANIMATION,
        ContentType.AUDIO,
        ContentType.DOCUMENT,
        ContentType.PHOTO,
        ContentType.VIDEO,
        ContentType.VIDEO_NOTE,
        ContentType.VOICE,
    }
)

CODE_ALPHABET = string.ascii_letters + string.digits + "_-"
CODE_LENGTH = 12
MAX_CODE_ALLOCATION_ATTEMPTS = 8
DEEP_LINK_CODE_PATTERN = re.compile(rf"^[{re.escape(CODE_ALPHABET)}]{{1,64}}$")


class UnsupportedContentError(Exception):
    pass


class ContentCodeAllocationError(Exception):
    pass


@dataclass(frozen=True)
class ContentLink:
    code: str
    deep_link: str


def generate_content_code(length: int = CODE_LENGTH) -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))


def is_deep_link_safe_code(code: str) -> bool:
    return DEEP_LINK_CODE_PATTERN.fullmatch(code) is not None


def build_content_deep_link(code: str, bot_username: str | None = None) -> str:
    if bot_username:
        return f"https://t.me/{bot_username}?start={code}"
    return f"/start {code}"


async def create_content_upload(
    *,
    source_chat_id: int,
    source_message_id: int,
    content_type: str,
    bot_username: str | None = None,
) -> ContentLink:
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise UnsupportedContentError(content_type)

    for _ in range(MAX_CODE_ALLOCATION_ATTEMPTS):
        code = generate_content_code()
        try:
            content = await create_content(
                source_chat_id=source_chat_id,
                source_message_id=source_message_id,
                content_type=content_type,
                code=code,
            )
        except ContentCodeCollisionError:
            continue

        return ContentLink(
            code=content.code,
            deep_link=build_content_deep_link(content.code, bot_username),
        )

    raise ContentCodeAllocationError(
        "could not allocate a unique content code"
    )