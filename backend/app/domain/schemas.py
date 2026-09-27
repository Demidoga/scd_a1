"""Pydantic request/response models — the API contract's shape.

These are distinct from `app.repositories.models.Complaint` (the ORM/table
mapping) on purpose: the API contract and the storage schema are allowed to
evolve independently. docs/Milestones/milestone-1.md §B/§C.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import Category, Priority, Status


class ComplaintCreate(BaseModel):
    """Client-supplied input for POST /api/complaints.

    Triage-derived fields (category, priority, ai_summary, triaged_by,
    triage_latency_ms) are NOT accepted here — they are backend-owned and
    computed by the triage pipeline, never trusted from the client.
    """

    text: str = Field(min_length=10, max_length=2000)
    location: str = Field(min_length=3, max_length=200)
    reporter_contact: str | None = Field(default=None, max_length=200)


class ComplaintStatusUpdate(BaseModel):
    status: Status


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintListResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int


class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    """Shared error envelope for 400/404/409/503 responses.

    `errors` carries field-level detail (validation failures); `detail` is a
    single human-readable message for non-field errors (404/409/503/etc).
    """

    detail: str
    errors: list[FieldError] | None = None


class StatsResponse(BaseModel):
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_priority: dict[str, int]


class TriageOutcome(BaseModel):
    complaint_id: uuid.UUID
    provider: str
    latency_ms: int
    fallback_used: bool
    created_at: datetime


class ProvidersMetaResponse(BaseModel):
    active_provider: str
    recent_outcomes: list[TriageOutcome]
