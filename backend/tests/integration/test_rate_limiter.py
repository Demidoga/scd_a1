"""Distributed Redis rate limiter — real Redis, atomic Lua INCR+EXPIRE.
docs/architecture/cache.md §2, docs/Milestones/milestone-3.md §22.7.
"""

from fastapi.testclient import TestClient

from app.providers.redis.client import get_redis_client
from app.providers.redis.rate_limiter import RateLimiter

VALID_PAYLOAD = {
    "text": "Water pipe burst near our house, flooding the street badly",
    "location": "Street 12, G-9/1, Islamabad",
}


def test_requests_under_limit_are_allowed() -> None:
    limiter = RateLimiter(get_redis_client(), max_requests=3, window_seconds=60)
    for _ in range(3):
        decision = limiter.check("1.2.3.4")
        assert decision.allowed is True


def test_exceeding_limit_returns_not_allowed_with_retry_after() -> None:
    limiter = RateLimiter(get_redis_client(), max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("5.6.7.8")

    decision = limiter.check("5.6.7.8")
    assert decision.allowed is False
    assert decision.retry_after_seconds > 0


def test_limit_is_keyed_per_ip() -> None:
    limiter = RateLimiter(get_redis_client(), max_requests=1, window_seconds=60)
    assert limiter.check("9.9.9.9").allowed is True
    assert limiter.check("9.9.9.9").allowed is False
    assert limiter.check("10.10.10.10").allowed is True  # different IP, separate window


def test_api_returns_429_with_retry_after_once_limit_exceeded(client: TestClient) -> None:
    # Default limit is 10 req/60s (RATE_LIMIT_REQUESTS default) — send 11.
    last_response = None
    for _ in range(11):
        last_response = client.post("/api/complaints", json=VALID_PAYLOAD)

    assert last_response is not None
    assert last_response.status_code == 429
    assert "Retry-After" in last_response.headers
