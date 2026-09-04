import asyncio
from unittest.mock import AsyncMock

import pytest

from app.database.models import ContentState
from app.database.repositories import create_content, get_content_by_code
from app.services import content_service
from app.services.content_service import (
    ContentCodeAllocationError,
    UnsupportedContentError,
    build_content_deep_link,
    create_content_upload,
)


def test_create_content_upload_persists_supported_content() -> None:
    async def run() -> None:
        result = await create_content_upload(
            source_chat_id=10,
            source_message_id=20,
            content_type="document",
            bot_username="dano_bot",
        )
        stored = await get_content_by_code(result.code)

        assert stored is not None
        assert stored.source_chat_id == 10
        assert stored.source_message_id == 20
        assert stored.content_type == "document"
        assert stored.state == ContentState.ACTIVE
        assert result.deep_link == f"https://t.me/dano_bot?start={result.code}"

    asyncio.run(run())


def test_create_content_upload_rejects_unsupported_type() -> None:
    async def run() -> None:
        with pytest.raises(UnsupportedContentError):
            await create_content_upload(
                source_chat_id=10,
                source_message_id=20,
                content_type="sticker",
            )

        assert await get_content_by_code("unusedcode01") is None

    asyncio.run(run())


def test_create_content_upload_retries_code_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    codes = iter(["taken_code01", "taken_code01", "fresh_code01"])
    monkeypatch.setattr(content_service, "generate_content_code", lambda: next(codes))

    async def run() -> None:
        await create_content(
            source_chat_id=1,
            source_message_id=1,
            content_type="video",
            code="taken_code01",
        )

        result = await create_content_upload(
            source_chat_id=99,
            source_message_id=100,
            content_type="video",
        )
        stored = await get_content_by_code("fresh_code01")
        original = await get_content_by_code("taken_code01")

        assert result.code == "fresh_code01"
        assert stored is not None
        assert stored.source_chat_id == 99
        assert stored.source_message_id == 100
        assert original is not None
        assert original.source_chat_id == 1

    asyncio.run(run())


def test_create_content_upload_raises_when_codes_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        content_service,
        "generate_content_code",
        lambda: "stuck_code01",
    )

    async def run() -> None:
        await create_content(
            source_chat_id=1,
            source_message_id=1,
            content_type="voice",
            code="stuck_code01",
        )

        with pytest.raises(ContentCodeAllocationError):
            await create_content_upload(
                source_chat_id=2,
                source_message_id=2,
                content_type="voice",
            )

        stored = await get_content_by_code("stuck_code01")
        assert stored is not None
        assert stored.source_chat_id == 1

    asyncio.run(run())


def test_build_content_deep_link_without_username() -> None:
    assert build_content_deep_link("abc123") == "/start abc123"


def test_unsupported_content_does_not_call_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    create_mock = AsyncMock()
    monkeypatch.setattr(content_service, "create_content", create_mock)

    async def run() -> None:
        with pytest.raises(UnsupportedContentError):
            await create_content_upload(
                source_chat_id=1,
                source_message_id=1,
                content_type="text",
            )

    asyncio.run(run())
    create_mock.assert_not_called()
