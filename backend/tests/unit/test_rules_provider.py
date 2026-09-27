"""RuleBasedTriage — deterministic classification. docs/architecture/ai.md."""

from app.domain.enums import Category, Priority
from app.providers.triage.rules import RuleBasedTriage


def test_deterministic_for_same_input() -> None:
    provider = RuleBasedTriage()
    first = provider.triage("Water pipe burst near house", "Street 1")
    second = provider.triage("Water pipe burst near house", "Street 1")
    assert first == second


def test_classifies_water_keywords() -> None:
    result = RuleBasedTriage().triage(
        "Water pipeline is leaking badly outside our house", "Sector G-9"
    )
    assert result.category == Category.WATER


def test_classifies_electricity_keywords() -> None:
    result = RuleBasedTriage().triage(
        "Transformer is sparking and there is a power cut", "Model Town"
    )
    assert result.category == Category.ELECTRICITY


def test_classifies_streetlights_keywords() -> None:
    result = RuleBasedTriage().triage("The streetlight has not worked in weeks", "F-8 Markaz")
    assert result.category == Category.STREETLIGHTS


def test_unrecognized_text_falls_back_to_other() -> None:
    result = RuleBasedTriage().triage("The community noticeboard needs new paint", "Block 5")
    assert result.category == Category.OTHER


def test_urgent_keyword_yields_high_priority() -> None:
    result = RuleBasedTriage().triage("This is an emergency, house is flooding", "Street 3")
    assert result.priority == Priority.HIGH


def test_summary_is_never_longer_than_140_chars() -> None:
    long_text = "This complaint text repeats. " * 20
    result = RuleBasedTriage().triage(long_text, "Street 9")
    assert len(result.summary) <= 140
