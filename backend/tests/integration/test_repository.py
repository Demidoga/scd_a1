"""ComplaintRepository against a real PostgreSQL test database.
docs/Milestones/milestone-2.md §21.1.
"""

import uuid

from sqlalchemy.orm import Session

from app.repositories.complaints import ComplaintFilters, ComplaintRepository
from app.repositories.models import Complaint


def _create(repo: ComplaintRepository, **overrides: object) -> Complaint:
    defaults = {
        "text": "Water pipe burst near the main road, please fix urgently",
        "location": "Street 12, G-9",
        "reporter_contact": None,
        "category": "water",
        "priority": "high",
        "ai_summary": "Burst water pipe",
        "triaged_by": "simulated",
        "triage_latency_ms": 5,
    }
    defaults.update(overrides)
    return repo.create(**defaults)  # type: ignore[arg-type]


def test_create_and_get_by_id(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    created = _create(repo)

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.category == "water"


def test_get_by_id_missing_returns_none(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    assert repo.get_by_id(uuid.uuid4()) is None


def test_list_filters_by_category(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    _create(repo, category="water")
    _create(
        repo, category="roads", text="Big pothole on the main street here", location="Mall Road"
    )

    items, total = repo.list_complaints(ComplaintFilters(category="water"), page=1, page_size=10)
    assert total == 1
    assert all(item.category == "water" for item in items)


def test_list_filters_by_priority(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    _create(repo, priority="high")
    _create(repo, priority="low", text="Minor cosmetic issue with the park bench paint")

    items, total = repo.list_complaints(ComplaintFilters(priority="low"), page=1, page_size=10)
    assert total == 1
    assert items[0].priority == "low"


def test_list_filters_by_status(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    created = _create(repo)
    repo.update_status(created, "in_progress")
    _create(repo, text="A second, unrelated complaint about roads here", location="Mall Road")

    items, total = repo.list_complaints(
        ComplaintFilters(status="in_progress"), page=1, page_size=10
    )
    assert total == 1
    assert items[0].status == "in_progress"


def test_pagination_and_total_count(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    for i in range(5):
        _create(repo, text=f"Complaint number {i} about a water leak issue", location=f"Street {i}")

    page1, total = repo.list_complaints(ComplaintFilters(), page=1, page_size=2)
    page2, _ = repo.list_complaints(ComplaintFilters(), page=2, page_size=2)

    assert total == 5
    assert len(page1) == 2
    assert len(page2) == 2
    assert {c.id for c in page1}.isdisjoint({c.id for c in page2})


def test_update_status_persists(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    created = _create(repo)

    updated = repo.update_status(created, "resolved")
    assert updated.status == "resolved"

    refetched = repo.get_by_id(created.id)
    assert refetched is not None
    assert refetched.status == "resolved"


def test_exists_with_text_and_location(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    _create(repo, text="A very specific unique complaint text goes here", location="Unique Street")

    assert repo.exists_with_text_and_location(
        "A very specific unique complaint text goes here", "Unique Street"
    )
    assert not repo.exists_with_text_and_location("Something else entirely", "Unique Street")


def test_aggregate_stats(db_session: Session) -> None:
    repo = ComplaintRepository(db_session)
    _create(repo, category="water", priority="high")
    _create(repo, category="roads", priority="low", text="Pothole complaint text goes here please")

    stats = repo.aggregate_stats()
    assert stats.total == 2
    assert stats.by_category["water"] == 1
    assert stats.by_category["roads"] == 1
    assert stats.by_priority["high"] == 1
    assert stats.by_priority["low"] == 1
