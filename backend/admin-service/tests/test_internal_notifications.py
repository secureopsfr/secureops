"""Tests unitaires de la protection des endpoints internes notifications."""

import pytest
from fastapi import HTTPException

import app.routers.internal_notifications as internal_notifications_module


@pytest.mark.asyncio()
async def test_internal_key_fails_when_not_configured(monkeypatch) -> None:
    """Doit échouer en fail-closed si la clé interne n'est pas configurée."""
    monkeypatch.setattr(internal_notifications_module, "INTERNAL_API_KEY", None)

    with pytest.raises(HTTPException) as exc:
        await internal_notifications_module._verify_internal_api_key(None)

    assert exc.value.status_code == 503


@pytest.mark.asyncio()
async def test_internal_key_rejects_invalid_key(monkeypatch) -> None:
    """Doit refuser une clé interne invalide."""
    monkeypatch.setattr(internal_notifications_module, "INTERNAL_API_KEY", "expected-key")

    with pytest.raises(HTTPException) as exc:
        await internal_notifications_module._verify_internal_api_key("wrong-key")

    assert exc.value.status_code == 401


@pytest.mark.asyncio()
async def test_internal_key_accepts_valid_key(monkeypatch) -> None:
    """Doit accepter la clé interne valide."""
    monkeypatch.setattr(internal_notifications_module, "INTERNAL_API_KEY", "expected-key")
    await internal_notifications_module._verify_internal_api_key("expected-key")
