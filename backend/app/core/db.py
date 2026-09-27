"""SQLAlchemy engine/session wiring.

Sync engine + sync sessions on purpose: FastAPI runs `def` (non-async) route
handlers in a threadpool automatically, so a blocking DB call here doesn't
block the event loop, and it keeps Alembic/session code simple (no async
driver, no greenlet). See docs/architecture/database.md.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def get_engine():
    return _engine


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a session, closes it after the request.

    Routes depend on this only to obtain a session to hand to a service
    function — they must not issue queries against it themselves.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
