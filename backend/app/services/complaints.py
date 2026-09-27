"""Complaint business rules: creation orchestration, retrieval, listing, and
status-transition enforcement. Routes call this; this calls repositories and
the triage/cache providers. docs/architecture/backend.md §2.
"""

import uuid

from app.core.errors import ComplaintNotFoundError, InvalidTransitionError
from app.domain.enums import Status
from app.domain.schemas import ComplaintCreate
from app.domain.transitions import is_transition_allowed
from app.providers.redis.cache import StatsCache
from app.repositories.complaints import ComplaintFilters, ComplaintRepository, ComplaintStats
from app.repositories.models import Complaint
from app.services.triage import TriageService


class ComplaintService:
    def __init__(
        self,
        repository: ComplaintRepository,
        triage_service: TriageService,
        stats_cache: StatsCache,
    ) -> None:
        self._repository = repository
        self._triage_service = triage_service
        self._stats_cache = stats_cache

    def create(self, payload: ComplaintCreate) -> Complaint:
        complaint_id = uuid.uuid4()
        execution = self._triage_service.triage(
            payload.text, payload.location, complaint_id_hint=str(complaint_id)
        )
        complaint = self._repository.create(
            id=complaint_id,
            text=payload.text,
            location=payload.location,
            reporter_contact=payload.reporter_contact,
            category=execution.result.category.value,
            priority=execution.result.priority.value,
            ai_summary=execution.result.summary,
            triaged_by=execution.triaged_by,
            triage_latency_ms=execution.latency_ms,
        )
        self._stats_cache.invalidate()
        return complaint

    def get(self, complaint_id: uuid.UUID) -> Complaint:
        complaint = self._repository.get_by_id(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(complaint_id)
        return complaint

    def list_complaints(
        self, filters: ComplaintFilters, page: int, page_size: int
    ) -> tuple[list[Complaint], int]:
        return self._repository.list_complaints(filters, page, page_size)

    def update_status(self, complaint_id: uuid.UUID, target: Status) -> Complaint:
        complaint = self.get(complaint_id)
        current = Status(complaint.status)
        if not is_transition_allowed(current, target):
            raise InvalidTransitionError(current, target)
        updated = self._repository.update_status(complaint, target.value)
        self._stats_cache.invalidate()
        return updated

    def recent_for_meta(self, limit: int = 20) -> list[Complaint]:
        return self._repository.recent(limit)

    def stats(self) -> tuple[ComplaintStats, bool]:
        """Returns (stats, cache_hit)."""
        cached = self._stats_cache.get()
        if cached is not None:
            return cached, True
        computed = self._repository.aggregate_stats()
        self._stats_cache.set(computed)
        return computed, False
