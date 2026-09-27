"""Distributed IP rate limiter for POST /api/complaints.

Fixed-window, 10 req/60s/IP by default (configurable), atomic single-round-trip
Lua INCR+EXPIRE — never plain INCR then EXPIRE (a crash between the two would
leave a key with no TTL, permanently locking that IP out).
docs/architecture/cache.md §2.

Fails CLOSED: unlike the caches in cache.py, a Redis outage here raises
DependencyUnavailableError (-> 503), because this exists to protect the
shared Groq free-tier quota, and an outage window is exactly when unlimited
traffic is least affordable.

This is called from the routes layer (the one named exception to
routes -> services -> repositories, see docs/architecture/backend.md §1),
not from services/.
"""

from dataclasses import dataclass

import redis

from app.core.errors import DependencyUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

_LUA_INCR_WITH_EXPIRY = """
local count = redis.call("INCR", KEYS[1])
if count == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return count
"""

_KEY_PREFIX = "civicpulse:ratelimit:"


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class RateLimiter:
    def __init__(self, client: redis.Redis, max_requests: int, window_seconds: int) -> None:
        self._client = client
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._script = client.register_script(_LUA_INCR_WITH_EXPIRY)

    def check(self, client_ip: str) -> RateLimitDecision:
        key = f"{_KEY_PREFIX}{client_ip}"
        try:
            count = self._script(keys=[key], args=[self._window_seconds])
        except redis.RedisError as exc:
            logger.warning("rate_limiter_unavailable", error=str(exc))
            raise DependencyUnavailableError("Redis") from exc

        if count > self._max_requests:
            ttl = self._client.ttl(key)
            retry_after = ttl if ttl and ttl > 0 else self._window_seconds
            return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)
        return RateLimitDecision(allowed=True, retry_after_seconds=0)
