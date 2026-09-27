"""Fixtures for tests that need a real PostgreSQL + Redis — scoped to this
directory only (pytest resolves conftest.py per-directory), so unit tests
under tests/unit/ never pay for or require live dependencies.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, get_engine
from app.providers.redis.client import get_redis_client


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> Generator[None, None, None]:
    engine = get_engine()
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_state() -> Generator[None, None, None]:
    """Truncate complaints and flush the test Redis DB (15) before/after every test."""
    get_redis_client().flushdb()
    with get_engine().begin() as conn:
        conn.execute(text("TRUNCATE TABLE complaints"))
    yield
    with get_engine().begin() as conn:
        conn.execute(text("TRUNCATE TABLE complaints"))
    get_redis_client().flushdb()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
