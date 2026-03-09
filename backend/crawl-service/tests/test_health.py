"""Tests du routeur health du crawl-service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    """Client de test FastAPI."""
    return TestClient(app)


def test_health_returns_200(client: TestClient) -> None:
    """Le endpoint /api/health retourne 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "crawl-service"
