"""`TriageResult` — the validation boundary between an untrusted/probabilistic
triage provider response and trusted application data.

Every `TriageProvider` implementation (see app/providers/triage/) must return
one of these, and every caller must construct one through Pydantic validation
rather than trusting raw provider output. See docs/architecture/ai.md §2.
"""

from pydantic import BaseModel, Field

from app.domain.enums import Category, Priority


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)
