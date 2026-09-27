"""SQLAlchemy ORM model for the `complaints` table.

Category/priority/status/triaged_by are plain VARCHAR + CHECK constraints
rather than native Postgres ENUM types — a CHECK gives the same value
restriction the schema contract (docs/architecture/database.md §1) asks for,
without native-enum's ALTER-TYPE migration friction if a value is ever added.

`triaged_by` allows `simulated` in addition to the three values database.md
lists (`llm:groq`, `rules`, `rules:fallback`): that doc predates ai.md §0's
instructor-approved 3-provider scope decision, and `TRIAGE_PROVIDER=simulated`
is the CI/dev default, so its rows must be persistable. Noted in
docs/ENGINEERING-NOTES.md as a resolved doc gap, not a silent deviation.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.enums import Category, Priority, Status

_CATEGORY_VALUES = tuple(c.value for c in Category)
_PRIORITY_VALUES = tuple(p.value for p in Priority)
_STATUS_VALUES = tuple(s.value for s in Status)
_TRIAGED_BY_VALUES = ("llm:groq", "rules", "rules:fallback", "simulated")


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()")
    )
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)

    category: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=Status.OPEN.value
    )

    ai_summary: Mapped[str | None] = mapped_column(String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(String(20), nullable=False)
    triage_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
        onupdate=sql_text("now()"),
    )

    __table_args__ = (
        CheckConstraint("char_length(text) BETWEEN 10 AND 2000", name="ck_complaints_text_length"),
        CheckConstraint(
            "char_length(location) BETWEEN 3 AND 200", name="ck_complaints_location_length"
        ),
        CheckConstraint(
            "ai_summary IS NULL OR char_length(ai_summary) <= 140",
            name="ck_complaints_ai_summary_length",
        ),
        CheckConstraint(
            f"category IN {_CATEGORY_VALUES}", name="ck_complaints_category_enum"
        ),
        CheckConstraint(
            f"priority IN {_PRIORITY_VALUES}", name="ck_complaints_priority_enum"
        ),
        CheckConstraint(f"status IN {_STATUS_VALUES}", name="ck_complaints_status_enum"),
        CheckConstraint(
            f"triaged_by IN {_TRIAGED_BY_VALUES}", name="ck_complaints_triaged_by_enum"
        ),
        CheckConstraint("triage_latency_ms >= 0", name="ck_complaints_triage_latency_nonneg"),
        Index("ix_complaints_status_priority", "status", "priority"),
        Index("ix_complaints_created_at", "created_at"),
    )
