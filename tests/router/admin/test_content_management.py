import asyncio
import inspect
import logging
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.database.models import ContentState
from app.database.repositories import create_content, get_content_by_code
from app.router.admin import admins
from app.router.admin.content import handlers as content_handlers
from app.router.admin.content.handlers import (
    ALREADY_ACTIVE_REPLY,
    ALREADY_INACTIVE_REPLY,
    CONTENT_NOT_FOUND_REPLY,
    INVALID_CODE_REPLY,
    INVALID_EXPIRATION_REPLY,
    INVALID_PAGE_REPLY,
    INVALID_REQUEST_REPLY,
    activate_command_handler,
    content_action_callback,
    deactivate_command_handler,
    delete_command_handler,
    expire_command_handler,
    list_handler,
)
from app.router.admin.content.router import content_admin
from app.router.admin.filters import AdminCallbackQueryFilter, AdminFilter


def _seed(
    code: str,
    *,
    state: str = ContentState.ACTIVE,
    expires_at: datetime | None = None,
) -> None:
    asyncio.run(
        create_content(
            source_chat_id=123,
            source_message_id=456,
            content_type="document",
            code=code,
            state=state,
            expires_at=expires_at,
        )
    )


def _make_message(from_user_id: int = 123456789) -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text, reply_markup=None):
        recorded["text"] = text
        recorded["reply_markup"] = reply_markup

    return (
        SimpleNamespace(from_user=SimpleNamespace(id=from_user_id), answer=answer),
        recorded,
    )


def _make_query(data: str, from_user_id: int = 123456789) -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text=None, show_alert: bool = False):
        recorded["answer"] = text
        recorded["show_alert"] = show_alert

    async def edit_text(text, reply_markup=None):
        recorded["edit_text"] = text
        recorded["edit_markup"] = reply_markup

    return (
        SimpleNamespace(
            data=data,
            from_user=SimpleNamespace(id=from_user_id),
            message=SimpleNamespace(edit_text=edit_text),
            answer=answer,
        ),
        recorded,
    )


def test_content_admin_subrouter_included_in_admins() -> None:
    assert content_admin in admins.sub_routers


def test_admin_callback_filter_accepts_seeded_admin() -> None:
    query = SimpleNamespace(from_user=SimpleNamespace(id=123456789))

    assert asyncio.run(AdminCallbackQueryFilter()(query)) is True


def test_admin_callback_filter_rejects_unknown_user() -> None:
    query = SimpleNamespace(from_user=SimpleNamespace(id=987654321))

    assert asyncio.run(AdminCallbackQueryFilter()(query)) is False


def test_admin_callback_filter_rejects_missing_user() -> None:
    query = SimpleNamespace(from_user=None)

    assert asyncio.run(AdminCallbackQueryFilter()(query)) is False


def test_admin_message_filter_accepts_seeded_admin() -> None:
    message = SimpleNamespace(from_user=SimpleNamespace(id=123456789))

    assert asyncio.run(AdminFilter()(message)) is True


def test_content_handlers_do_not_import_repositories() -> None:
    source = inspect.getsource(content_handlers)

    assert "repositories" not in source
    assert "create_content" not in source
    assert "select(" not in source


def test_list_handler_answers_bounded_page() -> None:
    for i in range(12):
        _seed(f"listcode{i:02d}")
    message, recorded = _make_message()

    asyncio.run(list_handler(message, SimpleNamespace(args=None)))

    assert "صفحه 1 از 2" in recorded["text"]
    assert recorded["reply_markup"] is not None


def test_list_handler_rejects_invalid_page() -> None:
    message, recorded = _make_message()

    asyncio.run(list_handler(message, SimpleNamespace(args="abc")))

    assert recorded["text"] == INVALID_PAGE_REPLY


def test_activate_command_requires_confirmation_before_mutation() -> None:
    _seed("confirmact1", state=ContentState.INACTIVE)
    message, recorded = _make_message()

    asyncio.run(activate_command_handler(message, SimpleNamespace(args="confirmact1")))

    assert recorded["reply_markup"] is not None
    stored = asyncio.run(get_content_by_code("confirmact1"))
    assert stored is not None
    assert stored.state == ContentState.INACTIVE


def test_deactivate_command_requires_confirmation_before_mutation() -> None:
    _seed("confirmde1", state=ContentState.ACTIVE)
    message, recorded = _make_message()

    asyncio.run(deactivate_command_handler(message, SimpleNamespace(args="confirmde1")))

    assert recorded["reply_markup"] is not None
    stored = asyncio.run(get_content_by_code("confirmde1"))
    assert stored is not None
    assert stored.state == ContentState.ACTIVE


