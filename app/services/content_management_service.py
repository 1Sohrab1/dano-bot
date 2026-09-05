import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil

from app.database.models import Content, ContentState
from app.database.repositories import (
    activate_content as repository_activate_content,
)
from app.database.repositories import (
    count_content,
    get_content_by_code,
    update_content_expiration,
)
from app.database.repositories import (
    deactivate_content as repository_deactivate_content,
)
from app.database.repositories import (
    delete_content as repository_delete_content,
)
from app.database.repositories import (
    list_content as repository_list_content,
)
from app.services.content_service import is_deep_link_safe_code

logger = logging.getLogger(__name__)

CONTENT_PAGE_SIZE = 10
MIN_EXPIRATION_DAYS = 1


class InvalidContentCodeError(Exception):
    pass


class ContentNotFoundError(Exception):
    pass


class ContentAlreadyActiveError(Exception):
    pass


class ContentAlreadyInactiveError(Exception):
    pass


class InvalidExpirationValueError(Exception):
    pass


@dataclass(frozen=True)
class ContentPage:
    items: list[Content]
    page: int
    page_size: int
    total: int
    total_pages: int


async def _resolve_content(code: str) -> Content:
    if not is_deep_link_safe_code(code):
        raise InvalidContentCodeError(code)

    content = await get_content_by_code(code)
    if content is None:
        raise ContentNotFoundError(code)

    return content


async def list_content(page: int, page_size: int = CONTENT_PAGE_SIZE) -> ContentPage:
    total = await count_content()
    total_pages = max(1, ceil(total / page_size)) if total > 0 else 1
    effective_page = max(1, min(page, total_pages))
    offset = (effective_page - 1) * page_size

    items = await repository_list_content(offset, page_size)

    return ContentPage(
        items=items,
        page=effective_page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


async def preview_content(code: str) -> Content:
    return await _resolve_content(code)


async def activate_content(code: str, *, actor: int) -> Content:
    content = await _resolve_content(code)
    if content.state == ContentState.ACTIVE:
        raise ContentAlreadyActiveError(code)

    updated = await repository_activate_content(code)
    if updated is None:
        raise ContentNotFoundError(code)

    logger.info(
        "event=content_activated actor=%s code=%s content_id=%s",
        actor,
        code,
        updated.id,
    )
    return updated


async def deactivate_content(code: str, *, actor: int) -> Content:
    content = await _resolve_content(code)
    if content.state == ContentState.INACTIVE:
        raise ContentAlreadyInactiveError(code)

    updated = await repository_deactivate_content(code)
    if updated is None:
        raise ContentNotFoundError(code)

    logger.info(
        "event=content_deactivated actor=%s code=%s content_id=%s",
        actor,
        code,
        updated.id,
    )
    return updated


async def delete_content(code: str, *, actor: int) -> Content:
    if not is_deep_link_safe_code(code):
        raise InvalidContentCodeError(code)

    content = await repository_delete_content(code)
    if content is None:
        raise ContentNotFoundError(code)

    logger.info(
        "event=content_deleted actor=%s code=%s content_id=%s",
        actor,
        code,
        content.id,
    )
    return content


async def set_content_expiration(
    code: str,
    days: int | None,
    *,
    actor: int,
) -> Content:
    await _resolve_content(code)

    expires_at = None
    if days is not None:
        if days < MIN_EXPIRATION_DAYS:
            raise InvalidExpirationValueError(days)
        expires_at = datetime.now(UTC) + timedelta(days=days)

    updated = await update_content_expiration(code, expires_at)
    if updated is None:
        raise ContentNotFoundError(code)

    logger.info(
        "event=content_expiration_set actor=%s code=%s content_id=%s days=%s expires_at=%s",
        actor,
        code,
        updated.id,
        "none" if days is None else days,
        updated.expires_at.isoformat() if updated.expires_at is not None else "none",
    )
    return updated