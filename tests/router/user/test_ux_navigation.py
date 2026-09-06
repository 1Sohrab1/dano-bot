import asyncio
from types import SimpleNamespace

from app.middlewares.rate_limit import USER_SCOPE, RateLimitMiddleware
from app.router.user import users
from app.router.user.callbacks import UserNav, UserNavAction
from app.router.user.filters import UserCallbackQueryFilter
from app.router.user.handlers import (
    HELP_TEXT,
    INVALID_REQUEST_REPLY,
    WELCOME_TEXT,
    start_handler,
    user_navigation_callback,
)
from app.router.user.keyboards import help_keyboard, welcome_keyboard


def _make_message(from_user_id: int = 555) -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text, reply_markup=None):
        recorded["text"] = text
        recorded["reply_markup"] = reply_markup

    return (
        SimpleNamespace(from_user=SimpleNamespace(id=from_user_id), answer=answer),
        recorded,
    )


def _make_query() -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text=None):
        recorded["answer"] = text

    async def edit_text(text, reply_markup=None):
        recorded["edit_text"] = text
        recorded["edit_markup"] = reply_markup

    return (
        SimpleNamespace(
            from_user=SimpleNamespace(id=555),
            message=SimpleNamespace(edit_text=edit_text),
            answer=answer,
        ),
        recorded,
    )


def test_welcome_includes_help_keyboard() -> None:
    message, recorded = _make_message()

    asyncio.run(start_handler(message))

    assert "دانو" in recorded["text"]
    assert recorded["reply_markup"] is not None
    buttons = recorded["reply_markup"].inline_keyboard[0]
    assert buttons[0].text == "❓ راهنما"
    assert buttons[0].callback_data == UserNav(action=UserNavAction.HELP).pack()


def test_welcome_keyboard_matches_builder() -> None:
    assert welcome_keyboard().inline_keyboard[0][0].callback_data == (
        UserNav(action=UserNavAction.HELP).pack()
    )
    assert help_keyboard().inline_keyboard[0][0].callback_data == (
        UserNav(action=UserNavAction.START).pack()
    )


def test_user_nav_callback_data_round_trip() -> None:
    for action in (UserNavAction.HELP, UserNavAction.START):
        assert UserNav.unpack(UserNav(action=action).pack()).action == action


def test_help_callback_renders_help_with_back() -> None:
    query, recorded = _make_query()

    asyncio.run(
        user_navigation_callback(query, UserNav(action=UserNavAction.HELP))
    )

    assert recorded["edit_text"] == HELP_TEXT
    assert recorded["edit_markup"] is not None
    back = recorded["edit_markup"].inline_keyboard[0][0]
    assert back.callback_data == UserNav(action=UserNavAction.START).pack()
    assert "answer" in recorded


def test_start_callback_rerenders_welcome() -> None:
    query, recorded = _make_query()

    asyncio.run(
        user_navigation_callback(query, UserNav(action=UserNavAction.START))
    )

    assert recorded["edit_text"] == WELCOME_TEXT
    assert recorded["edit_markup"] is not None
    assert "answer" in recorded


def test_unknown_user_nav_action_is_rejected() -> None:
    query, recorded = _make_query()

    asyncio.run(
        user_navigation_callback(query, UserNav.model_construct(action="unknown"))
    )

    assert recorded["answer"] == INVALID_REQUEST_REPLY
    assert "edit_text" not in recorded


def test_user_callback_filter_requires_user() -> None:
    assert (
        asyncio.run(
            UserCallbackQueryFilter()(
                SimpleNamespace(from_user=SimpleNamespace(id=555))
            )
        )
        is True
    )
    assert (
        asyncio.run(UserCallbackQueryFilter()(SimpleNamespace(from_user=None)))
        is False
    )


def test_user_callback_queries_are_rate_limited() -> None:
    registered = [
        handler.callback.__name__ for handler in users.callback_query.handlers
    ]
    assert "user_navigation_callback" in registered

    scopes = [
        middleware.scope
        for middleware in users.callback_query.middleware
        if isinstance(middleware, RateLimitMiddleware)
    ]

    assert scopes == [USER_SCOPE]
