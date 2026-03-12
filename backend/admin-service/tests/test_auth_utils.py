"""Tests unitaires des dépendances d'auth admin."""

import pytest
from fastapi import HTTPException

import app.utils.auth as auth_module


def test_require_admin_user_accepts_admin_claims(monkeypatch) -> None:
    """Doit accepter un JWT avec groupe admin."""

    def fake_verify(token):  # type: ignore[no-untyped-def]
        return {"sub": "u1", "cognito:groups": ["admin"]}

    monkeypatch.setattr(auth_module, "verify_cognito_jwt", fake_verify)
    claims = auth_module.require_admin_user("Bearer header.payload.signature")

    assert claims["sub"] == "u1"


def test_require_admin_user_rejects_non_admin(monkeypatch) -> None:
    """Doit refuser un JWT sans groupe admin."""

    def fake_verify(token):  # type: ignore[no-untyped-def]
        return {"sub": "u1", "cognito:groups": ["user"]}

    monkeypatch.setattr(auth_module, "verify_cognito_jwt", fake_verify)

    with pytest.raises(HTTPException) as exc:
        auth_module.require_admin_user("Bearer header.payload.signature")

    assert exc.value.status_code == 403


def test_require_admin_user_rejects_missing_authorization() -> None:
    """Doit refuser l'absence du header Authorization."""
    with pytest.raises(HTTPException) as exc:
        auth_module.require_admin_user(None)

    assert exc.value.status_code == 401