def test_delete_command_warns_and_requires_confirmation() -> None:
    _seed("confirmdel1")
    message, recorded = _make_message()

    asyncio.run(delete_command_handler(message, SimpleNamespace(args="confirmdel1")))

    assert recorded["reply_markup"] is not None
    assert "غیرقابل بازگشت" in recorded["text"]
    assert asyncio.run(get_content_by_code("confirmdel1")) is not None


def test_activate_command_short_circuits_already_active() -> None:
    _seed("confirmact2")
    message, recorded = _make_message()

    asyncio.run(activate_command_handler(message, SimpleNamespace(args="confirmact2")))

    assert recorded["text"] == ALREADY_ACTIVE_REPLY
    assert recorded["reply_markup"] is None


def test_deactivate_command_short_circuits_already_inactive() -> None:
    _seed("confirmde2", state=ContentState.INACTIVE)
    message, recorded = _make_message()

    asyncio.run(deactivate_command_handler(message, SimpleNamespace(args="confirmde2")))

    assert recorded["text"] == ALREADY_INACTIVE_REPLY
    assert recorded["reply_markup"] is None


def test_activate_command_rejects_unknown_code() -> None:
    message, recorded = _make_message()

    asyncio.run(activate_command_handler(message, SimpleNamespace(args="nonexist01")))

    assert recorded["text"] == CONTENT_NOT_FOUND_REPLY


def test_activate_confirm_callback_activates_content() -> None:
    _seed("cbact0001", state=ContentState.INACTIVE)
    query, recorded = _make_query("content:activate:cbact0001")

    asyncio.run(content_action_callback(query))

    stored = asyncio.run(get_content_by_code("cbact0001"))
    assert stored is not None
    assert stored.state == ContentState.ACTIVE
    assert "فعال شد" in recorded["answer"]


def test_deactivate_confirm_callback_deactivates_content() -> None:
    _seed("cbdeact01")
    query, recorded = _make_query("content:deactivate:cbdeact01")

    asyncio.run(content_action_callback(query))

    stored = asyncio.run(get_content_by_code("cbdeact01"))
    assert stored is not None
    assert stored.state == ContentState.INACTIVE
    assert "غیرفعال شد" in recorded["answer"]


def test_delete_confirm_callback_deletes_content() -> None:
    _seed("cbdel0001")
    query, recorded = _make_query("content:delete:cbdel0001")

    asyncio.run(content_action_callback(query))

    assert asyncio.run(get_content_by_code("cbdel0001")) is None
    assert "حذف شد" in recorded["answer"]


def test_cancel_callback_leaves_active_content_unchanged() -> None:
    _seed("cbcancel01")
    query, _ = _make_query("content:cancel:cbcancel01")

    asyncio.run(content_action_callback(query))

    stored = asyncio.run(get_content_by_code("cbcancel01"))
    assert stored is not None
    assert stored.state == ContentState.ACTIVE


def test_cancel_callback_leaves_inactive_content_unchanged() -> None:
    _seed("cbcancel02", state=ContentState.INACTIVE)
    query, _ = _make_query("content:cancel:cbcancel02")

    asyncio.run(content_action_callback(query))

    stored = asyncio.run(get_content_by_code("cbcancel02"))
    assert stored is not None
    assert stored.state == ContentState.INACTIVE


def test_confirm_callback_revalidates_missing_content() -> None:
    query, recorded = _make_query("content:activate:nonexist01")

    asyncio.run(content_action_callback(query))

    assert recorded["answer"] == CONTENT_NOT_FOUND_REPLY


def test_confirm_delete_callback_on_missing_content_is_safe() -> None:
    query, recorded = _make_query("content:delete:nonexist01")

    asyncio.run(content_action_callback(query))

    assert recorded["answer"] == CONTENT_NOT_FOUND_REPLY


def test_confirm_callback_revalidates_already_active() -> None:
    _seed("alreadyact1")
    query, recorded = _make_query("content:activate:alreadyact1")

    asyncio.run(content_action_callback(query))

    assert recorded["answer"] == ALREADY_ACTIVE_REPLY


def test_confirm_callback_revalidates_already_inactive() -> None:
    _seed("alreadyinac", state=ContentState.INACTIVE)
    query, recorded = _make_query("content:deactivate:alreadyinac")

    asyncio.run(content_action_callback(query))

    assert recorded["answer"] == ALREADY_INACTIVE_REPLY


def test_callback_rejects_malformed_data() -> None:
    query, recorded = _make_query("garbage")

    asyncio.run(content_action_callback(query))

    assert recorded["answer"] == INVALID_REQUEST_REPLY


def test_callback_rejects_unknown_action() -> None:
    query, recorded = _make_query("content:unknown:code")

    asyncio.run(content_action_callback(query))

    assert recorded["answer"] == INVALID_REQUEST_REPLY


