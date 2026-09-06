import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.database.models import ContentState
from app.database.repositories import create_content, get_content_by_code
from app.router.admin.content.callbacks import ContentUx, ContentUxAction
from app.router.admin.content.handlers import (
    CANCEL_REPLY,
    CONTENT_NOT_FOUND_REPLY,
    DELETE_CONFIRM_TEXT,
    EXPIRATION_PROMPT_TEXT,
    INVALID_EXPIRATION_INPUT_REPLY,
    INVALID_EXPIRATION_VALUE_REPLY,
    INVALID_REQUEST_REPLY,
    LIST_EMPTY_REPLY,
    SUCCESS_EXPIRATION_CLEARED_REPLY,
    content_ux_callback,
    expiration_days_handler,
    expiration_invalid_handler,
    format_content_detail,
    format_content_list,
)
from app.router.admin.content.states import ExpirationStates


class FakeState:
    def __init__(self) -> None:
        self._data: dict = {}
        self._state = None

    async def update_data(self, **kwargs) -> None:
        self._data.update(kwargs)

    async def get_data(self) -> dict:
        return dict(self._data)

    async def set_state(self, state) -> None:
        self._state = state

    async def get_state(self):
        return self._state

    async def clear(self) -> None:
        self._data.clear()
        self._state = None


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


def _make_query() -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text=None, show_alert: bool = False):
        recorded["answer"] = text
        recorded["show_alert"] = show_alert

    async def edit_text(text, reply_markup=None):
        recorded["edit_text"] = text
        recorded["edit_markup"] = reply_markup

    return (
        SimpleNamespace(
            from_user=SimpleNamespace(id=123456789),
            message=SimpleNamespace(
                edit_text=edit_text,
                message_id=100,
                chat=SimpleNamespace(id=123456789),
            ),
            answer=answer,
        ),
        recorded,
    )


def _make_message(text: str) -> tuple[SimpleNamespace, dict]:
    recorded: dict = {}

    async def answer(text, reply_markup=None):
        recorded["text"] = text
        recorded["reply_markup"] = reply_markup

    return (
        SimpleNamespace(
            from_user=SimpleNamespace(id=123456789),
            text=text,
            answer=answer,
        ),
        recorded,
    )


def _button_rows(recorded: dict) -> list[list[SimpleNamespace]]:
    return recorded["edit_markup"].inline_keyboard


def _row_texts(recorded: dict) -> list[list[str]]:
    return [
        [button.text for button in row]
        for row in _button_rows(recorded)
    ]


def _row_callbacks(recorded: dict) -> list[list[str]]:
    return [
        [button.callback_data for button in row]
        for row in _button_rows(recorded)
    ]


def test_content_ux_callback_data_round_trip() -> None:
    for action in ContentUxAction:
        packed = ContentUx(action=action, code="code123", page=2).pack()
        unpacked = ContentUx.unpack(packed)
        assert unpacked.action == action
        assert unpacked.code == "code123"
        assert unpacked.page == 2


def test_list_renders_paginated_selectable_items() -> None:
    for i in range(12):
        _seed(f"pgitem{i:02d}")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.LIST, page=1), FakeState()
        )
    )

    assert "صفحه 1 از 2" in recorded["edit_text"]
    rows = _button_rows(recorded)
    assert len(rows) == 12  # 10 items + pagination + back
    first = ContentUx.unpack(rows[0][0].callback_data)
    assert first.action == ContentUxAction.DETAIL
    assert first.code.startswith("pgitem")
    assert first.page == 1
    assert "بعدی ▶️" in [button.text for button in rows[10]]
    assert "← بازگشت به پنل" in [button.text for button in rows[11]]


