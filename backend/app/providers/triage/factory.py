"""Provider factory: TRIAGE_PROVIDER (config) -> concrete TriageProvider.

The service layer depends on this, never on a specific provider class, so
vendor construction details stay out of app/services. docs/architecture/ai.md §3.
"""

from app.core.config import Settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


class UnknownTriageProviderError(ValueError):
    pass


def create_triage_provider(settings: Settings) -> TriageProvider:
    match settings.triage_provider:
        case "llm":
            if not settings.llm_api_key:
                raise ValueError(
                    "TRIAGE_PROVIDER=llm requires LLM_API_KEY to be set"
                )
            return LLMTriage(api_key=settings.llm_api_key, model=settings.llm_model)
        case "rules":
            return RuleBasedTriage()
        case "simulated":
            return SimulatedTriage()
        case other:
            raise UnknownTriageProviderError(f"Unknown TRIAGE_PROVIDER: {other!r}")
