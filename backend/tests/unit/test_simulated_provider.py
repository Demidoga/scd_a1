"""SimulatedTriage — deterministic, network-free, supports failure injection.
docs/Milestones/milestone-3.md §6.4.
"""

import pytest

from app.domain.triage import TriageResult
from app.providers.triage.errors import TriageTimeoutError
from app.providers.triage.simulated import SimulatedTriage


def test_deterministic_result() -> None:
    provider = SimulatedTriage()
    first = provider.triage("Garbage not collected for a week", "Block 5")
    second = provider.triage("Garbage not collected for a week", "Block 5")
    assert first == second
    assert isinstance(first, TriageResult)


def test_force_failure_raises_configured_error() -> None:
    provider = SimulatedTriage(force_failure=TriageTimeoutError("boom"))
    with pytest.raises(TriageTimeoutError):
        provider.triage("Anything", "Anywhere")


def test_default_provider_never_raises() -> None:
    provider = SimulatedTriage()
    result = provider.triage("Road has a large pothole", "Mall Road")
    assert isinstance(result, TriageResult)
