"""Tests unitaires pour le module http_fetch (app.utils.http_fetch)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.utils.http_fetch import fetch_https


@pytest.mark.asyncio()
async def test_fetch_https_retourne_reponse() -> None:
    """fetch_https retourne la réponse en cas de succès."""
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_resp)

    with patch("app.utils.http_fetch.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await fetch_https("https://example.com")

    assert result is mock_resp
    assert result.status_code == 200


@pytest.mark.asyncio()
async def test_fetch_https_retourne_none_connect_error() -> None:
    """fetch_https retourne None en cas de ConnectError."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    with patch("app.utils.http_fetch.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await fetch_https("https://example.com")

    assert result is None


@pytest.mark.asyncio()
async def test_fetch_https_retourne_none_timeout() -> None:
    """fetch_https retourne None en cas de timeout."""
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.ConnectTimeout("Timeout"))

    with patch("app.utils.http_fetch.httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_context

        result = await fetch_https("https://example.com")

    assert result is None
