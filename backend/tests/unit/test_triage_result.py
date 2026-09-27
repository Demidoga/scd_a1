"""TriageResult validation boundary — docs/Milestones/milestone-3.md §4.1."""

import pytest
from pydantic import ValidationError

from app.domain.triage import TriageResult

VALID = {
    "category": "water",
    "priority": "high",
    "summary": "Burst pipe near Street 12",
    "confidence": 0.9,
}


def test_valid_result() -> None:
    result = TriageResult.model_validate(VALID)
    assert result.category.value == "water"
    assert result.priority.value == "high"


def test_invalid_category_rejected() -> None:
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**VALID, "category": "not-a-category"})


def test_invalid_priority_rejected() -> None:
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**VALID, "priority": "critical"})


def test_summary_at_max_length_accepted() -> None:
    result = TriageResult.model_validate({**VALID, "summary": "x" * 140})
    assert len(result.summary) == 140


def test_summary_over_max_length_rejected() -> None:
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**VALID, "summary": "x" * 141})


@pytest.mark.parametrize("confidence", [0.0, 1.0, 0.5])
def test_confidence_within_bounds_accepted(confidence: float) -> None:
    result = TriageResult.model_validate({**VALID, "confidence": confidence})
    assert result.confidence == confidence


def test_confidence_below_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**VALID, "confidence": -0.01})


def test_confidence_above_one_rejected() -> None:
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**VALID, "confidence": 1.01})


def test_missing_required_field_rejected() -> None:
    incomplete = {k: v for k, v in VALID.items() if k != "category"}
    with pytest.raises(ValidationError):
        TriageResult.model_validate(incomplete)


def test_malformed_structured_data_rejected() -> None:
    with pytest.raises(ValidationError):
        TriageResult.model_validate("not even a dict")
