"""RuleBasedTriage — deterministic keyword classifier.

Two jobs: (1) the CI/offline-friendly `TRIAGE_PROVIDER=rules` path, and
(2) the mandatory fallback when LLMTriage fails (docs/architecture/ai.md §5).
Because it's the fallback, it must never itself raise for well-formed input —
every complaint has to get *some* deterministic classification.
"""

from app.domain.triage import TriageResult
from app.providers.triage._classifier import (
    classify_category,
    classify_priority,
    summarize,
)

_DETERMINISTIC_CONFIDENCE = 0.55


class RuleBasedTriage:
    name = "rules"

    def triage(self, text: str, location: str) -> TriageResult:
        lowered = text.lower()
        return TriageResult(
            category=classify_category(lowered),
            priority=classify_priority(lowered),
            summary=summarize(text, location),
            confidence=_DETERMINISTIC_CONFIDENCE,
        )
