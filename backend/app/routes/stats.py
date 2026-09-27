"""GET /api/stats — Redis read-through cached aggregate statistics.
docs/architecture/cache.md §1.
"""

from fastapi import APIRouter, Depends, Response

from app.core.wiring import get_complaint_service
from app.domain.schemas import StatsResponse
from app.services.complaints import ComplaintService

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def get_stats(
    response: Response,
    service: ComplaintService = Depends(get_complaint_service),
) -> StatsResponse:
    stats, cache_hit = service.stats()
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return StatsResponse(
        total=stats.total,
        by_status=stats.by_status,
        by_category=stats.by_category,
        by_priority=stats.by_priority,
    )
