"""Domain enums shared by the API contract, service layer, and persistence model.

These are the single source of truth for CivicPulse's complaint vocabulary.
Serialized values (API JSON, DB columns) are the lowercase strings below —
never rename the *values*, only the Python identifiers, if this ever changes.
"""

from enum import Enum


class Category(str, Enum):
    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    ROADS = "roads"
    STREETLIGHTS = "streetlights"
    OTHER = "other"


class Priority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Status(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class TriagedBy(str, Enum):
    """Controlled marker values for `complaint.triaged_by`.

    Not a DB enum column — stored as text so the value can compose
    (``rules:fallback``) without extending a SQL enum type. Kept here as
    an enum anyway so callers can't typo a provider marker.
    """

    LLM_GROQ = "llm:groq"
    RULES = "rules"
    RULES_FALLBACK = "rules:fallback"
