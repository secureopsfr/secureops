"""Tests unitaires du router mailing list."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.mailing_list as mailing_list_router_module


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(mailing_list_router_module.router, prefix="/api")
    return app


def test_verify_email_response_contract(monkeypatch) -> None:
    """Le endpoint verify doit respecter MailingListSubscribeResponse."""

    def fake_verify_email(email: str):  # type: ignore[no-untyped-def]
        return {"success": True, "message": "ok", "email": email}

    monkeypatch.setattr(mailing_list_router_module.mailing_list_service, "verify_email", fake_verify_email)
    client = TestClient(_build_app())

    resp = client.put("/api/mailing-list/verify", params={"email": "john@example.com"})

    assert resp.status_code == 200
    assert resp.json() == {"success": True, "message": "ok", "email": "john@example.com"}


def test_unsubscribe_response_contract(monkeypatch) -> None:
    """Le endpoint unsubscribe doit respecter MailingListSubscribeResponse."""

    def fake_unsubscribe(email: str):  # type: ignore[no-untyped-def]
        return {"success": True, "message": "unsubscribed", "email": email}

    monkeypatch.setattr(mailing_list_router_module.mailing_list_service, "unsubscribe_email", fake_unsubscribe)
    client = TestClient(_build_app())

    resp = client.delete("/api/mailing-list/unsubscribe", params={"email": "john@example.com"})

    assert resp.status_code == 200
    assert resp.json() == {"success": True, "message": "unsubscribed", "email": "john@example.com"}
