"""GET /api/meta/providers — active triage provider + last 20 outcomes.
docs/architecture/ai.md §"Provider Observability".

Recent outcomes are derived from the complaints table itself (most recent
rows) rather than a separate in-memory ring buffer — PostgreSQL is the sole
source of truth (docs/architecture/database.md §6), and an in-process buffer
wouldn't be shared across horizontally-scaled backend replicas anyway.
"""

from fastapi import APIRouter, Depends

from app.core.wiring import get_complaint_service, get_triage_provider
from app.domain.schemas import ProvidersMetaResponse, TriageOutcome
from app.providers.triage.base import TriageProvider
from app.services.complaints import ComplaintService

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/providers", response_model=ProvidersMetaResponse)
def get_providers_meta(
    service: ComplaintService = Depends(get_complaint_service),
    provider: TriageProvider = Depends(get_triage_provider),
) -> ProvidersMetaResponse:
    recent = service.recent_for_meta(limit=20)
    outcomes = [
        TriageOutcome(
            complaint_id=c.id,
            provider=c.triaged_by,
            latency_ms=c.triage_latency_ms,
            fallback_used=c.triaged_by == "rules:fallback",
            created_at=c.created_at,
        )
        for c in recent
    ]
    return ProvidersMetaResponse(active_provider=provider.name, recent_outcomes=outcomes)
