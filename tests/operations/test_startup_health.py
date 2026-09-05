import asyncio
import logging
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app import logging as app_logging
from app.config import Settings
from app.main import startup
from app.services import health_service
from app.services.health_service import (
    ApplicationState,
    ApplicationStatus,
    HealthReport,
    check_database,
    check_health,
)


def test_configure_logging_applies_valid_level() -> None:
    app_logging.configure_logging("INFO")

    assert logging.getLogger().level == logging.INFO


def test_configure_logging_normalizes_case() -> None:
    try:
        app_logging.configure_logging("debug")

        assert logging.getLogger().level == logging.DEBUG
    finally:
        app_logging.configure_logging("INFO")


def test_configure_logging_rejects_invalid_level() -> None:
    with pytest.raises(ValueError, match="invalid log level"):
        app_logging.configure_logging("VERBOSE")


def test_settings_normalizes_log_level() -> None:
    configured = Settings(
        bot_token="test-token",
        admin_ids=[1],
        database_url="sqlite://",
        log_level="warning",
    )

    assert configured.log_level == "WARNING"


def test_settings_rejects_invalid_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(
            bot_token="test-token",
            admin_ids=[1],
            database_url="sqlite://",
            log_level="VERBOSE",
        )


def test_check_database_healthy() -> None:
    assert asyncio.run(check_database()) is True


def test_check_database_failure_detected_and_logged(
    monkeypatch, caplog: pytest.LogCaptureFixture
) -> None:
    class BrokenEngine:
        def connect(self) -> object:
            raise OperationalError("SELECT 1", {}, Exception("down"))

    monkeypatch.setattr(health_service, "engine", BrokenEngine())

    with caplog.at_level(logging.WARNING):
        assert asyncio.run(check_database()) is False

    assert "event=database_health_check_failed" in caplog.text


def test_check_health_report_when_ready_and_healthy() -> None:
    status = ApplicationStatus()
    status.mark_ready()

    report = asyncio.run(check_health(status))

    assert report == HealthReport(
        ready=True, database=True, state=ApplicationState.READY
    )
    assert report.healthy is True


def test_check_health_report_when_not_ready() -> None:
    report = asyncio.run(check_health(ApplicationStatus()))

    assert report.ready is False
    assert report.database is True
    assert report.state == ApplicationState.STARTING
    assert report.healthy is False


def test_check_health_report_when_database_down(monkeypatch) -> None:
    class BrokenEngine:
        def connect(self) -> object:
            raise OperationalError("SELECT 1", {}, Exception("down"))

    monkeypatch.setattr(health_service, "engine", BrokenEngine())
    status = ApplicationStatus()
    status.mark_ready()

    report = asyncio.run(check_health(status))

    assert report.ready is True
    assert report.database is False
    assert report.healthy is False


def test_initial_status_is_not_ready() -> None:
    status = ApplicationStatus()

    assert status.state == ApplicationState.STARTING
    assert status.is_ready is False


def test_startup_marks_ready_and_logs_milestones(
    monkeypatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr("app.main.init_db", AsyncMock())
    monkeypatch.setattr("app.main.check_database", AsyncMock(return_value=True))
    status = ApplicationStatus()

    with caplog.at_level(logging.INFO):
        asyncio.run(startup(status))

    assert status.is_ready is True
    assert status.state == ApplicationState.READY
    for event in (
        "event=application_starting",
        "event=database_initialization_starting",
        "event=database_initialization_completed",
        "event=application_ready",
    ):
        assert event in caplog.text


def test_startup_failure_marks_failed_and_reraises(
    monkeypatch, caplog: pytest.LogCaptureFixture
) -> None:
    async def failing_init() -> None:
        raise RuntimeError("migration exploded")

    monkeypatch.setattr("app.main.init_db", failing_init)
    status = ApplicationStatus()

    with (
        caplog.at_level(logging.INFO),
        pytest.raises(RuntimeError, match="migration exploded"),
    ):
        asyncio.run(startup(status))

    assert status.state == ApplicationState.FAILED
    assert status.is_ready is False
    assert "event=startup_failed" in caplog.text


def test_startup_fails_when_health_check_fails(monkeypatch) -> None:
    monkeypatch.setattr("app.main.init_db", AsyncMock())
    monkeypatch.setattr("app.main.check_database", AsyncMock(return_value=False))
    status = ApplicationStatus()

    with pytest.raises(RuntimeError, match="startup database health check"):
        asyncio.run(startup(status))

    assert status.state == ApplicationState.FAILED
    assert status.is_ready is False
