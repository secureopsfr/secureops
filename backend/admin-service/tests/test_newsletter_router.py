"""Tests unitaires du router newsletter."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.newsletter as newsletter_router_module


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(newsletter_router_module.router, prefix="/api")
    return app


def test_schedule_newsletter_accepts_string_scheduled_at(monkeypatch) -> None:
    """Le endpoint schedule doit accepter scheduled_at string sans isoformat()."""
    called = {"value": False}

    def fake_schedule(email_id: int, scheduled_at: str):  # type: ignore[no-untyped-def]
        called["value"] = True
        return {"message": "scheduled", "email_id": email_id, "scheduled_at": scheduled_at}

    async def fake_log_action(**kwargs):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr(newsletter_router_module.newsletter_service, "schedule_newsletter_email", fake_schedule)
    monkeypatch.setattr(newsletter_router_module, "log_action", fake_log_action)
    client = TestClient(_build_app())

    payload = {"email_id": 10, "scheduled_at": "2026-03-20T08:30:00Z"}
    resp = client.post("/api/newsletter/schedule", json=payload)

    assert resp.status_code == 200
    assert called["value"] is True
    assert resp.json()["scheduled_at"] == "2026-03-20T08:30:00Z"
