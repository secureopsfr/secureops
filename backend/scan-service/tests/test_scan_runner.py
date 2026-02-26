"""Tests unitaires pour les vérifications TLS/HTTPS (scan_runner)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.scan_runner import (
    _build_http_url,
    _build_https_url,
    _location_redirects_to_https,
    run_tls_checks,
)


def test_build_https_url_from_http() -> None:
    """_build_https_url transforme http://host en https://host/."""
    assert _build_https_url("http://example.com") == "https://example.com/"
    assert _build_https_url("http://example.com/") == "https://example.com/"
    assert _build_https_url("http://example.com:80/path") == "https://example.com/"


def test_build_https_url_from_https() -> None:
    """_build_https_url transforme https://host en https://host/."""
    assert _build_https_url("https://example.com") == "https://example.com/"
    assert _build_https_url("https://example.com:443/") == "https://example.com/"


def test_build_http_url() -> None:
    """_build_http_url construit http://host/."""
    assert _build_http_url("https://example.com") == "http://example.com/"
    assert _build_http_url("http://example.com:80/path") == "http://example.com/"


def test_location_redirects_to_https() -> None:
    """_location_redirects_to_https détecte les URLs https."""
    assert _location_redirects_to_https("https://example.com/") is True
    assert _location_redirects_to_https("HTTPS://example.com") is True
    assert _location_redirects_to_https("http://example.com") is False
    assert _location_redirects_to_https("") is False
    assert _location_redirects_to_https(None) is False


@pytest.mark.asyncio()
async def test_run_tls_checks_https_ok_et_redirect_ok() -> None:
    """run_tls_checks retourne https_enabled=True et http_redirects_to_https=True."""
    mock_https_resp = AsyncMock()
    mock_https_resp.status_code = 200
    mock_http_resp = AsyncMock()
    mock_http_resp.status_code = 301
    mock_http_resp.headers = {"location": "https://example.com/"}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=[mock_https_resp, mock_http_resp])

    with patch("app.services.scan_runner.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("https://example.com")

    assert result.https_enabled is True
    assert result.http_redirects_to_https is True
    assert len(result.findings) == 0


@pytest.mark.asyncio()
async def test_run_tls_checks_https_non_actif_connect_error() -> None:
    """run_tls_checks retourne https_enabled=False et un finding en cas de ConnectError."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    with patch("app.services.scan_runner.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("http://monsite.com")

    assert result.https_enabled is False
    assert result.http_redirects_to_https is None
    assert len(result.findings) == 1
    assert "HTTPS non activé" in result.findings[0]
    assert "interception" in result.findings[0]


@pytest.mark.asyncio()
async def test_run_tls_checks_https_non_actif_timeout() -> None:
    """run_tls_checks retourne https_enabled=False en cas de timeout."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectTimeout("Timeout"))

    with patch("app.services.scan_runner.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("http://example.com")

    assert result.https_enabled is False
    assert result.http_redirects_to_https is None
    assert len(result.findings) == 1
    assert "HTTPS non activé" in result.findings[0]


@pytest.mark.asyncio()
async def test_run_tls_checks_pas_redirection_http() -> None:
    """run_tls_checks détecte l'absence de redirection HTTP→HTTPS (réponse 200)."""
    mock_https_resp = AsyncMock()
    mock_https_resp.status_code = 200
    mock_http_resp = AsyncMock()
    mock_http_resp.status_code = 200
    mock_http_resp.headers = {}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=[mock_https_resp, mock_http_resp])

    with patch("app.services.scan_runner.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("https://monsite.com")

    assert result.https_enabled is True
    assert result.http_redirects_to_https is False
    assert len(result.findings) == 1
    assert "Pas de redirection HTTP→HTTPS" in result.findings[0]
