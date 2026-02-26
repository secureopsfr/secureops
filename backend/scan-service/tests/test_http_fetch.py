"""Tests unitaires pour le module http_fetch (app.utils.http_fetch)."""

from unittest.mock import AsyncMock

import httpx
import pytest

from app.utils.http_fetch import get_with_client


@pytest.mark.asyncio()
async def test_get_with_client_retourne_reponse() -> None:
    """get_with_client retourne la réponse en cas de succès."""
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    result = await get_with_client(mock_client, "https://example.com/")

    assert result is mock_resp
    assert result.status_code == 200


@pytest.mark.asyncio()
async def test_get_with_client_retourne_none_connect_error() -> None:
    """get_with_client retourne None en cas de ConnectError."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    result = await get_with_client(mock_client, "https://example.com/")

    assert result is None


@pytest.mark.asyncio()
async def test_get_with_client_retourne_none_timeout() -> None:
    """get_with_client retourne None en cas de timeout."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectTimeout("Timeout"))

    result = await get_with_client(mock_client, "https://example.com/")

    assert result is None
