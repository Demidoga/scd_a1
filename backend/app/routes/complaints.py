"""HTTP layer for complaint endpoints. Parses/validates input, calls
ComplaintService, serializes responses. No SQL, no business rules here —
see docs/architecture/backend.md §2.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.wiring import get_complaint_service
from app.domain.enums import Category, Priority
from app.domain.enums import Status as ComplaintStatus
from app.domain.schemas import (
    ComplaintCreate,
    ComplaintListResponse,
    ComplaintResponse,
    ComplaintStatusUpdate,
)
from app.repositories.complaints import ComplaintFilters
from app.routes.dependencies import enforce_rate_limit
from app.services.complaints import ComplaintService

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)],
)
def create_complaint(
    payload: ComplaintCreate,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    complaint = service.create(payload)
    return ComplaintResponse.model_validate(complaint)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: uuid.UUID,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    complaint = service.get(complaint_id)
    return ComplaintResponse.model_validate(complaint)


@router.get("", response_model=ComplaintListResponse)
def list_complaints(
    category: Category | None = None,
    priority: Priority | None = None,
    status: ComplaintStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintListResponse:
    filters = ComplaintFilters(
        category=category.value if category else None,
        priority=priority.value if priority else None,
        status=status.value if status else None,
    )
    items, total = service.list_complaints(filters, page, page_size)
    return ComplaintListResponse(
        items=[ComplaintResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: uuid.UUID,
    payload: ComplaintStatusUpdate,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    complaint = service.update_status(complaint_id, payload.status)
    return ComplaintResponse.model_validate(complaint)
