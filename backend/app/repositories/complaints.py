"""All SQL access for complaints lives here — the only layer allowed to
import sqlalchemy query constructs. docs/architecture/backend.md §2.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.repositories.models import Complaint


@dataclass(frozen=True)
class ComplaintFilters:
    category: str | None = None
    priority: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class ComplaintStats:
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_priority: dict[str, int]


class ComplaintRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        text: str,
        location: str,
        reporter_contact: str | None,
        category: str,
        priority: str,
        ai_summary: str | None,
        triaged_by: str,
        triage_latency_ms: int,
        id: uuid.UUID | None = None,
    ) -> Complaint:
        complaint = Complaint(
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=category,
            priority=priority,
            ai_summary=ai_summary,
            triaged_by=triaged_by,
            triage_latency_ms=triage_latency_ms,
        )
        if id is not None:
            complaint.id = id
        self._session.add(complaint)
        self._session.commit()
        self._session.refresh(complaint)
        return complaint

    def get_by_id(self, complaint_id: uuid.UUID) -> Complaint | None:
        return self._session.get(Complaint, complaint_id)

    def exists_with_text_and_location(self, text: str, location: str) -> bool:
        """Used by the idempotent seed script (app/seed.py) to skip rows it
        already inserted on a previous run, without relying on a separate
        "is this a seed row" marker column.
        """
        stmt = select(Complaint.id).where(
            Complaint.text == text, Complaint.location == location
        )
        return self._session.execute(stmt).first() is not None

    def list_complaints(
        self, filters: ComplaintFilters, page: int, page_size: int
    ) -> tuple[list[Complaint], int]:
        stmt = select(Complaint)
        count_stmt = select(func.count()).select_from(Complaint)

        if filters.category:
            stmt = stmt.where(Complaint.category == filters.category)
            count_stmt = count_stmt.where(Complaint.category == filters.category)
        if filters.priority:
            stmt = stmt.where(Complaint.priority == filters.priority)
            count_stmt = count_stmt.where(Complaint.priority == filters.priority)
        if filters.status:
            stmt = stmt.where(Complaint.status == filters.status)
            count_stmt = count_stmt.where(Complaint.status == filters.status)

        total = self._session.execute(count_stmt).scalar_one()

        stmt = (
            stmt.order_by(Complaint.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self._session.execute(stmt).scalars().all())
        return items, total

    def update_status(self, complaint: Complaint, new_status: str) -> Complaint:
        complaint.status = new_status
        self._session.commit()
        self._session.refresh(complaint)
        return complaint

    def recent(self, limit: int = 20) -> list[Complaint]:
        stmt = select(Complaint).order_by(Complaint.created_at.desc()).limit(limit)
        return list(self._session.execute(stmt).scalars().all())

    def aggregate_stats(self) -> ComplaintStats:
        def _counts_by(column) -> dict[str, int]:
            stmt = select(column, func.count()).group_by(column)
            return {value: count for value, count in self._session.execute(stmt).all()}

        total = self._session.execute(select(func.count()).select_from(Complaint)).scalar_one()
        return ComplaintStats(
            total=total,
            by_status=_counts_by(Complaint.status),
            by_category=_counts_by(Complaint.category),
            by_priority=_counts_by(Complaint.priority),
        )
