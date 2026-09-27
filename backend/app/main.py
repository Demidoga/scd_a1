"""FastAPI application entrypoint. Wires middleware, exception handlers, and
routers — no business logic here. docs/architecture/backend.md.

Graceful shutdown: uvicorn already stops accepting new connections and drains
in-flight requests on SIGTERM before sending the ASGI lifespan shutdown event;
this lifespan handler's job is just to close the DB pool / Redis connection
cleanly once that happens. docs/architecture/backend.md §5 "Graceful shutdown".
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.db import get_engine
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.providers.redis.client import get_redis_client
from app.routes import complaints, health, meta, metrics, stats

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(get_settings().log_level)
    logger.info("startup", triage_provider=get_settings().triage_provider)
    yield
    logger.info("shutdown_draining")
    get_engine().dispose()
    get_redis_client().close()
    logger.info("shutdown_complete")


app = FastAPI(title="CivicPulse API", lifespan=lifespan)

app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)

app.include_router(complaints.router)
app.include_router(stats.router)
app.include_router(meta.router)
app.include_router(health.router)
app.include_router(metrics.router)
