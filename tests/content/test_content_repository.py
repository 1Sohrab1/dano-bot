import asyncio
from datetime import UTC, datetime

import pytest

from app.database.models import ContentState
from app.database.repositories import (
    ContentCodeCollisionError,
    activate_content,
    create_content,
    deactivate_content,
    get_content_by_code,
)


def test_create_content_persists_source_metadata() -> None:
    async def run() -> None:
        created = await create_content(
            source_chat_id=100,
            source_message_id=200,
            content_type="document",
            code="doccode12ab",
        )

        stored = await get_content_by_code("doccode12ab")

        assert stored is not None
        assert stored.id == created.id
        assert stored.source_chat_id == 100
        assert stored.source_message_id == 200
        assert stored.content_type == "document"
        assert stored.state == ContentState.ACTIVE
        assert stored.expires_at is None
        assert stored.created_at.tzinfo is not None

    asyncio.run(run())


def test_create_content_rejects_duplicate_codes() -> None:
    async def run() -> None:
        await create_content(
            source_chat_id=1,
            source_message_id=1,
            content_type="video",
            code="duplicate01",
        )

        with pytest.raises(ContentCodeCollisionError):
            await create_content(
                source_chat_id=2,
                source_message_id=2,
                content_type="video",
                code="duplicate01",
            )

        stored = await get_content_by_code("duplicate01")
        assert stored is not None
        assert stored.source_chat_id == 1
        assert stored.source_message_id == 1

    asyncio.run(run())


def test_activate_and_deactivate_content_by_code() -> None:
    async def run() -> None:
        await create_content(
            source_chat_id=3,
            source_message_id=4,
            content_type="photo",
            code="statetoggle1",
        )

        deactivated = await deactivate_content("statetoggle1")
        activated = await activate_content("statetoggle1")
        missing = await deactivate_content("missing-code")

        assert deactivated is not None
        assert deactivated.state == ContentState.INACTIVE
        assert activated is not None
        assert activated.state == ContentState.ACTIVE
        assert missing is None

        stored = await get_content_by_code("statetoggle1")
        assert stored is not None
        assert stored.state == ContentState.ACTIVE

    asyncio.run(run())


def test_create_content_stores_optional_expiration() -> None:
    expires_at = datetime(2027, 1, 1, tzinfo=UTC)

    async def run() -> None:
        created = await create_content(
            source_chat_id=5,
            source_message_id=6,
            content_type="audio",
            code="expirescode1",
            expires_at=expires_at,
        )

        assert created.expires_at == expires_at

    asyncio.run(run())
