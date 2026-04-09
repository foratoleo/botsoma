"""
Sliding-window rate limiter per conversation.

Uses an in-memory sliding window algorithm that tracks individual request
timestamps.  When Redis is available, the limiter delegates to a Redis
sorted-set implementation for consistency across multiple bot instances.

Default limit: 10 requests per 60-second window per conversation_id.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = structlog.get_logger(__name__)

_DEFAULT_MAX_REQUESTS: int = 10
_DEFAULT_WINDOW_SECONDS: int = 60

_RATE_LIMIT_KEY_PREFIX: str = "botsoma:ratelimit:"

RATE_LIMIT_MESSAGE: str = (
    "Voce enviou muitas mensagens em pouco tempo. "
    "Aguarde um momento antes de tentar novamente."
)


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of a rate-limit check."""

    allowed: bool
    current_count: int
    limit: int
    retry_after_seconds: float | None = None


class RateLimiter:
    """Sliding-window rate limiter with optional Redis backend.

    Parameters
    ----------
    max_requests:
        Maximum number of requests allowed within the window.
    window_seconds:
        Duration of the sliding window in seconds.
    redis_client:
        Optional ``redis.asyncio.Redis`` instance.  When provided, the
        limiter uses Redis sorted sets for distributed rate limiting.
        Falls back to in-memory tracking when ``None``.
    """

    def __init__(
        self,
        max_requests: int = _DEFAULT_MAX_REQUESTS,
        window_seconds: int = _DEFAULT_WINDOW_SECONDS,
        redis_client: Redis | None = None,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._redis = redis_client
        # In-memory fallback: conversation_id -> list of timestamps (epoch float)
        self._buckets: dict[str, list[float]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check(self, conversation_id: str) -> RateLimitResult:
        """Check and record a request for *conversation_id*.

        Returns a ``RateLimitResult`` indicating whether the request is
        allowed or should be rejected.
        """
        if self._redis is not None:
            try:
                return await self._check_redis(conversation_id)
            except Exception as exc:
                logger.warning(
                    "rate_limiter_redis_failed",
                    conversation_id=conversation_id[:20],
                    error=str(exc),
                )
                # Fall through to in-memory check on Redis failure.

        return self._check_memory(conversation_id)

    # ------------------------------------------------------------------
    # In-memory implementation
    # ------------------------------------------------------------------

    def _check_memory(self, conversation_id: str) -> RateLimitResult:
        now = time.monotonic()
        cutoff = now - self._window_seconds

        # Prune expired timestamps.
        timestamps = self._buckets[conversation_id]
        self._buckets[conversation_id] = [
            ts for ts in timestamps if ts > cutoff
        ]
        timestamps = self._buckets[conversation_id]

        if len(timestamps) >= self._max_requests:
            oldest = timestamps[0]
            retry_after = oldest + self._window_seconds - now
            return RateLimitResult(
                allowed=False,
                current_count=len(timestamps),
                limit=self._max_requests,
                retry_after_seconds=round(max(retry_after, 0.1), 1),
            )

        timestamps.append(now)
        return RateLimitResult(
            allowed=True,
            current_count=len(timestamps),
            limit=self._max_requests,
        )

    # ------------------------------------------------------------------
    # Redis implementation (sorted set with score = timestamp)
    # ------------------------------------------------------------------

    def _key(self, conversation_id: str) -> str:
        return f"{_RATE_LIMIT_KEY_PREFIX}{conversation_id}"

    async def _check_redis(self, conversation_id: str) -> RateLimitResult:
        assert self._redis is not None  # noqa: S101

        now = time.time()
        cutoff = now - self._window_seconds
        key = self._key(conversation_id)

        pipe = self._redis.pipeline(transaction=True)
        # Remove entries outside the window.
        pipe.zremrangebyscore(key, "-inf", cutoff)
        # Count remaining entries.
        pipe.zcard(key)
        # Add current request (score = timestamp, member = unique timestamp str).
        pipe.zadd(key, {f"{now}": now})
        # Set TTL so keys auto-expire after window elapses.
        pipe.expire(key, self._window_seconds + 1)
        results = await pipe.execute()

        current_count: int = results[1]  # zcard result before adding new entry

        if current_count >= self._max_requests:
            # Fetch the oldest entry to compute retry_after.
            oldest_entries = await self._redis.zrange(key, 0, 0, withscores=True)
            retry_after = 0.1
            if oldest_entries:
                oldest_score = oldest_entries[0][1]
                retry_after = max(oldest_score + self._window_seconds - now, 0.1)
            return RateLimitResult(
                allowed=False,
                current_count=current_count,
                limit=self._max_requests,
                retry_after_seconds=round(retry_after, 1),
            )

        return RateLimitResult(
            allowed=True,
            current_count=current_count + 1,  # Include the entry we just added.
            limit=self._max_requests,
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def clear(self, conversation_id: str | None = None) -> None:
        """Clear in-memory rate-limit data.

        When *conversation_id* is ``None``, clears all buckets.
        """
        if conversation_id is None:
            self._buckets.clear()
        else:
            self._buckets.pop(conversation_id, None)


# --------------------------------------------------------------------------
# Module-level singleton
# --------------------------------------------------------------------------

_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Return the module-level ``RateLimiter`` singleton.

    Call ``init_rate_limiter()`` at startup to configure it.
    If not initialized, returns a default in-memory limiter.
    """
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter


def init_rate_limiter(
    max_requests: int = _DEFAULT_MAX_REQUESTS,
    window_seconds: int = _DEFAULT_WINDOW_SECONDS,
    redis_client: Redis | None = None,
) -> RateLimiter:
    """Initialize the global rate limiter.

    Should be called once during application startup.
    """
    global _limiter
    _limiter = RateLimiter(
        max_requests=max_requests,
        window_seconds=window_seconds,
        redis_client=redis_client,
    )
    logger.info(
        "rate_limiter_initialized",
        max_requests=max_requests,
        window_seconds=window_seconds,
        backend="redis" if redis_client is not None else "memory",
    )
    return _limiter
