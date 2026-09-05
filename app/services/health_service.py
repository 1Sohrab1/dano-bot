import logging
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import text

from app.database.database import engine

logger = logging.getLogger(__name__)


class ApplicationState(StrEnum):
    STARTING = "starting"
    READY = "ready"
    FAILED = "failed"


class ApplicationStatus:
    """Lightweight mutable holder for the process lifecycle state."""

    def __init__(self) -> None:
        self._state = ApplicationState.STARTING

    @property
    def state(self) -> ApplicationState:
        return self._state

    @property
    def is_ready(self) -> bool:
        return self._state == ApplicationState.READY

    def mark_ready(self) -> None:
        self._state = ApplicationState.READY

    def mark_failed(self) -> None:
        self._state = ApplicationState.FAILED


application_status = ApplicationStatus()


@dataclass(frozen=True)
class HealthReport:
    ready: bool
    database: bool
    state: ApplicationState

    @property
    def healthy(self) -> bool:
        return self.ready and self.database


async def check_database() -> bool:
    """Verify database connectivity with a lightweight query."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as error:  # noqa: BLE001 - any failure means unhealthy
        logger.warning(
            "event=database_health_check_failed error_type=%s",
            error.__class__.__name__,
        )
        return False

    return True


async def check_health(
    status: ApplicationStatus = application_status,
) -> HealthReport:
    """Build a health report suitable for future deployment probes."""
    database_ok = await check_database()
    return HealthReport(
        ready=status.is_ready, database=database_ok, state=status.state
    )
