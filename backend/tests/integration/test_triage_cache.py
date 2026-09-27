"""Redis content-hash triage cache against real Redis. docs/architecture/ai.md
§"Content-hash cache", docs/Milestones/milestone-3.md §22.5.

Tested at the TriageService+TriageCache level (not through the HTTP API)
because proving "no second inference call" requires a call-counting provider,
and the API's active provider is a fixed process-wide singleton.
"""

from app.domain.triage import TriageResult
from app.providers.redis.cache import TriageCache
from app.providers.redis.client import get_redis_client
from app.providers.triage.simulated import SimulatedTriage
from app.services.triage import TriageService


class _CountingSimulated:
    name = "simulated"

    def __init__(self) -> None:
        self.call_count = 0
        self._inner = SimulatedTriage()

    def triage(self, text: str, location: str) -> TriageResult:
        self.call_count += 1
        return self._inner.triage(text, location)


def _service() -> tuple[TriageService, _CountingSimulated]:
    cache = TriageCache(get_redis_client(), ttl_seconds=86400)
    provider = _CountingSimulated()
    return TriageService(provider=provider, cache=cache), provider


def test_first_call_is_cache_miss_and_calls_provider() -> None:
    service, provider = _service()
    execution = service.triage("Garbage not collected for a week now", "Block 5")
    assert execution.cache_hit is False
    assert provider.call_count == 1


def test_repeated_identical_input_hits_cache_and_skips_provider() -> None:
    service, provider = _service()
    first = service.triage("Streetlight has not worked in weeks", "Sector F-8")
    second = service.triage("Streetlight has not worked in weeks", "Sector F-8")

    assert provider.call_count == 1  # provider only called once, second was a cache hit
    assert second.cache_hit is True
    assert second.result == first.result


def test_different_location_is_a_different_cache_key() -> None:
    service, provider = _service()
    service.triage("Same complaint text used for both requests", "Location A")
    service.triage("Same complaint text used for both requests", "Location B")

    assert provider.call_count == 2  # different location -> different content hash -> no hit


def test_cached_result_is_schema_valid() -> None:
    service, _ = _service()
    service.triage("Road has a large dangerous pothole", "Mall Road")
    second = service.triage("Road has a large dangerous pothole", "Mall Road")

    assert isinstance(second.result, TriageResult)
