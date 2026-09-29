"""Provider factory: TRIAGE_PROVIDER -> concrete provider. docs/architecture/ai.md §3."""

import pytest

from app.core.config import Settings
from app.providers.triage.factory import UnknownTriageProviderError, create_triage_provider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def _settings(**overrides: object) -> Settings:
    return Settings(**overrides)  # type: ignore[arg-type]


def test_rules_provider_selected() -> None:
    provider = create_triage_provider(_settings(triage_provider="rules"))
    assert isinstance(provider, RuleBasedTriage)


def test_simulated_provider_selected() -> None:
    provider = create_triage_provider(_settings(triage_provider="simulated"))
    assert isinstance(provider, SimulatedTriage)


def test_llm_provider_selected_when_key_present() -> None:
    provider = create_triage_provider(_settings(triage_provider="llm", llm_api_key="k"))
    assert isinstance(provider, LLMTriage)


def test_llm_without_api_key_degrades_to_rules_instead_of_crashing() -> None:
    provider = create_triage_provider(_settings(triage_provider="llm", llm_api_key=""))
    assert isinstance(provider, RuleBasedTriage)


def test_unknown_provider_rejected() -> None:
    settings = _settings(triage_provider="simulated")
    # Bypass the Literal type check to exercise the factory's own guard —
    # in practice an invalid TRIAGE_PROVIDER env value fails Settings
    # construction first, but the factory's `case other` branch is still
    # real defensive code worth covering directly.
    settings.triage_provider = "not-a-real-provider"  # type: ignore[assignment]
    with pytest.raises(UnknownTriageProviderError):
        create_triage_provider(settings)
