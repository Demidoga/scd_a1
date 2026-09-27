"""Retry classification is fixed by exception type. docs/architecture/ai.md §5."""

import pytest

from app.providers.triage.errors import (
    TriageBadRequestError,
    TriageMalformedOutputError,
    TriageRateLimitError,
    TriageServerError,
    TriageTimeoutError,
)


@pytest.mark.parametrize("error_cls", [TriageTimeoutError, TriageRateLimitError, TriageServerError])
def test_retryable_errors(error_cls: type[Exception]) -> None:
    assert error_cls("x").retryable is True


@pytest.mark.parametrize("error_cls", [TriageBadRequestError, TriageMalformedOutputError])
def test_non_retryable_errors(error_cls: type[Exception]) -> None:
    assert error_cls("x").retryable is False
