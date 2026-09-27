"""create complaints table

Revision ID: 0001
Revises:
Create Date: 2026-09-27

Indexes: (status, priority) supports the operations dashboard's status/
priority filter queries; created_at supports the default created_at DESC
listing order and recent-record access. docs/architecture/database.md §3.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("text", sa.String(length=2000), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("reporter_contact", sa.String(length=200), nullable=True),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("ai_summary", sa.String(length=140), nullable=True),
        sa.Column("triaged_by", sa.String(length=20), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "char_length(text) BETWEEN 10 AND 2000", name="ck_complaints_text_length"
        ),
        sa.CheckConstraint(
            "char_length(location) BETWEEN 3 AND 200", name="ck_complaints_location_length"
        ),
        sa.CheckConstraint(
            "ai_summary IS NULL OR char_length(ai_summary) <= 140",
            name="ck_complaints_ai_summary_length",
        ),
        sa.CheckConstraint(
            "category IN ('water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other')",
            name="ck_complaints_category_enum",
        ),
        sa.CheckConstraint(
            "priority IN ('high', 'normal', 'low')", name="ck_complaints_priority_enum"
        ),
        sa.CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'rejected')",
            name="ck_complaints_status_enum",
        ),
        sa.CheckConstraint(
            "triaged_by IN ('llm:groq', 'rules', 'rules:fallback', 'simulated')",
            name="ck_complaints_triaged_by_enum",
        ),
        sa.CheckConstraint(
            "triage_latency_ms >= 0", name="ck_complaints_triage_latency_nonneg"
        ),
    )
    op.create_index(
        "ix_complaints_status_priority", "complaints", ["status", "priority"]
    )
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_complaints_created_at", table_name="complaints")
    op.drop_index("ix_complaints_status_priority", table_name="complaints")
    op.drop_table("complaints")