def test_list_pagination_moves_between_pages() -> None:
    for i in range(12):
        _seed(f"pgnav{i:02d}")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.LIST, page=2), FakeState()
        )
    )

    assert "صفحه 2 از 2" in recorded["edit_text"]
    rows = _button_rows(recorded)
    assert len(rows) == 4  # 2 items + pagination + back
    assert "قبلی ◀️" in [button.text for button in rows[2]]
    assert "بعدی ▶️" not in [button.text for button in rows[2]]
    prev = ContentUx.unpack(rows[2][0].callback_data)
    assert prev.action == ContentUxAction.LIST
    assert prev.page == 1


def test_out_of_range_page_renders_last_safe_page() -> None:
    for i in range(3):
        _seed(f"pgsafe{i:02d}")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.LIST, page=99), FakeState()
        )
    )

    assert "صفحه 1 از 1" in recorded["edit_text"]


def test_zero_page_renders_first_safe_page() -> None:
    for i in range(3):
        _seed(f"pgzero{i:02d}")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.LIST, page=0), FakeState()
        )
    )

    assert "صفحه 1 از 1" in recorded["edit_text"]


def test_empty_list_renders_spec_empty_state() -> None:
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.LIST, page=1), FakeState()
        )
    )

    assert recorded["edit_text"] == LIST_EMPTY_REPLY
    rows = _button_rows(recorded)
    assert len(rows) == 1
    assert rows[0][0].text == "← بازگشت به پنل"


def test_detail_renders_exact_spec_format() -> None:
    _seed("detailcode", expires_at=datetime(2030, 1, 1, tzinfo=UTC))
    query, recorded = _make_query()

    stored = asyncio.run(get_content_by_code("detailcode"))
    assert stored is not None
    asyncio.run(
        content_ux_callback(
            query,
            ContentUx(
                action=ContentUxAction.DETAIL, code="detailcode", page=1
            ),
            FakeState(),
        )
    )

    assert recorded["edit_text"] == format_content_detail(stored)
    assert "کد: detailcode" in recorded["edit_text"]
    assert "نوع: document" in recorded["edit_text"]
    assert "وضعیت: فعال" in recorded["edit_text"]
    assert "انقضا: 2030-01-01 00:00" in recorded["edit_text"]


def test_active_detail_offers_active_action_set() -> None:
    _seed("activeset")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DETAIL, code="activeset", page=2), FakeState()
        )
    )

    assert _row_texts(recorded) == [
        ["⛔ غیرفعال کردن"],
        ["🗓 تنظیم انقضا"],
        ["🗑 حذف محتوا"],
        ["← بازگشت"],
    ]
    back = ContentUx.unpack(_button_rows(recorded)[3][0].callback_data)
    assert back.action == ContentUxAction.LIST
    assert back.page == 2


def test_inactive_detail_offers_inactive_action_set() -> None:
    _seed("inactives", state=ContentState.INACTIVE)
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DETAIL, code="inactives", page=1), FakeState()
        )
    )

    assert _row_texts(recorded) == [
        ["✅ فعال کردن"],
        ["🗓 تنظیم انقضا"],
        ["🗑 حذف محتوا"],
        ["← بازگشت"],
    ]


def test_activate_button_activates_and_rerenders_detail() -> None:
    _seed("uxact0001", state=ContentState.INACTIVE)
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.ACTIVATE, code="uxact0001", page=1), FakeState()
        )
    )

    stored = asyncio.run(get_content_by_code("uxact0001"))
    assert stored is not None
    assert stored.state == ContentState.ACTIVE
    assert "فعال شد" in recorded["answer"]
    assert "وضعیت: فعال" in recorded["edit_text"]
    assert "⛔ غیرفعال کردن" in _row_texts(recorded)[0]


def test_deactivate_button_deactivates_and_rerenders_detail() -> None:
    _seed("uxdeact01")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DEACTIVATE, code="uxdeact01", page=1), FakeState()
        )
    )

    stored = asyncio.run(get_content_by_code("uxdeact01"))
    assert stored is not None
    assert stored.state == ContentState.INACTIVE
    assert "غیرفعال شد" in recorded["answer"]
    assert "وضعیت: غیرفعال" in recorded["edit_text"]
    assert "✅ فعال کردن" in _row_texts(recorded)[0]


