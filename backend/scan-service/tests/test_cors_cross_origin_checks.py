"""Tests unitaires pour les vérifications CORS et cross-origin (app.services.cors_cross_origin.checks)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.cors_cross_origin.checks import (
    CorsCrossOriginCheckResult,
    run_cors_cross_origin_checks,
)


def _mock_response(
    url: str = "https://example.com/",
    text: str = "",
    headers: dict | None = None,
) -> MagicMock:
    """Construit un mock de réponse HTTP."""
    resp = MagicMock()
    resp.url = url
    resp.text = text
    resp.headers = dict(headers or {})
    return resp


@pytest.mark.asyncio()
async def test_cors_response_none() -> None:
    """Réponse None → fetch_ok False et finding explicatif."""
    result = await run_cors_cross_origin_checks(None, "https://example.com/", AsyncMock())
    assert isinstance(result, CorsCrossOriginCheckResult)
    assert result.fetch_ok is False
    assert len(result.findings) >= 1
    assert "inaccessibles" in result.findings[0].lower() or "indisponible" in result.findings[0].lower()


@pytest.mark.asyncio()
async def test_cors_mixed_content() -> None:
    """Page HTTPS avec ressource script en http:// → finding mixed content."""
    resp = _mock_response(
        url="https://example.com/",
        text='<html><script src="http://cdn.evil.com/lib.js"></script></html>',
    )
    client = AsyncMock()
    client.get = AsyncMock(return_value=MagicMock(status_code=200, headers={}))
    client.request = AsyncMock(return_value=MagicMock(status_code=200, headers={}))
    result = await run_cors_cross_origin_checks(resp, "https://example.com/", client)
    assert result.fetch_ok is True
    assert any("mixed content" in f.lower() and "http" in f.lower() for f in result.findings)


@pytest.mark.asyncio()
async def test_cors_corp_missing_main_page() -> None:
    """Page principale sans CORP → finding CORP manquant (page principale)."""
    resp = _mock_response(url="https://example.com/", text="<html></html>", headers={})
    client = AsyncMock()
    client.get = AsyncMock(return_value=MagicMock(status_code=200, headers={}))
    client.request = AsyncMock(return_value=MagicMock(status_code=200, headers={}))
    result = await run_cors_cross_origin_checks(resp, "https://example.com/", client)
    assert result.fetch_ok is True
    assert any("cross-origin-resource-policy" in f.lower() and "page principale" in f.lower() for f in result.findings)


@pytest.mark.asyncio()
async def test_cors_acao_star_on_sensitive_endpoint() -> None:
    """Requête vers URL sensible avec ACAO * → finding ACAO * sur endpoint sensible."""
    resp = _mock_response(
        url="https://example.com/api/",
        text="<html></html>",
        headers={},
    )
    client = AsyncMock()
    mock_cors_resp = MagicMock()
    mock_cors_resp.status_code = 200
    mock_cors_resp.headers = {
        "Access-Control-Allow-Origin": "*",
    }
    mock_cors_resp.url = "https://example.com/api/"
    client.get = AsyncMock(return_value=mock_cors_resp)
    client.request = AsyncMock(return_value=mock_cors_resp)
    result = await run_cors_cross_origin_checks(resp, "https://example.com/api/", client)
    assert result.fetch_ok is True
    assert any("allow-origin" in f.lower() and "*" in f and "sensible" in f.lower() for f in result.findings)


@pytest.mark.asyncio()
async def test_cors_credentials_with_reflected_origin() -> None:
    """Réponse avec Credentials true et ACAO reflétant test_origin → finding réflexion."""
    resp = _mock_response(url="https://example.com/", text="<html></html>", headers={})
    client = AsyncMock()
    mock_cors_resp = MagicMock()
    mock_cors_resp.status_code = 200
    mock_cors_resp.headers = {
        "Access-Control-Allow-Origin": "https://evil.example.com",
        "Access-Control-Allow-Credentials": "true",
    }
    mock_cors_resp.url = "https://example.com/"
    client.get = AsyncMock(return_value=mock_cors_resp)
    client.request = AsyncMock(return_value=mock_cors_resp)
    result = await run_cors_cross_origin_checks(resp, "https://example.com/", client)
    assert result.fetch_ok is True
    assert any("réflexion" in f.lower() or "reflection" in f.lower() for f in result.findings)
