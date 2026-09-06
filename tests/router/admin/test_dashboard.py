import asyncio
from types import SimpleNamespace

from app.middlewares.rate_limit import ADMIN_SCOPE, RateLimitMiddleware
from app.router.admin import admins
from app.router.admin.callbacks import AdminNav, AdminNavAction
from app.router.admin.dashboard import dashboard_admin
from app.router.admin.dashboard.handlers import (
    ADMIN_HELP_TEXT,
    DASHBOARD_TEXT,
    INVALID_REQUEST_REPLY,
    MANAGE_HINT_TEXT,
    UPLOAD_PROMPT_TEXT,
    admin_navigation_callback,
)
from app.router.admin.filters import AdminCallbackQueryFilter
from app.router.admin.handlers import admin_handler
from app.router.admin.keyboards import back_keyboard, dashboard_keyboard


def _make_message() -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text, reply_markup=None):
        recorded["text"] = text
        recorded["reply_markup"] = reply_markup

    return (SimpleNamespace(answer=answer), recorded)


def _make_query() -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text=None):
        recorded["answer"] = text

    async def edit_text(text, reply_markup=None):
        recorded["edit_text"] = text
        recorded["edit_markup"] = reply_markup

    return (
        SimpleNamespace(
            from_user=SimpleNamespace(id=123456789),
            message=SimpleNamespace(edit_text=edit_text),
            answer=answer,
        ),
        recorded,
    )


def test_admin_dashboard_exposes_supported_actions() -> None:
    message, recorded = _make_message()

    asyncio.run(admin_handler(message))

    assert "پنل مدیریت" in recorded["text"]
    assert recorded["reply_markup"] is not None
    rows = recorded["reply_markup"].inline_keyboard
    assert [row[0].text for row in rows] == [
        "📤 افزودن محتوا",
        "📚 مدیریت محتوا",
        "❓ راهنما",
    ]
    assert [row[0].callback_data for row in rows] == [
        AdminNav(action=AdminNavAction.UPLOAD).pack(),
        AdminNav(action=AdminNavAction.MANAGE).pack(),
        AdminNav(action=AdminNavAction.HELP).pack(),
    ]


def test_dashboard_keyboard_matches_builder() -> None:
    assert dashboard_keyboard().inline_keyboard[0][0].callback_data == (
        AdminNav(action=AdminNavAction.UPLOAD).pack()
    )
    assert back_keyboard().inline_keyboard[0][0].callback_data == (
        AdminNav(action=AdminNavAction.DASHBOARD).pack()
    )


def test_admin_nav_callback_data_round_trip() -> None:
    for action in (
        AdminNavAction.DASHBOARD,
        AdminNavAction.UPLOAD,
        AdminNavAction.MANAGE,
        AdminNavAction.HELP,
    ):
        assert AdminNav.unpack(AdminNav(action=action).pack()).action == action


def test_dashboard_callback_rerenders_dashboard() -> None:
    query, recorded = _make_query()

    asyncio.run(
        admin_navigation_callback(query, AdminNav(action=AdminNavAction.DASHBOARD))
    )

    assert recorded["edit_text"] == DASHBOARD_TEXT
    assert recorded["edit_markup"] is not None
    assert "answer" in recorded


def test_upload_callback_guides_into_upload_workflow() -> None:
    query, recorded = _make_query()

    asyncio.run(
        admin_navigation_callback(query, AdminNav(action=AdminNavAction.UPLOAD))
    )

    assert "ارسال کنید" in recorded["edit_text"]
    assert recorded["edit_text"] == UPLOAD_PROMPT_TEXT
    back = recorded["edit_markup"].inline_keyboard[0][0]
    assert back.text == "← بازگشت به پنل"
    assert "answer" in recorded


def test_manage_callback_points_to_existing_workflow() -> None:
    query, recorded = _make_query()

    asyncio.run(
        admin_navigation_callback(query, AdminNav(action=AdminNavAction.MANAGE))
    )

    assert "/list" in recorded["edit_text"]
    assert recorded["edit_text"] == MANAGE_HINT_TEXT
    assert recorded["edit_markup"] is not None
    assert "answer" in recorded


def test_help_callback_renders_admin_help() -> None:
    query, recorded = _make_query()

    asyncio.run(
        admin_navigation_callback(query, AdminNav(action=AdminNavAction.HELP))
    )

    assert recorded["edit_text"] == ADMIN_HELP_TEXT
    assert recorded["edit_markup"] is not None
    assert "answer" in recorded


def test_unknown_admin_nav_action_is_rejected() -> None:
    query, recorded = _make_query()

    asyncio.run(
        admin_navigation_callback(
            query, AdminNav.model_construct(action="unknown")
        )
    )

    assert recorded["answer"] == INVALID_REQUEST_REPLY
    assert "edit_text" not in recorded


def test_navigation_callback_without_message_still_answers() -> None:
    recorded: dict = {}

    async def answer(text=None):
        recorded["answer"] = text

    query = SimpleNamespace(
        from_user=SimpleNamespace(id=123456789), message=None, answer=answer
    )

    asyncio.run(
        admin_navigation_callback(query, AdminNav(action=AdminNavAction.HELP))
    )

    assert "answer" in recorded


def test_non_admin_callback_is_rejected_by_filter() -> None:
    query = SimpleNamespace(from_user=SimpleNamespace(id=987654321))

    assert asyncio.run(AdminCallbackQueryFilter()(query)) is False


def test_admin_callback_queries_have_authorization_and_rate_limit() -> None:
    registered = [
        handler.callback.__name__
        for handler in dashboard_admin.callback_query.handlers
    ]
    assert "admin_navigation_callback" in registered

    assert (
        asyncio.run(
            AdminCallbackQueryFilter()(
                SimpleNamespace(from_user=SimpleNamespace(id=123456789))
            )
        )
        is True
    )

    dashboard_scopes = [
        middleware.scope
        for middleware in dashboard_admin.callback_query.middleware
        if isinstance(middleware, RateLimitMiddleware)
    ]
    assert dashboard_scopes == [ADMIN_SCOPE]

    # The parent admins.callback_query observer must not register its own
    # copy: aiogram resolves parent router middlewares into the child
    # chain, so a parent copy would double-count content callbacks.
    parent_scopes = [
        middleware.scope
        for middleware in admins.callback_query.middleware
        if isinstance(middleware, RateLimitMiddleware)
    ]
    assert parent_scopes == []
    assert dashboard_admin in admins.sub_routers
