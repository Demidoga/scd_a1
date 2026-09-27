"""GET /api/meta/providers — active provider + recent triage outcomes.
docs/Milestones/milestone-3.md §12.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.complaints import ComplaintRepository


def test_meta_providers_reports_active_provider(client: TestClient) -> None:
    response = client.get("/api/meta/providers")
    assert response.status_code == 200
    assert response.json()["active_provider"] == "simulated"


def test_meta_providers_lists_recent_outcomes(client: TestClient) -> None:
    client.post(
        "/api/complaints",
        json={"text": "Water pipe burst near our house today", "location": "Street 1"},
    )

    response = client.get("/api/meta/providers")
    body = response.json()
    assert len(body["recent_outcomes"]) == 1
    outcome = body["recent_outcomes"][0]
    assert outcome["provider"] == "simulated"
    assert outcome["fallback_used"] is False
    assert isinstance(outcome["latency_ms"], int)


def test_meta_providers_caps_at_20_outcomes(client: TestClient, db_session: Session) -> None:
    # Inserted directly via the repository (bypassing the rate-limited POST
    # endpoint) — this test is about the meta endpoint's cap, not rate limiting.
    repo = ComplaintRepository(db_session)
    for i in range(25):
        repo.create(
            text=f"Complaint number {i} about a road pothole here",
            location="Mall Road",
            reporter_contact=None,
            category="roads",
            priority="normal",
            ai_summary="Pothole",
            triaged_by="simulated",
            triage_latency_ms=1,
        )

    response = client.get("/api/meta/providers")
    assert len(response.json()["recent_outcomes"]) == 20
