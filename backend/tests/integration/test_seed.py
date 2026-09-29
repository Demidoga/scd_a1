"""The seed command must be idempotent: a second run inserts nothing.
docs/architecture/database.md §4, assignment rubric D ("running it twice
changes nothing").
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.repositories.models import Complaint
from app.seed import run_seed
from app.seed_data import SEED_COMPLAINTS


def _row_count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Complaint)) or 0


def test_seed_inserts_at_least_thirty_rows(db_session: Session) -> None:
    run_seed()
    db_session.expire_all()
    assert _row_count(db_session) == len(SEED_COMPLAINTS)
    assert _row_count(db_session) >= 30


def test_seed_twice_does_not_duplicate(db_session: Session) -> None:
    run_seed()
    db_session.expire_all()
    after_first = _row_count(db_session)

    run_seed()
    db_session.expire_all()
    assert _row_count(db_session) == after_first
