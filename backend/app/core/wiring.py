"""Composition root: wires providers/repositories/services together behind
FastAPI dependency functions. Routes depend on `get_complaint_service`
(and friends) — never on repositories or providers directly — so the
routes -> services -> repositories direction (docs/architecture/backend.md §1)
holds by construction.
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_db_session
from app.providers.redis.cache import StatsCache, TriageCache
from app.providers.redis.client import get_redis_client
from app.providers.triage.base import TriageProvider
from app.providers.triage.factory import create_triage_provider
from app.repositories.complaints import ComplaintRepository
from app.services.complaints import ComplaintService
from app.services.triage import TriageService


@lru_cache
def get_triage_provider() -> TriageProvider:
    """The active provider is a process-wide singleton — constructed once
    from TRIAGE_PROVIDER, not re-selected per request."""
    return create_triage_provider(get_settings())


def build_complaint_service(
    db: Session,
    settings: Settings | None = None,
    provider: TriageProvider | None = None,
) -> ComplaintService:
    """Plain factory, usable outside FastAPI's DI (seed script, tests).

    `get_complaint_service` below is the FastAPI-dependency-shaped wrapper
    around this that routes actually use. `provider` is accepted explicitly
    (rather than always calling `get_triage_provider()` internally) so tests
    can override it via FastAPI's `dependency_overrides` on
    `get_triage_provider` — e.g. to inject an always-failing provider for
    the mandatory fallback test (docs/architecture/testing.md §2).
    """
    settings = settings or get_settings()
    provider = provider or get_triage_provider()
    redis_client = get_redis_client()
    repository = ComplaintRepository(db)
    triage_cache = TriageCache(redis_client, settings.triage_cache_ttl_seconds)
    triage_service = TriageService(provider=provider, cache=triage_cache)
    stats_cache = StatsCache(redis_client, settings.stats_cache_ttl_seconds)
    return ComplaintService(repository, triage_service, stats_cache)


def get_complaint_service(
    db: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    provider: TriageProvider = Depends(get_triage_provider),
) -> ComplaintService:
    return build_complaint_service(db, settings, provider)
