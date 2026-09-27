"""GET /api/stats read-through Redis cache: MISS -> HIT -> invalidate on write.
docs/Milestones/milestone-3.md §22.6.
"""

from fastapi.testclient import TestClient


def test_first_request_is_miss_second_is_hit(client: TestClient) -> None:
    first = client.get("/api/stats")
    assert first.status_code == 200
    assert first.headers["X-Cache"] == "MISS"

    second = client.get("/api/stats")
    assert second.headers["X-Cache"] == "HIT"
    assert second.json() == first.json()


def test_complaint_creation_invalidates_stats_cache(client: TestClient) -> None:
    client.get("/api/stats")  # populate cache -> total 0
    hit = client.get("/api/stats")
    assert hit.headers["X-Cache"] == "HIT"

    client.post(
        "/api/complaints",
        json={"text": "A fresh complaint about a water leak here", "location": "Street 1"},
    )

    after_write = client.get("/api/stats")
    assert after_write.headers["X-Cache"] == "MISS"
    assert after_write.json()["total"] == 1


def test_stats_totals_are_correct(client: TestClient) -> None:
    for _ in range(3):
        client.post(
            "/api/complaints",
            json={"text": "Another water leak complaint text here please", "location": "Street 2"},
        )

    response = client.get("/api/stats")
    assert response.json()["total"] == 3
