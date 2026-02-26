"""Tests unitaires pour les vérifications Security Headers (app.services.security_headers.checks)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.security_headers import run_security_headers_checks


@pytest.mark.asyncio()
async def test_run_security_headers_checks_tous_presents() -> None:
    """run_security_headers_checks retourne tous les headers présents si la réponse les contient."""
    mock_resp = AsyncMock()
    mock_resp.headers = {
        "Content-Security-Policy": "default-src 'self'",
        "Strict-Transport-Security": "max-age=31536000",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=()",
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.security_headers.checks.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_security_headers_checks("https://example.com")

    assert result.fetch_ok is True
    assert len(result.headers_present) == 6
    assert "Content-Security-Policy" in result.headers_present
    assert "X-Content-Type-Options" in result.headers_present
    assert result.headers_missing == ()
    assert result.findings == ()


@pytest.mark.asyncio()
async def test_run_security_headers_checks_aucun_present() -> None:
    """run_security_headers_checks détecte tous les headers manquants."""
    mock_resp = AsyncMock()
    mock_resp.headers = {}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.security_headers.checks.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_security_headers_checks("https://example.com")

    assert result.fetch_ok is True
    assert result.headers_present == ()
    assert len(result.headers_missing) == 6
    assert len(result.findings) == 6
    assert any("Content-Security-Policy" in f for f in result.findings)
    assert any("XSS" in f for f in result.findings)
    assert any("X-Frame-Options" in f for f in result.findings)


@pytest.mark.asyncio()
async def test_run_security_headers_checks_x_content_type_options_mauvais() -> None:
    """run_security_headers_checks détecte X-Content-Type-Options avec valeur incorrecte."""
    mock_resp = AsyncMock()
    mock_resp.headers = {
        "X-Content-Type-Options": "invalid",
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.security_headers.checks.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_security_headers_checks("https://example.com")

    assert result.fetch_ok is True
    assert "X-Content-Type-Options" in result.headers_present
    assert any("nosniff" in f for f in result.findings)
    assert any("valeur incorrecte" in f for f in result.findings)


@pytest.mark.asyncio()
async def test_run_security_headers_checks_connect_error() -> None:
    """run_security_headers_checks retourne fetch_ok=False en cas de ConnectError."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    with patch("app.services.security_headers.checks.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_security_headers_checks("https://example.com")

    assert result.fetch_ok is False
    assert result.headers_present == ()
    assert len(result.headers_missing) == 6
    assert len(result.findings) == 1
    assert "connexion refusée" in result.findings[0].lower() or "timeout" in result.findings[0].lower() or "en-têtes" in result.findings[0].lower()


@pytest.mark.asyncio()
async def test_run_security_headers_checks_headers_case_insensitive() -> None:
    """Les noms d'en-têtes HTTP sont insensibles à la casse."""
    mock_resp = AsyncMock()
    mock_resp.headers = {
        "content-security-policy": "default-src 'self'",
        "x-frame-options": "DENY",
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.security_headers.checks.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_security_headers_checks("https://example.com")

    assert result.fetch_ok is True
    assert "Content-Security-Policy" in result.headers_present
    assert "X-Frame-Options" in result.headers_present
    assert len(result.headers_missing) == 4
