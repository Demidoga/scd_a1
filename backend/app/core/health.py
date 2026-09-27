"""Dependency reachability probes for /ready. Not domain SQL — a bare
connectivity check, not a query against the complaints schema — so this
stays out of app/repositories and is used directly by the /ready route.
docs/architecture/backend.md §6.
"""

from sqlalchemy import text

from app.core.db import get_engine
from app.providers.redis.client import get_redis_client


def check_database() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception:
        return False
