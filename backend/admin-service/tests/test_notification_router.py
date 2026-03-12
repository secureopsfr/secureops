"""Tests unitaires du router notification."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.notification as notification_router_module


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(notification_router_module.router, prefix="/api")
    return app


def test_schedule_notification_accepts_string_scheduled_at(monkeypatch) -> None:
    """Le endpoint schedule accepte scheduled_at string."""
    called = {"value": False}

    def fake_schedule(email_id: int, scheduled_at: str):  # type: ignore[no-untyped-def]
        called["value"] = True
        return {"message": "scheduled", "email_id": email_id, "scheduled_at": scheduled_at}

    monkeypatch.setattr(notification_router_module.notification_service, "schedule_notification_email", fake_schedule)
    client = TestClient(_build_app())

    payload = {"email_id": 22, "scheduled_at": "2026-03-25T10:00:00Z"}
    resp = client.post("/api/notifications/schedule", json=payload)

    assert resp.status_code == 200
    assert called["value"] is True
    assert resp.json()["scheduled_at"] == "2026-03-25T10:00:00Z"
