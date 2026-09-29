"""Provider factory: TRIAGE_PROVIDER (config) -> concrete TriageProvider.

The service layer depends on this, never on a specific provider class, so
vendor construction details stay out of app/services. docs/architecture/ai.md §3.
"""

from app.core.config import Settings
from app.core.logging import get_logger
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage

logger = get_logger(__name__)


class UnknownTriageProviderError(ValueError):
    pass


def create_triage_provider(settings: Settings) -> TriageProvider:
    match settings.triage_provider:
        case "llm":
            if not settings.llm_api_key:
                # The AI API is the first choice, but a missing key must not stop
                # the app from starting: degrade to rules and say so loudly.
                logger.warning("llm_api_key_missing_using_rules")
                return RuleBasedTriage()
            return LLMTriage(api_key=settings.llm_api_key, model=settings.llm_model)
        case "rules":
            return RuleBasedTriage()
        case "simulated":
            return SimulatedTriage()
        case other:
            raise UnknownTriageProviderError(f"Unknown TRIAGE_PROVIDER: {other!r}")
