"""Route-level FastAPI dependencies.

`enforce_rate_limit` is the one deliberate exception to routes -> services ->
repositories (docs/architecture/backend.md §1 "Named exception: the rate
limiter"): it talks to Redis directly from the routes layer, and — because
FastAPI resolves `dependencies=[Depends(...)]` before validating the request
body against its Pydantic model — it runs *before* Pydantic validation, so an
abusive request never spends validation or AI budget.
"""

from functools import lru_cache

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import RateLimitExceededError
from app.core.logging import get_logger
from app.providers.redis.client import get_redis_client
from app.providers.redis.rate_limiter import RateLimiter

logger = get_logger(__name__)


@lru_cache
def _get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(
        client=get_redis_client(),
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


def enforce_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    decision = _get_rate_limiter().check(client_ip)
    if not decision.allowed:
        logger.warning("rate_limit_exceeded", client_ip=client_ip)
        raise RateLimitExceededError(retry_after_seconds=decision.retry_after_seconds)
