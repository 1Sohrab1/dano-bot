import asyncio
from types import SimpleNamespace

from app.database.repositories import get_content_by_code
from app.router.admin.filters import AdminFilter
from app.router.admin.handlers import (
    UNSUPPORTED_CONTENT_REPLY,
    admin_handler,
    content_upload_handler,
    unsupported_content_handler,
)
from app.router.user.handlers import start_handler


def test_content_upload_handler_persists_supported_document() -> None:
    async def run() -> None:
        recorded: dict[str, str] = {}

        async def answer(text: str) -> None:
            recorded["text"] = text

        async def me() -> SimpleNamespace:
            return SimpleNamespace(username="dano_bot")

        message = SimpleNamespace(
            content_type="document",
            chat=SimpleNamespace(id=111),
            message_id=222,
            bot=SimpleNamespace(me=me),
            answer=answer,
        )

        await content_upload_handler(message)

        assert "محتوا با موفقیت ذخیره شد" in recorded["text"]
        assert "https://t.me/dano_bot?start=" in recorded["text"]

        code = recorded["text"].rsplit("start=", 1)[1]
        stored = await get_content_by_code(code)
        assert stored is not None
        assert stored.source_chat_id == 111
        assert stored.source_message_id == 222
        assert stored.content_type == "document"

    asyncio.run(run())


def test_unsupported_content_handler_does_not_persist() -> None:
    async def run() -> None:
        recorded: dict[str, str] = {}

        async def answer(text: str) -> None:
            recorded["text"] = text

        message = SimpleNamespace(
            content_type="sticker",
            chat=SimpleNamespace(id=111),
            message_id=333,
            answer=answer,
        )

        await unsupported_content_handler(message)

        assert recorded["text"] == UNSUPPORTED_CONTENT_REPLY
        assert await get_content_by_code("sticker333") is None

    asyncio.run(run())


def test_admin_command_still_responds() -> None:
    async def run() -> None:
        recorded: dict = {}

        async def answer(text: str, reply_markup=None) -> None:
            recorded["text"] = text
            recorded["reply_markup"] = reply_markup

        await admin_handler(SimpleNamespace(answer=answer))
        assert "پنل مدیریت" in recorded["text"]
        assert recorded["reply_markup"] is not None

    asyncio.run(run())


def test_non_admin_cannot_pass_admin_filter() -> None:
    message = SimpleNamespace(from_user=SimpleNamespace(id=987654321))
    assert asyncio.run(AdminFilter()(message)) is False


def test_start_handler_does_not_create_content() -> None:
    async def run() -> None:
        recorded: dict = {}

        async def answer(text: str, reply_markup=None) -> None:
            recorded["text"] = text
            recorded["reply_markup"] = reply_markup

        message = SimpleNamespace(
            from_user=SimpleNamespace(id=555),
            answer=answer,
        )
        await start_handler(message)
        assert "دانو" in recorded["text"]
        assert await get_content_by_code("555") is None

    asyncio.run(run())
