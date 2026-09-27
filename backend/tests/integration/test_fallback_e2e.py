"""The mandatory fallback test: a provider that always raises still yields a
201 with triaged_by == "rules:fallback". docs/architecture/testing.md §2,
docs/Milestones/milestone-3.md §22.3.
"""

from fastapi.testclient import TestClient

from app.core.wiring import get_triage_provider
from app.main import app
from app.providers.triage.errors import TriageTimeoutError
from app.providers.triage.simulated import SimulatedTriage


def test_provider_always_raises_still_returns_201_with_rules_fallback(client: TestClient) -> None:
    always_failing = SimulatedTriage(force_failure=TriageTimeoutError("simulated outage"))
    app.dependency_overrides[get_triage_provider] = lambda: always_failing
    try:
        response = client.post(
            "/api/complaints",
            json={
                "text": "Water pipe burst near our house, flooding badly",
                "location": "Street 12, G-9/1, Islamabad",
            },
        )
    finally:
        app.dependency_overrides.pop(get_triage_provider, None)

    assert response.status_code == 201
    body = response.json()
    assert body["triaged_by"] == "rules:fallback"
    # The persisted result must still be a schema-valid classification.
    assert body["category"] in {
        "water",
        "electricity",
        "sanitation",
        "roads",
        "streetlights",
        "other",
    }
    assert body["priority"] in {"high", "normal", "low"}
