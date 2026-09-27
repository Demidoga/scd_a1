"""Shared Redis client factory. One connection pool for the whole process."""

from functools import lru_cache

import redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
