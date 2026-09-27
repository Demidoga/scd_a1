"""Request ID propagation. docs/architecture/backend.md §6, docs/Milestones/milestone-2.md §16."""

import uuid

from fastapi.testclient import TestClient


def test_supplied_request_id_is_echoed_back(client: TestClient) -> None:
    supplied = str(uuid.uuid4())
    response = client.get("/health", headers={"X-Request-ID": supplied})
    assert response.headers["X-Request-ID"] == supplied


def test_missing_request_id_is_generated(client: TestClient) -> None:
    response = client.get("/health")
    generated = response.headers["X-Request-ID"]
    assert generated
    uuid.UUID(generated)  # must be a valid UUID