def test_activate_button_revalidates_already_active() -> None:
    _seed("uxalready")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.ACTIVATE, code="uxalready", page=1), FakeState()
        )
    )

    assert recorded["answer"] == "این محتوا از قبل فعال است."


def test_delete_start_renders_confirmation_without_deleting() -> None:
    _seed("uxdelstart")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DELETE_START, code="uxdelstart", page=1), FakeState()
        )
    )

    assert recorded["edit_text"] == DELETE_CONFIRM_TEXT
    assert "غیرقابل بازگشت" in recorded["edit_text"]
    assert _row_texts(recorded) == [["🗑 بله، حذف کن", "لغو"]]
    assert asyncio.run(get_content_by_code("uxdelstart")) is not None


def test_delete_cancel_returns_to_detail_and_keeps_content() -> None:
    _seed("uxdelcancel")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.CANCEL, code="uxdelcancel", page=1), FakeState()
        )
    )

    assert recorded["answer"] == CANCEL_REPLY
    assert "کد: uxdelcancel" in recorded["edit_text"]
    assert asyncio.run(get_content_by_code("uxdelcancel")) is not None


def test_delete_confirm_deletes_and_clears_keyboard() -> None:
    _seed("uxdeldone")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DELETE_CONFIRM, code="uxdeldone", page=1), FakeState()
        )
    )

    assert asyncio.run(get_content_by_code("uxdeldone")) is None
    assert "حذف شد" in recorded["answer"]
    assert recorded["edit_text"] == "محتوا حذف شد 🗑️"


def test_stale_delete_confirm_fails_safely() -> None:
    _seed("uxdelstale")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DELETE_CONFIRM, code="uxdelstale", page=1), FakeState()
        )
    )
    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DELETE_CONFIRM, code="uxdelstale", page=1), FakeState()
        )
    )

    assert recorded["answer"] == CONTENT_NOT_FOUND_REPLY


def test_expire_starts_awaiting_days_flow() -> None:
    _seed("uxexpstart")
    query, recorded = _make_query()
    state = FakeState()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.EXPIRE, code="uxexpstart", page=1), state
        )
    )

    assert asyncio.run(state.get_state()) == ExpirationStates.awaiting_days
    data = asyncio.run(state.get_data())
    assert data["code"] == "uxexpstart"
    assert data["chat_id"] == 123456789
    assert data["message_id"] == 100
    assert recorded["edit_text"] == EXPIRATION_PROMPT_TEXT
    assert _row_texts(recorded) == [["بدون انقضا"], ["لغو"]]


def test_expiration_days_input_sets_expiration_and_clears_state() -> None:
    _seed("uxexpdays")
    state = FakeState()
    asyncio.run(
        state.update_data(code="uxexpdays", page=1, chat_id=123, message_id=7)
    )
    asyncio.run(state.set_state(ExpirationStates.awaiting_days))
    message, recorded = _make_message("7")

    asyncio.run(expiration_days_handler(message, state))

    stored = asyncio.run(get_content_by_code("uxexpdays"))
    assert stored is not None
    assert stored.expires_at is not None
    assert (
        abs(
            (stored.expires_at - (datetime.now(UTC) + timedelta(days=7))).total_seconds()
        )
        < 30
    )
    assert "تنظیم شد" in recorded["text"]
    assert asyncio.run(state.get_state()) is None
    assert asyncio.run(state.get_data()) == {}


def test_expiration_days_replaces_stale_prompt_message() -> None:
    _seed("uxexpedit")
    recorded: dict = {}

    async def answer(text, reply_markup=None):
        recorded["text"] = text

    bot = AsyncMock()
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=123456789),
        text="3",
        bot=bot,
        answer=answer,
    )
    state = FakeState()
    asyncio.run(
        state.update_data(code="uxexpedit", page=1, chat_id=123, message_id=7)
    )
    asyncio.run(state.set_state(ExpirationStates.awaiting_days))

    asyncio.run(expiration_days_handler(message, state))

    bot.edit_message_text.assert_awaited_once()
    assert "تنظیم شد" in recorded["text"]


