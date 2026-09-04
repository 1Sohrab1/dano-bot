from app.main import dp
from app.router.admin.router import admins
from app.router.user.router import users


def test_dispatcher_includes_separate_admin_and_user_routers() -> None:
    assert admins in dp.sub_routers
    assert users in dp.sub_routers
