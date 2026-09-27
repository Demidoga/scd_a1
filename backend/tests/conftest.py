"""Test environment setup, shared by unit and integration tests.

Sets DATABASE_URL/REDIS_URL/TRIAGE_PROVIDER to test-safe values *before*
anything under app/ is imported — app.core.db creates its engine at import
time, so these env vars must land first. This is why they're set here, at
module level, rather than inside a fixture.

DB/Redis-touching autouse fixtures (schema creation, per-test cleanup) live
in tests/integration/conftest.py instead of here, so unit tests never need
a live PostgreSQL/Redis to run.
"""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://civicpulse:civicpulse@localhost:5432/civicpulse_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("TRIAGE_PROVIDER", "simulated")
