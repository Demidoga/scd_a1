"""Triage orchestration: retry-once-then-fallback. docs/architecture/ai.md §5."""

import time

import pytest

from app.domain.triage import TriageResult
from app.providers.triage.errors import (
    TriageBadRequestError,
    TriageMalformedOutputError,
    TriageRateLimitError,
    TriageServerError,
    TriageTimeoutError,
)
from app.providers.triage.simulated import SimulatedTriage
from app.services.triage import TriageService


class _CountingProvider:
    """Wraps a real provider but counts calls and can fail N times before
    succeeding, so tests can assert exact retry counts."""

    name = "counting"

    def __init__(self, fail_times: int, error: Exception, then: SimulatedTriage) -> None:
        self._fail_times = fail_times
        self._error = error
        self._then = then
        self.call_count = 0

    def triage(self, text: str, location: str) -> TriageResult:
        self.call_count += 1
        if self.call_count <= self._fail_times:
            raise self._error
        return self._then.triage(text, location)


def test_success_uses_provider_name_as_triaged_by() -> None:
    service = TriageService(provider=SimulatedTriage(), cache=None)
    execution = service.triage("Water pipe burst", "Street 1")
    assert execution.triaged_by == "simulated"
    assert execution.cache_hit is False


@pytest.mark.parametrize(
    "error",
    [
        TriageTimeoutError("timeout"),
        TriageRateLimitError("429"),
        TriageServerError("500"),
    ],
)
def test_retryable_failure_is_retried_once_then_succeeds(error: Exception, monkeypatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    provider = _CountingProvider(fail_times=1, error=error, then=SimulatedTriage())
    service = TriageService(provider=provider, cache=None)

    execution = service.triage("Streetlight not working", "Block 5")

    assert provider.call_count == 2  # one failure + one retry
    assert execution.triaged_by == provider.name  # succeeded via the active provider, not fallback


@pytest.mark.parametrize(
    "error",
    [
        TriageTimeoutError("timeout"),
        TriageRateLimitError("429"),
        TriageServerError("500"),
    ],
)
def test_retryable_failure_twice_falls_back(error: Exception, monkeypatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    provider = _CountingProvider(fail_times=99, error=error, then=SimulatedTriage())
    service = TriageService(provider=provider, cache=None)

    execution = service.triage("Sewerage overflowing badly", "Street 9")

    assert provider.call_count == 2  # initial attempt + exactly one retry, no more
    assert execution.triaged_by == "rules:fallback"


@pytest.mark.parametrize(
    "error", [TriageBadRequestError("400"), TriageMalformedOutputError("bad json")]
)
def test_non_retryable_failure_falls_back_without_retry(error: Exception) -> None:
    provider = _CountingProvider(fail_times=99, error=error, then=SimulatedTriage())
    service = TriageService(provider=provider, cache=None)

    execution = service.triage("Garbage piling up on the street", "Block 2")

    assert provider.call_count == 1  # no retry for non-retryable errors
    assert execution.triaged_by == "rules:fallback"


def test_provider_always_raises_still_returns_valid_fallback_result() -> None:
    provider = SimulatedTriage(force_failure=TriageTimeoutError("always fails"))
    service = TriageService(provider=provider, cache=None)

    execution = service.triage("Road full of potholes near the market", "Mall Road")

    assert execution.triaged_by == "rules:fallback"
    assert execution.result is not None
