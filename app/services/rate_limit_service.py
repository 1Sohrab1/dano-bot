import asyncio
import logging
import time

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 60
MAX_TRACKED_KEYS = 100_000


class RateLimitStoreFullError(Exception):
    """Raised when the store is at capacity and cannot track a new key.

    Handled by `is_allowed()`, which fails open so the bot stays available.
    """


class InMemoryRateLimitStore:
    """Fixed-window in-memory counter store.

    Storage strategy: single-process memory only. Counters are keyed by
    ``"<scope>:<telegram_user_id>"`` and reset when the window elapses.
    This is intentionally simple: no external infrastructure, no shared
    state between bot instances, and counters are lost on restart.

    Capacity policy: at most ``MAX_TRACKED_KEYS`` buckets are tracked. When
    a new key arrives at capacity, expired buckets are pruned first; if the
    store is still full, the new key is rejected with
    `RateLimitStoreFullError` and the event is allowed (fail open). Active
    buckets are never evicted.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, tuple[float, int]] = {}
        self._lock = asyncio.Lock()

    async def increment(
        self, key: str, window_seconds: int, *, now: float | None = None
    ) -> int:
        current = time.monotonic() if now is None else now
        async with self._lock:
            if key in self._buckets:
                start, count = self._buckets[key]
                if current - start >= window_seconds:
                    start, count = current, 0
                count += 1
                self._buckets[key] = (start, count)
                return count

            if len(self._buckets) >= MAX_TRACKED_KEYS:
                self._prune_expired(current, window_seconds)
                if len(self._buckets) >= MAX_TRACKED_KEYS:
                    raise RateLimitStoreFullError(
                        "rate limit store capacity exceeded"
                    )

            self._buckets[key] = (current, 1)
            return 1

    def _prune_expired(self, current: float, window_seconds: int) -> None:
        expired = [
            key
            for key, (start, _) in self._buckets.items()
            if current - start >= window_seconds
        ]
        for key in expired:
            del self._buckets[key]

    def clear(self) -> None:
        self._buckets.clear()


_default_store = InMemoryRateLimitStore()


def _bucket_key(scope: str, user_id: int) -> str:
    return f"{scope}:{user_id}"


async def is_allowed(
    *,
    scope: str,
    user_id: int,
    limit: int,
    window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    store: InMemoryRateLimitStore | None = None,
    now: float | None = None,
) -> bool:
    """Return True when the event is within the configured fixed-window limit.

    Storage failures fail open (the event is allowed) so a broken rate-limit
    backend can never take the bot offline. Exceeded limits fail closed.
    """
    backend = store if store is not None else _default_store
    try:
        count = await backend.increment(
            _bucket_key(scope, user_id), window_seconds, now=now
        )
    except Exception as error:  # noqa: BLE001 - any backend failure must fail open
        logger.warning(
            "event=rate_limit_store_failed scope=%s user_id=%s error_type=%s",
            scope,
            user_id,
            error.__class__.__name__,
        )
        return True

    if count > limit:
        logger.info(
            "event=rate_limit_exceeded scope=%s user_id=%s count=%s limit=%s",
            scope,
            user_id,
            count,
            limit,
        )
        return False

    return True
