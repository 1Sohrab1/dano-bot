import asyncio
from types import SimpleNamespace

from app.database.models import User
from app.database.repositories import (
    get_admin_by_telegram_id,
    get_or_create_user,
    get_user_by_telegram_id,
    is_admin,
    list_admin_telegram_ids,
)
from app.router.admin.filters import AdminFilter
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
    assert asyncio.run(list_admin_telegram_ids()) == [222]


def test_seed_administrators_adds_new_ids() -> None:
    asyncio.run(seed_administrators([1001]))
    asyncio.run(seed_administrators([1001, 1002]))

    assert asyncio.run(is_admin(1001)) is True
    assert asyncio.run(is_admin(1002)) is True
    assert set(asyncio.run(list_admin_telegram_ids())) == {1001, 1002}


def test_seed_administrators_removes_ids_dropped_from_config() -> None:
    asyncio.run(seed_administrators([1001, 1002]))
    asyncio.run(seed_administrators([1001]))

    assert asyncio.run(get_admin_by_telegram_id(1001)) is not None
    assert asyncio.run(get_admin_by_telegram_id(1002)) is None
    assert asyncio.run(is_admin(1002)) is False
    assert asyncio.run(list_admin_telegram_ids()) == [1001]


def test_removed_admin_is_rejected_by_authorization() -> None:
    asyncio.run(seed_administrators([1001, 1002]))
    asyncio.run(seed_administrators([1001]))

    message = SimpleNamespace(from_user=SimpleNamespace(id=1002))
    assert asyncio.run(AdminFilter()(message)) is False


def test_seed_administrators_clears_all_when_config_is_empty() -> None:
    asyncio.run(seed_administrators([1001, 1002]))
    asyncio.run(seed_administrators([]))

    assert asyncio.run(list_admin_telegram_ids()) == []
    assert asyncio.run(is_admin(1001)) is False
    assert asyncio.run(is_admin(1002)) is False


def test_is_admin_rejects_unknown_telegram_id() -> None:
    assert asyncio.run(is_admin(987654321)) is False


def test_configured_admin_is_seeded_on_init() -> None:
    assert asyncio.run(is_admin(123456789)) is True
