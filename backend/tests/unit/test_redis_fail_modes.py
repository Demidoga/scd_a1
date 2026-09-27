"""Redis outage behavior — the caches fail OPEN, the rate limiter fails
CLOSED. This asymmetry is a named invariant, not an accident:
docs/architecture/cache.md §2 "When Redis itself is unreachable" and §5
invariants checklist.
"""

from unittest.mock import MagicMock

import pytest
import redis

from app.core.errors import DependencyUnavailableError
from app.domain.triage import TriageResult
from app.providers.redis.cache import StatsCache, TriageCache
from app.providers.redis.rate_limiter import RateLimiter
from app.repositories.complaints import ComplaintStats


def _broken_redis_client() -> MagicMock:
    client = MagicMock(spec=redis.Redis)
    client.get.side_effect = redis.RedisError("connection refused")
    client.set.side_effect = redis.RedisError("connection refused")
    client.delete.side_effect = redis.RedisError("connection refused")
    client.register_script.return_value = MagicMock(
        side_effect=redis.RedisError("connection refused")
    )
    return client


def test_stats_cache_get_fails_open_to_none() -> None:
    cache = StatsCache(_broken_redis_client(), ttl_seconds=30)
    assert cache.get() is None  # caller treats this as a cache miss, queries PostgreSQL instead


def test_stats_cache_set_and_invalidate_do_not_raise() -> None:
    cache = StatsCache(_broken_redis_client(), ttl_seconds=30)
    stats = ComplaintStats(total=0, by_status={}, by_category={}, by_priority={})
    cache.set(stats)  # must not raise — a failed cache write is not a request failure
    cache.invalidate()


def test_triage_cache_get_fails_open_to_none() -> None:
    cache = TriageCache(_broken_redis_client(), ttl_seconds=86400)
    assert cache.get("some complaint text", "some location") is None


def test_triage_cache_set_does_not_raise() -> None:
    cache = TriageCache(_broken_redis_client(), ttl_seconds=86400)
    result = TriageResult(category="water", priority="high", summary="x", confidence=0.5)
    cache.set("text", "location", result, "simulated")  # must not raise


def test_rate_limiter_fails_closed_on_redis_outage() -> None:
    limiter = RateLimiter(_broken_redis_client(), max_requests=10, window_seconds=60)
    with pytest.raises(DependencyUnavailableError):
        limiter.check("1.2.3.4")
