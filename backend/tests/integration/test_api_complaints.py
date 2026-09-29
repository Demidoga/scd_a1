"""POST/GET/PATCH /api/complaints through the real HTTP stack (TestClient),
against real PostgreSQL + Redis with TRIAGE_PROVIDER=simulated.
docs/Milestones/milestone-2.md §21.1 "API".
"""

from fastapi.testclient import TestClient

VALID_PAYLOAD = {
    "text": "Water pipe burst near our house, flooding the street badly",
    "location": "Street 12, G-9/1, Islamabad",
}


def test_create_complaint_returns_201_with_triage_fields(client: TestClient) -> None:
    response = client.post("/api/complaints", json=VALID_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open"
    assert body["category"] in {
        "water",
        "electricity",
        "sanitation",
        "roads",
        "streetlights",
        "other",
    }
    assert body["priority"] in {"high", "normal", "low"}
    assert body["triaged_by"]
    assert isinstance(body["triage_latency_ms"], int)


def test_create_complaint_rejects_short_text_with_400(client: TestClient) -> None:
    response = client.post("/api/complaints", json={"text": "too short", "location": "Street 1"})
    assert response.status_code == 400
    body = response.json()
    assert body["errors"]
    assert any(e["field"] == "text" for e in body["errors"])


def test_create_complaint_rejects_short_location_with_400(client: TestClient) -> None:
    response = client.post(
        "/api/complaints", json={"text": VALID_PAYLOAD["text"], "location": "NY"}
    )
    assert response.status_code == 400


def test_create_complaint_does_not_trust_client_supplied_triage_fields(client: TestClient) -> None:
    response = client.post(
        "/api/complaints",
        json={**VALID_PAYLOAD, "category": "roads", "status": "resolved", "triaged_by": "hacker"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open"  # client-supplied status ignored, not "resolved"


def test_get_complaint_by_id(client: TestClient) -> None:
    created = client.post("/api/complaints", json=VALID_PAYLOAD).json()
    response = client.get(f"/api/complaints/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_complaint_returns_404(client: TestClient) -> None:
    response = client.get("/api/complaints/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_complaints_returns_total_and_pagination(client: TestClient) -> None:
    for i in range(3):
        client.post(
            "/api/complaints",
            json={
                "text": f"Complaint number {i} about a water leak here",
                "location": f"Street {i}",
            },
        )

    response = client.get("/api/complaints", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2


def test_list_complaints_page_size_over_100_rejected(client: TestClient) -> None:
    response = client.get("/api/complaints", params={"page_size": 101})
    assert response.status_code == 400


def test_list_complaints_filters_by_status(client: TestClient) -> None:
    created = client.post("/api/complaints", json=VALID_PAYLOAD).json()
    client.patch(f"/api/complaints/{created['id']}/status", json={"status": "in_progress"})

    response = client.get("/api/complaints", params={"status": "in_progress"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == created["id"]


def test_valid_status_transition_returns_200(client: TestClient) -> None:
    created = client.post("/api/complaints", json=VALID_PAYLOAD).json()
    response = client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_response_lists_allowed_transitions_for_each_status(client: TestClient) -> None:
    created = client.post("/api/complaints", json=VALID_PAYLOAD).json()
    assert created["allowed_transitions"] == ["in_progress", "rejected"]

    in_progress = client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "in_progress"}
    ).json()
    assert in_progress["allowed_transitions"] == ["resolved", "rejected"]

    resolved = client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "resolved"}
    ).json()
    assert resolved["allowed_transitions"] == []


def test_invalid_status_transition_returns_409_naming_attempt(client: TestClient) -> None:
    created = client.post("/api/complaints", json=VALID_PAYLOAD).json()
    # open -> resolved is not allowed (must go through in_progress first)
    response = client.patch(f"/api/complaints/{created['id']}/status", json={"status": "resolved"})
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "open" in detail
    assert "resolved" in detail


def test_terminal_status_rejects_further_transitions(client: TestClient) -> None:
    created = client.post("/api/complaints", json=VALID_PAYLOAD).json()
    client.patch(f"/api/complaints/{created['id']}/status", json={"status": "rejected"})

    response = client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "in_progress"}
    )
    assert response.status_code == 409


def test_status_update_on_missing_complaint_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/complaints/00000000-0000-0000-0000-000000000000/status",
        json={"status": "in_progress"},
    )
    assert response.status_code == 404
