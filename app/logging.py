import logging

VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging in one place.

    Idempotent: the level is applied on every call, the handler is
    attached once, and existing handlers (for example pytest's log
    capture) are left untouched.

    Raises ValueError for unknown levels so misconfiguration fails fast
    and deterministically at startup instead of silently misbehaving.
    """
    global _configured

    normalized = level.upper()
    if normalized not in VALID_LOG_LEVELS:
        raise ValueError(
            f"invalid log level {level!r}; expected one of {', '.join(VALID_LOG_LEVELS)}"
        )

    root = logging.getLogger()
    root.setLevel(normalized)
    if not _configured:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root.addHandler(handler)
        _configured = True
