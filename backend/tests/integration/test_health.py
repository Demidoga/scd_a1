"""/health (liveness) and /ready (readiness). docs/architecture/backend.md §6."""

from fastapi.testclient import TestClient

import app.routes.health as health_routes


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_200_when_dependencies_reachable(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200


def test_ready_returns_503_naming_postgres_when_db_unreachable(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(health_routes, "check_database", lambda: False)
    response = client.get("/ready")
    assert response.status_code == 503
    assert "postgresql" in response.json()["detail"]


def test_ready_returns_503_naming_redis_when_redis_unreachable(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(health_routes, "check_database", lambda: True)
    monkeypatch.setattr(health_routes, "check_redis", lambda: False)
    response = client.get("/ready")
    assert response.status_code == 503
    assert "redis" in response.json()["detail"]
