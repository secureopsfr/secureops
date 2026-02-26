"""Tests unitaires pour les vérifications TLS/HTTPS (scan_runner)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.scan_runner import _build_https_url, run_tls_checks


def test_build_https_url_from_http() -> None:
    """_build_https_url transforme http://host en https://host/."""
    assert _build_https_url("http://example.com") == "https://example.com/"
    assert _build_https_url("http://example.com/") == "https://example.com/"
    assert _build_https_url("http://example.com:80/path") == "https://example.com/"


def test_build_https_url_from_https() -> None:
    """_build_https_url transforme https://host en https://host/."""
    assert _build_https_url("https://example.com") == "https://example.com/"
    assert _build_https_url("https://example.com:443/") == "https://example.com/"


@pytest.mark.asyncio()
async def test_run_tls_checks_https_ok() -> None:
    """run_tls_checks retourne https_enabled=True quand le serveur répond en HTTPS."""
    mock_response = AsyncMock()
    mock_response.status_code = 200

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)

    with patch("app.services.scan_runner.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await run_tls_checks("https://example.com")

    assert result.https_enabled is True
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
    assert len(result.findings) == 1
    assert "HTTPS non activé" in result.findings[0]
