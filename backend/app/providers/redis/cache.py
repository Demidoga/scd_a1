"""Redis-backed caches: `/api/stats` read-through cache and the triage
content-hash cache. Both fail OPEN — a Redis outage degrades to a direct
PostgreSQL query / direct provider call rather than an error, because both
are pure optimizations with no cost-control role. docs/architecture/cache.md
§1, docs/architecture/ai.md §5 "Content-hash cache". Contrast with the rate
limiter (rate_limiter.py), which fails CLOSED.
"""

import hashlib
import json
from dataclasses import asdict

import redis
from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger
from app.core.metrics import TRIAGE_CACHE_HITS, TRIAGE_CACHE_MISSES
from app.domain.triage import TriageResult
from app.repositories.complaints import ComplaintStats

logger = get_logger(__name__)

_STATS_CACHE_KEY = "civicpulse:stats:aggregate"
_TRIAGE_CACHE_PREFIX = "civicpulse:triage:"


class StatsCache:
    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    def get(self) -> ComplaintStats | None:
        try:
            raw = self._client.get(_STATS_CACHE_KEY)
        except redis.RedisError:
            logger.warning("stats_cache_unavailable", operation="get")
            return None
        if raw is None:
            return None
        data = json.loads(raw)
        return ComplaintStats(**data)

    def set(self, stats: ComplaintStats) -> None:
        try:
            self._client.set(_STATS_CACHE_KEY, json.dumps(asdict(stats)), ex=self._ttl_seconds)
        except redis.RedisError:
            logger.warning("stats_cache_unavailable", operation="set")

    def invalidate(self) -> None:
        try:
            self._client.delete(_STATS_CACHE_KEY)
        except redis.RedisError:
            logger.warning("stats_cache_unavailable", operation="invalidate")


class CachedTriage(BaseModel):
    """Cache payload: the validated result plus which provider marker produced
    it, so a cache hit reports true provenance rather than whichever provider
    happens to be active when the hit occurs (relevant if TRIAGE_PROVIDER
    changes while a still-live 24h cache entry exists).
    """

    result: TriageResult
    triaged_by: str


class TriageCache:
    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(text: str, location: str) -> str:
        # Both text and location are hashed together unconditionally — see
        # docs/architecture/ai.md §"Content-hash cache" for why location is
        # always part of the key, not just "when the provider uses it".
        digest = hashlib.sha256(f"{text}\x1f{location}".encode()).hexdigest()
        return f"{_TRIAGE_CACHE_PREFIX}{digest}"

    def get(self, text: str, location: str) -> CachedTriage | None:
        try:
            raw = self._client.get(self._key(text, location))
        except redis.RedisError:
            logger.warning("triage_cache_unavailable", operation="get")
            return None

        if raw is None:
            TRIAGE_CACHE_MISSES.inc()
            return None

        try:
            cached = CachedTriage.model_validate_json(raw)
        except ValidationError:
            # Corrupted/stale entry — never let bad cache data bypass validation.
            TRIAGE_CACHE_MISSES.inc()
            return None

        TRIAGE_CACHE_HITS.inc()
        return cached

    def set(self, text: str, location: str, result: TriageResult, triaged_by: str) -> None:
        payload = CachedTriage(result=result, triaged_by=triaged_by)
        try:
            self._client.set(
                self._key(text, location), payload.model_dump_json(), ex=self._ttl_seconds
            )
        except redis.RedisError:
            logger.warning("triage_cache_unavailable", operation="set")
