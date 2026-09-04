import asyncio

from app.database.models import User
from app.database.repositories import (
    get_admin_by_telegram_id,
    get_or_create_user,
    get_user_by_telegram_id,
    is_admin,
)
from app.services.identity_service import seed_administrators


def test_get_or_create_user_is_idempotent() -> None:
    first = asyncio.run(get_or_create_user(111))
    second = asyncio.run(get_or_create_user(111))

    assert first.id is not None
    assert first.id == second.id
    assert first.telegram_id == 111


def test_user_identity_stores_only_telegram_id() -> None:
    assert set(User.model_fields) == {"id", "telegram_id"}


def test_seed_administrators_is_idempotent() -> None:
    async def seed_twice() -> None:
        await seed_administrators([222])
        await seed_administrators([222])

    asyncio.run(seed_twice())

    admin = asyncio.run(get_admin_by_telegram_id(222))
    user = asyncio.run(get_user_by_telegram_id(222))

    assert admin is not None
    assert user is not None
    assert admin.user_id == user.id
    assert asyncio.run(is_admin(222)) is True


def test_is_admin_rejects_unknown_telegram_id() -> None:
    assert asyncio.run(is_admin(987654321)) is False


def test_configured_admin_is_seeded_on_init() -> None:
    assert asyncio.run(is_admin(123456789)) is True
