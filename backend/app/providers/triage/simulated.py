"""SimulatedTriage — deterministic, network-free provider used in CI and by
default in local dev (`TRIAGE_PROVIDER=simulated`). docs/architecture/ai.md §7.

Supports failure injection so tests can exercise the retry/fallback pipeline
without a real network dependency: construct with `force_failure=` set to any
TriageProviderError instance and every `triage()` call raises it instead of
returning a result.
"""

from app.domain.triage import TriageResult
from app.providers.triage._classifier import (
    classify_category,
    classify_priority,
    summarize,
)
from app.providers.triage.errors import TriageProviderError

_SIMULATED_CONFIDENCE = 0.75


class SimulatedTriage:
    name = "simulated"

    def __init__(self, force_failure: TriageProviderError | None = None) -> None:
        self._force_failure = force_failure

    def triage(self, text: str, location: str) -> TriageResult:
        if self._force_failure is not None:
            raise self._force_failure

        lowered = text.lower()
        return TriageResult(
            category=classify_category(lowered),
            priority=classify_priority(lowered),
            summary=summarize(text, location),
            confidence=_SIMULATED_CONFIDENCE,
        )
