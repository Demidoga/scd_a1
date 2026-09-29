"""Triage orchestration: cache lookup -> provider call -> jittered retry on
retryable failure -> RuleBasedTriage fallback -> record. docs/architecture/ai.md §4-5.

Retry-once-then-fallback is a single policy applied to whichever live
provider is configured, not something duplicated inside each provider
class — see app/providers/triage/llm.py's module docstring for why.
"""

import random
import time
from dataclasses import dataclass

from app.core.logging import get_logger
from app.core.metrics import TRIAGE_FALLBACK_COUNT, TRIAGE_LATENCY
from app.domain.triage import TriageResult
from app.providers.redis.cache import TriageCache
from app.providers.triage.base import TriageProvider
from app.providers.triage.errors import TriageProviderError
from app.providers.triage.rules import RuleBasedTriage

logger = get_logger(__name__)

_RETRY_JITTER_MIN_SECONDS = 0.5
_RETRY_JITTER_MAX_SECONDS = 1.5


@dataclass(frozen=True)
class TriageExecution:
    result: TriageResult
    triaged_by: str
    latency_ms: int
    cache_hit: bool


class TriageService:
    def __init__(
        self,
        provider: TriageProvider,
        cache: TriageCache | None = None,
        fallback_provider: TriageProvider | None = None,
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._fallback = fallback_provider or RuleBasedTriage()

    def triage(
        self, text: str, location: str, *, complaint_id_hint: str = "pending"
    ) -> TriageExecution:
        start = time.perf_counter()

        if self._cache is not None:
            cached = self._cache.get(text, location)
            if cached is not None:
                latency_ms = int((time.perf_counter() - start) * 1000)
                return TriageExecution(
                    result=cached.result,
                    triaged_by=cached.triaged_by,
                    latency_ms=latency_ms,
                    cache_hit=True,
                )

        triaged_by = self._provider.name
        try:
            result = self._call_with_one_retry(text, location)
        except TriageProviderError as exc:
            logger.warning(
                "triage_fallback",
                complaint_id=complaint_id_hint,
                provider=self._provider.name,
                error_class=type(exc).__name__,
            )
            TRIAGE_FALLBACK_COUNT.inc()
            result = self._fallback.triage(text, location)
            triaged_by = "rules:fallback"

        latency_ms = int((time.perf_counter() - start) * 1000)
        TRIAGE_LATENCY.labels(provider=triaged_by).observe(latency_ms / 1000)

        if self._cache is not None:
            self._cache.set(text, location, result, triaged_by)

        return TriageExecution(
            result=result, triaged_by=triaged_by, latency_ms=latency_ms, cache_hit=False
        )

    def _call_with_one_retry(self, text: str, location: str) -> TriageResult:
        try:
            return self._provider.triage(text, location)
        except TriageProviderError as exc:
            if not exc.retryable:
                raise
            jitter = random.uniform(_RETRY_JITTER_MIN_SECONDS, _RETRY_JITTER_MAX_SECONDS)
            time.sleep(jitter)
            return self._provider.triage(text, location)  # second failure propagates to caller
