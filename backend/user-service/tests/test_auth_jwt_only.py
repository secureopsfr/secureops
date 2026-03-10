"""Tests unitaires des contraintes JWT-only."""

import pytest
from fastapi import HTTPException

from app.utils.auth import require_jwt_user


@pytest.mark.asyncio()
async def test_require_jwt_user_accepts_jwt() -> None:
    """Doit accepter un utilisateur authentifié en JWT."""
    claims = {"sub": "u1", "auth_type": "jwt"}
    result = await require_jwt_user(claims)
    assert result == claims


@pytest.mark.asyncio()
async def test_require_jwt_user_rejects_api_key() -> None:
    """Doit refuser une authentification de type API key."""
    with pytest.raises(HTTPException) as exc:
        await require_jwt_user({"sub": "u1", "auth_type": "api_key"})

    assert exc.value.status_code == 403
