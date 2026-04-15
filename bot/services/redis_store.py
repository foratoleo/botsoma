"""
Redis-backed session store with automatic fallback to in-memory storage.

Provides ``RedisSessionStore`` that serializes ``Session`` dataclasses to JSON
and stores them in Redis with a configurable TTL (default 7 days).

When Redis is unavailable at startup or during operation, the store
transparently falls back to an in-memory ``dict`` and logs a warning so
the bot never crashes due to a missing cache layer.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = structlog.get_logger(__name__)

# Default session TTL: 7 days in seconds.
_DEFAULT_TTL_SECONDS: int = 7 * 24 * 60 * 60

_SESSION_KEY_PREFIX: str = "botsoma:session:"


class RedisSessionStore:
    """Async session store backed by Redis with in-memory fallback.

    Parameters
    ----------
    redis_url:
        Redis connection URL (e.g. ``redis://localhost:6379/0``).
        When ``None`` or empty, the store starts directly in fallback mode.
    ttl_seconds:
        Per-session TTL applied on every save.  Defaults to 7 days.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> None:
        self._redis_url = redis_url
        self._ttl = ttl_seconds
        self._redis: Redis | None = None
        self._fallback: dict[str, dict] = {}
        self._using_fallback: bool = not bool(redis_url)
        self._connected: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Establish Redis connection.  Falls back silently on failure."""
        if self._using_fallback:
            logger.warning(
                "redis_not_configured",
                msg="REDIS_URL not set — using in-memory session store",
            )
            return

        try:
            from redis.asyncio import from_url  # type: ignore[import-untyped]

            self._redis = from_url(
                self._redis_url,  # type: ignore[arg-type]
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Verify connectivity with a PING.
            await self._redis.ping()  # type: ignore[union-attr]
            self._connected = True
            logger.info("redis_connected", url=self._redis_url)
        except Exception as exc:
            logger.warning(
                "redis_connect_failed",
                error=str(exc),
                msg="Falling back to in-memory session store",
            )
            self._redis = None
            self._using_fallback = True

    async def close(self) -> None:
        """Close Redis connection gracefully."""
        if self._redis is not None:
            try:
                await self._redis.aclose()  # type: ignore[union-attr]
            except Exception:
                pass
            self._redis = None
            self._connected = False

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def _key(self, session_id: str) -> str:
        return f"{_SESSION_KEY_PREFIX}{session_id}"

    async def get(self, session_id: str) -> dict | None:
        """Return serialized session dict or ``None`` if not found."""
        if self._using_fallback or self._redis is None:
            return self._fallback.get(session_id)

        try:
            raw = await self._redis.get(self._key(session_id))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning(
                "redis_get_failed",
                session_id=session_id,
                error=str(exc),
            )
            # Try fallback on transient failure.
            return self._fallback.get(session_id)

    async def save(self, session_id: str, data: dict) -> None:
        """Persist a session dict with TTL refresh."""
        # Always keep a copy in fallback for resilience.
        self._fallback[session_id] = data

        if self._using_fallback or self._redis is None:
            return

        try:
            await self._redis.setex(
                self._key(session_id),
                self._ttl,
                json.dumps(data, ensure_ascii=False),
            )
        except Exception as exc:
            logger.warning(
                "redis_save_failed",
                session_id=session_id,
                error=str(exc),
            )

    async def delete(self, session_id: str) -> None:
        """Remove a session from both Redis and in-memory fallback."""
        self._fallback.pop(session_id, None)

        if self._using_fallback or self._redis is None:
            return

        try:
            await self._redis.delete(self._key(session_id))
        except Exception as exc:
            logger.warning(
                "redis_delete_failed",
                session_id=session_id,
                error=str(exc),
            )

    async def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        if self._using_fallback or self._redis is None:
            return session_id in self._fallback

        try:
            return bool(await self._redis.exists(self._key(session_id)))
        except Exception:
            return session_id in self._fallback

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def is_redis_connected(self) -> bool:
        return self._connected and not self._using_fallback

    @property
    def is_fallback_mode(self) -> bool:
        return self._using_fallback


# --------------------------------------------------------------------------
# Session serialization helpers
# --------------------------------------------------------------------------


def session_to_dict(session: object) -> dict:
    """Convert a ``Session`` dataclass instance to a plain dict for JSON storage."""
    return asdict(session)  # type: ignore[arg-type]


def dict_to_session(data: dict) -> object:
    """Reconstruct a ``Session`` dataclass from a stored dict.

    Import is deferred to avoid circular imports (Session lives in triage_flow).
    """
    from bot.services.sentiment import FrustrationTracker
    from bot.services.triage_flow import Session

    # Reconstruct the frustration tracker from stored data (if present).
    tracker_data = data.get("frustration_tracker")
    if isinstance(tracker_data, dict):
        frustration_tracker = FrustrationTracker.from_dict(tracker_data)
    else:
        frustration_tracker = FrustrationTracker()

    return Session(
        id=data["id"],
        turns=data.get("turns", []),
        questions_asked=data.get("questions_asked", 0),
        closed=data.get("closed", False),
        last_bot_question=data.get("last_bot_question", ""),
        in_follow_up=data.get("in_follow_up", False),
        frustration_tracker=frustration_tracker,
        pending_classification=data.get("pending_classification", ""),
        classification_confirmed=data.get("classification_confirmed", False),
        channel=data.get("channel", "teams"),
    )


# --------------------------------------------------------------------------
# Module-level singleton
# --------------------------------------------------------------------------

_store: RedisSessionStore | None = None


def get_session_store() -> RedisSessionStore:
    """Return the module-level ``RedisSessionStore`` singleton.

    Call ``init_session_store()`` at application startup to configure it.
    If not initialized, returns a fallback-only store.
    """
    global _store
    if _store is None:
        _store = RedisSessionStore()
    return _store


async def init_session_store(redis_url: str | None = None) -> RedisSessionStore:
    """Initialize and connect the global session store.

    Should be called once during application startup.
    """
    global _store
    _store = RedisSessionStore(redis_url=redis_url)
    await _store.connect()
    return _store
