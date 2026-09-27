"""Triage provider failure taxonomy.

Retry policy (docs/architecture/ai.md §5) is fixed by exception *type*, not by
inspecting strings, so the service layer's retry logic is a simple lookup.
"""


class TriageProviderError(Exception):
    """Base class for all provider failures. Not retryable by default."""

    retryable: bool = False


class TriageTimeoutError(TriageProviderError):
    retryable = True


class TriageRateLimitError(TriageProviderError):
    """HTTP 429 from the provider."""

    retryable = True


class TriageServerError(TriageProviderError):
    """HTTP 5xx from the provider."""

    retryable = True


class TriageBadRequestError(TriageProviderError):
    """HTTP 400 from the provider — the request itself was invalid. Never retried."""

    retryable = False


class TriageMalformedOutputError(TriageProviderError):
    """Provider responded, but the payload failed TriageResult validation.

    Not retried — a second call with the same input is unlikely to fix a
    schema mismatch. Goes straight to the RuleBasedTriage fallback.
    """

    retryable = False
