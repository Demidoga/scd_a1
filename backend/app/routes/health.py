"""`/health` (liveness, DB-independent) and `/ready` (readiness, checks
PostgreSQL + Redis). These semantics must never be swapped — see
docs/architecture/backend.md §6.
"""

from fastapi import APIRouter

from app.core.errors import DependencyUnavailableError
from app.core.health import check_database, check_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str]:
    if not check_database():
        raise DependencyUnavailableError("postgresql")
    if not check_redis():
        raise DependencyUnavailableError("redis")
    return {"status": "ready"}
