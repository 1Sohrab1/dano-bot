import asyncio
from types import SimpleNamespace

from app.main import dp
from app.router.admin.filters import AdminFilter
from app.router.admin.router import admins
from app.router.user.router import users


def test_dispatcher_includes_separate_admin_and_user_routers() -> None:
    assert admins in dp.sub_routers
    assert users in dp.sub_routers


def test_admin_filter_accepts_configured_admin() -> None:
    message = SimpleNamespace(from_user=SimpleNamespace(id=123456789))

    assert asyncio.run(AdminFilter()(message)) is True


def test_admin_filter_rejects_unknown_user() -> None:
    message = SimpleNamespace(from_user=SimpleNamespace(id=987654321))

    assert asyncio.run(AdminFilter()(message)) is False
