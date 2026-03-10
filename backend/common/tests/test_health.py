"""Tests unitaires pour common.health."""

from fastapi.testclient import TestClient

from common.health import create_health_router


def test_create_health_router_returns_ok() -> None:
    """Le router health retourne status ok avec le nom du service."""
    router = create_health_router("my-service")
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "my-service"
    assert "timestamp" in data


def test_health_timestamp_iso_format() -> None:
    """Le timestamp est au format ISO."""
    router = create_health_router("test-svc", prefix="/api")
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    response = client.get("/api/health")
    data = response.json()
    ts = data["timestamp"]
    assert "T" in ts
    assert "Z" in ts or "+" in ts
