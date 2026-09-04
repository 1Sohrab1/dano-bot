import asyncio
from types import SimpleNamespace

from app.database.repositories import get_user_by_telegram_id
from app.router.admin.filters import AdminFilter
from app.router.user.handlers import start_handler


def test_admin_filter_accepts_seeded_admin() -> None:
    message = SimpleNamespace(from_user=SimpleNamespace(id=123456789))

    assert asyncio.run(AdminFilter()(message)) is True


def test_admin_filter_rejects_unknown_user() -> None:
    message = SimpleNamespace(from_user=SimpleNamespace(id=987654321))

    assert asyncio.run(AdminFilter()(message)) is False


def test_admin_filter_rejects_missing_user() -> None:
    message = SimpleNamespace(from_user=None)

    assert asyncio.run(AdminFilter()(message)) is False


def test_start_handler_persists_user() -> None:
    async def run() -> None:
        recorded: dict[str, str] = {}

        async def answer(text: str) -> None:
            recorded["text"] = text

        message = SimpleNamespace(
            from_user=SimpleNamespace(id=555),
            answer=answer,
        )
        await start_handler(message)

        user = await get_user_by_telegram_id(555)
        assert user is not None
        assert user.telegram_id == 555
        assert "دانو" in recorded["text"]

    asyncio.run(run())
