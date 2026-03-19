"""Tests unitaires du middleware d'authentification gateway."""

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

import app.middleware as middleware_module
from app.middleware import AuthMiddleware


@pytest.fixture(autouse=True)
def _enable_auth_middleware(monkeypatch) -> None:
    """Force l'activation du middleware pendant les tests."""
    monkeypatch.setenv("DISABLE_AUTH_MIDDLEWARE", "false")


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/protected")
    async def protected() -> dict[str, str]:
        return {"status": "protected"}

    @app.get("/admin/secure")
    async def admin_secure() -> dict[str, str]:
        return {"status": "admin"}

    @app.get("/admin/api/docs")
    async def admin_docs() -> dict[str, str]:
        return {"status": "docs"}

    @app.post("/user/api/user/init")
    async def user_init() -> dict[str, str]:
        return {"status": "init"}

    return app


def test_public_health_bypasses_auth(monkeypatch) -> None:
    """La route /health ne doit pas déclencher l'authentification."""

    async def fake_authenticate(request, require_admin=False):  # type: ignore[no-untyped-def]
        raise AssertionError("auth should not be called for /health")

    monkeypatch.setattr(middleware_module, "_authenticate", fake_authenticate)
    client = TestClient(_build_test_app())

    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_admin_route_requires_admin_flag(monkeypatch) -> None:
    """Les routes /admin/* doivent appeler _authenticate avec require_admin=True."""
    calls: list[bool] = []

    async def fake_authenticate(request, require_admin=False):  # type: ignore[no-untyped-def]
        calls.append(require_admin)
        return {"sub": "u1"}, None

    monkeypatch.setattr(middleware_module, "_authenticate", fake_authenticate)
    client = TestClient(_build_test_app())

    resp = client.get("/admin/secure")

    assert resp.status_code == 200
    assert calls == [True]


def test_admin_docs_are_public(monkeypatch) -> None:
    """GET /admin/api/docs est une route publique (aucune authentification requise)."""
    calls: list[bool] = []

    async def fake_authenticate(request, require_admin=False):  # type: ignore[no-untyped-def]
        calls.append(require_admin)
        return {"sub": "u1"}, None

    monkeypatch.setattr(middleware_module, "_authenticate", fake_authenticate)
    client = TestClient(_build_test_app())

    resp = client.get("/admin/api/docs")

    assert resp.status_code == 200
    assert resp.json() == {"status": "docs"}
    # Route publique : _authenticate n'est jamais appelé
    assert calls == []


def test_auth_only_method_path_uses_simple_auth(monkeypatch) -> None:
    """POST /user/api/user/init doit être auth-only (pas require_admin)."""
    calls: list[bool] = []

    async def fake_authenticate(request, require_admin=False):  # type: ignore[no-untyped-def]
        calls.append(require_admin)
        return {"sub": "u1"}, None

    monkeypatch.setattr(middleware_module, "_authenticate", fake_authenticate)
    client = TestClient(_build_test_app())

    resp = client.post("/user/api/user/init")

    assert resp.status_code == 200
    assert calls == [False]


def test_protected_route_returns_auth_error(monkeypatch) -> None:
    """Les routes protégées renvoient l'erreur _authenticate le cas échéant."""

    async def fake_authenticate(request, require_admin=False):  # type: ignore[no-untyped-def]
        return None, JSONResponse(status_code=401, content={"detail": "unauthorized"})

    monkeypatch.setattr(middleware_module, "_authenticate", fake_authenticate)
    client = TestClient(_build_test_app())

    resp = client.get("/protected")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "unauthorized"
