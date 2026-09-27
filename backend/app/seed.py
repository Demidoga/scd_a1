"""Idempotent complaint seed command. docs/architecture/database.md §4.

Usage:
    uv run python -m app.seed

Runs each seed row through the same ComplaintService.create() path a real
POST /api/complaints request uses (so seeded complaints get real triage
results, not hand-picked category/priority values), but skips any row whose
exact (text, location) already exists — safe to run repeatedly.
"""

from app.core.db import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.core.wiring import build_complaint_service
from app.domain.schemas import ComplaintCreate
from app.repositories.complaints import ComplaintRepository
from app.seed_data import SEED_COMPLAINTS

logger = get_logger(__name__)


def run_seed() -> None:
    session = SessionLocal()
    try:
        repository = ComplaintRepository(session)
        service = build_complaint_service(session)

        inserted = 0
        skipped = 0
        for text, location, reporter_contact in SEED_COMPLAINTS:
            if repository.exists_with_text_and_location(text, location):
                skipped += 1
                continue
            service.create(
                ComplaintCreate(text=text, location=location, reporter_contact=reporter_contact)
            )
            inserted += 1

        logger.info("seed_complete", inserted=inserted, skipped=skipped)
        print(f"Seed complete: {inserted} inserted, {skipped} already present (skipped).")
    finally:
        session.close()


if __name__ == "__main__":
    configure_logging()
    run_seed()