def test_list_callback_renders_next_page() -> None:
    for i in range(15):
        _seed(f"pgcode{i:02d}")
    query, recorded = _make_query("content:list:2")

    asyncio.run(content_action_callback(query))

    assert "صفحه 2 از 2" in recorded["edit_text"]


def test_list_callback_rejects_invalid_page() -> None:
    query, recorded = _make_query("content:list:abc")

    asyncio.run(content_action_callback(query))

    assert recorded["answer"] == INVALID_PAGE_REPLY


def test_expire_command_sets_relative_expiration() -> None:
    _seed("expset0001")
    message, recorded = _make_message()

    asyncio.run(expire_command_handler(message, SimpleNamespace(args="expset0001 7")))

    stored = asyncio.run(get_content_by_code("expset0001"))
    assert stored is not None
    assert stored.expires_at is not None
    assert abs((stored.expires_at - (datetime.now(UTC) + timedelta(days=7))).total_seconds()) < 30
    assert "تنظیم شد" in recorded["text"]


def test_expire_command_clears_expiration() -> None:
    _seed("expclear01", expires_at=datetime(2030, 1, 1, tzinfo=UTC))
    message, recorded = _make_message()

    asyncio.run(expire_command_handler(message, SimpleNamespace(args="expclear01 off")))

    stored = asyncio.run(get_content_by_code("expclear01"))
    assert stored is not None
    assert stored.expires_at is None
    assert "حذف شد" in recorded["text"]


def test_expire_command_rejects_invalid_value() -> None:
    _seed("expinvalid1")
    message, recorded = _make_message()

    asyncio.run(expire_command_handler(message, SimpleNamespace(args="expinvalid1 abc")))

    assert recorded["text"] == INVALID_EXPIRATION_REPLY


def test_expire_command_rejects_missing_args() -> None:
    message, recorded = _make_message()

    asyncio.run(expire_command_handler(message, SimpleNamespace(args=None)))

    assert recorded["text"] == INVALID_EXPIRATION_REPLY


def test_expire_command_rejects_invalid_code() -> None:
    message, recorded = _make_message()

    asyncio.run(expire_command_handler(message, SimpleNamespace(args="کد 5")))

    assert recorded["text"] == INVALID_CODE_REPLY


def test_expire_command_rejects_unknown_code() -> None:
    message, recorded = _make_message()

    asyncio.run(expire_command_handler(message, SimpleNamespace(args="nonexist01 5")))

    assert recorded["text"] == CONTENT_NOT_FOUND_REPLY


def test_confirm_callback_logs_structured_event(caplog: pytest.LogCaptureFixture) -> None:
    _seed("dellog001")
    query, _ = _make_query("content:delete:dellog001")

    with caplog.at_level(logging.INFO):
        asyncio.run(content_action_callback(query))

    assert "event=content_deleted actor=123456789 code=dellog001" in caplog.text


def test_list_handler_delegates_to_service(monkeypatch) -> None:
    mock_list = AsyncMock(
        return_value=SimpleNamespace(items=[], page=1, page_size=10, total=0, total_pages=1)
    )
    monkeypatch.setattr(content_handlers.content_management_service, "list_content", mock_list)
    message, _ = _make_message()

    asyncio.run(list_handler(message, SimpleNamespace(args="1")))

    mock_list.assert_awaited_once_with(1)


def test_activate_command_delegates_preview_to_service(monkeypatch) -> None:
    mock_preview = AsyncMock(
        return_value=SimpleNamespace(
            code="code12345", content_type="document", state=ContentState.INACTIVE
        )
    )
    monkeypatch.setattr(
        content_handlers.content_management_service, "preview_content", mock_preview
    )
    message, recorded = _make_message()

    asyncio.run(activate_command_handler(message, SimpleNamespace(args="code12345")))

    mock_preview.assert_awaited_once_with("code12345")
    assert recorded["reply_markup"] is not None


def test_expire_command_delegates_to_service(monkeypatch) -> None:
    mock_expire = AsyncMock(return_value=SimpleNamespace(expires_at=datetime(2030, 1, 1, tzinfo=UTC)))
    monkeypatch.setattr(
        content_handlers.content_management_service, "set_content_expiration", mock_expire
    )
    message, _ = _make_message()

    asyncio.run(expire_command_handler(message, SimpleNamespace(args="code12345 7")))

    mock_expire.assert_awaited_once_with("code12345", 7, actor=123456789)


def test_activate_confirm_callback_delegates_to_mutator() -> None:
    original = content_handlers._MUTATORS["activate"]
    mock_mutator = AsyncMock(return_value=SimpleNamespace(id=1))
    content_handlers._MUTATORS["activate"] = mock_mutator
    try:
        query, _ = _make_query("content:activate:code12345")

        asyncio.run(content_action_callback(query))

        mock_mutator.assert_awaited_once_with("code12345", actor=123456789)
    finally:
        content_handlers._MUTATORS["activate"] = original