def test_expiration_invalid_non_numeric_input_is_safe() -> None:
    _seed("uxexpbad1")
    state = FakeState()
    asyncio.run(state.update_data(code="uxexpbad1"))
    asyncio.run(state.set_state(ExpirationStates.awaiting_days))
    message, recorded = _make_message("abc")

    asyncio.run(expiration_invalid_handler(message))

    assert recorded["text"] == INVALID_EXPIRATION_INPUT_REPLY


def test_expiration_zero_days_is_rejected_and_state_kept() -> None:
    _seed("uxexpzero")
    state = FakeState()
    asyncio.run(state.update_data(code="uxexpzero"))
    asyncio.run(state.set_state(ExpirationStates.awaiting_days))
    message, recorded = _make_message("0")

    asyncio.run(expiration_days_handler(message, state))

    assert recorded["text"] == INVALID_EXPIRATION_VALUE_REPLY
    stored = asyncio.run(get_content_by_code("uxexpzero"))
    assert stored is not None
    assert stored.expires_at is None
    assert asyncio.run(state.get_state()) == ExpirationStates.awaiting_days


def test_expiration_off_clears_expiration_and_rerenders_detail() -> None:
    _seed("uxexpoff", expires_at=datetime(2030, 1, 1, tzinfo=UTC))
    query, recorded = _make_query()
    state = FakeState()
    asyncio.run(state.set_state(ExpirationStates.awaiting_days))

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.EXPIRE_OFF, code="uxexpoff", page=1), state
        )
    )

    stored = asyncio.run(get_content_by_code("uxexpoff"))
    assert stored is not None
    assert stored.expires_at is None
    assert recorded["answer"] == SUCCESS_EXPIRATION_CLEARED_REPLY
    assert "انقضا: بدون انقضا" in recorded["edit_text"]
    assert asyncio.run(state.get_state()) is None


def test_expire_cancel_discards_flow_and_returns_to_detail() -> None:
    _seed("uxexpcancel")
    query, recorded = _make_query()
    state = FakeState()
    asyncio.run(
        state.update_data(code="uxexpcancel", page=1, chat_id=123, message_id=7)
    )
    asyncio.run(state.set_state(ExpirationStates.awaiting_days))

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.CANCEL, code="uxexpcancel", page=1), state
        )
    )

    assert recorded["answer"] == CANCEL_REPLY
    assert "کد: uxexpcancel" in recorded["edit_text"]
    stored = asyncio.run(get_content_by_code("uxexpcancel"))
    assert stored is not None
    assert stored.expires_at is None
    assert asyncio.run(state.get_state()) is None


def test_unknown_content_ux_action_is_rejected() -> None:
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query,
            ContentUx.model_construct(action="unknown", code="x"),
            FakeState(),
        )
    )

    assert recorded["answer"] == INVALID_REQUEST_REPLY
    assert "edit_text" not in recorded


def test_detail_back_navigates_to_originating_page() -> None:
    for i in range(12):
        _seed(f"pgback{i:02d}")
    query, recorded = _make_query()

    asyncio.run(
        content_ux_callback(
            query, ContentUx(action=ContentUxAction.DETAIL, code="pgback02", page=2), FakeState()
        )
    )

    back = ContentUx.unpack(_button_rows(recorded)[3][0].callback_data)
    assert back.action == ContentUxAction.LIST
    assert back.page == 2


def test_list_empty_via_list_handler_content() -> None:
    from app.services.content_management_service import ContentPage

    empty_page = ContentPage(items=[], page=1, page_size=10, total=0, total_pages=1)
    assert format_content_list(empty_page) == LIST_EMPTY_REPLY