"""`TriageProvider` — the interface the rest of the application depends on
instead of a vendor SDK. See docs/architecture/ai.md §1 and ADR 0001.

Three implementations exist: LLMTriage (llm.py), RuleBasedTriage (rules.py),
SimulatedTriage (simulated.py). All are selected via factory.py based on the
TRIAGE_PROVIDER environment variable. No provider-specific types may leak
past this interface into app/services or app/routes.
"""

from typing import Protocol

from app.domain.triage import TriageResult


class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult:
        """Classify a complaint. Raises on failure — callers handle retry/fallback."""
        ...
