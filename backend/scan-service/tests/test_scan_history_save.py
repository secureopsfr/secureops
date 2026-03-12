"""Tests unitaires de sauvegarde de l'historique de scan."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.scan_history_save import save_scan_to_history


@pytest.mark.asyncio()
async def test_save_scan_to_history_success_returns_id() -> None:
    """La sauvegarde retourne l'ID du scan si user-service répond 2xx."""
    payload = {
        "url": "https://example.com",
        "scan_type": "frontend",
        "score": 100,
        "findings": [],
        "timestamp": "2026-01-01T00:00:00+00:00",
        "duration": 1.23,
        "category_summaries": [],
    }
    response = MagicMock()
    response.status_code = 201
    response.json.return_value = {"id": "scan_123"}

    client = AsyncMock()
    client.post.return_value = response
    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = False

    with patch("app.services.scan_history_save.httpx.AsyncClient", return_value=client_cm):
        scan_id = await save_scan_to_history(payload, "Bearer token")

    assert scan_id == "scan_123"


@pytest.mark.asyncio()
async def test_save_scan_to_history_raises_on_http_error() -> None:
    """La sauvegarde lève une exception si user-service répond >= 400."""
    payload = {
        "url": "https://example.com",
        "scan_type": "frontend",
        "score": 80,
        "findings": [],
        "timestamp": "2026-01-01T00:00:00+00:00",
        "duration": 2.0,
    }
    response = MagicMock()
    response.status_code = 500
    response.text = "boom"

    client = AsyncMock()
    client.post.return_value = response
    client_cm = AsyncMock()
    client_cm.__aenter__.return_value = client
    client_cm.__aexit__.return_value = False

    with patch("app.services.scan_history_save.httpx.AsyncClient", return_value=client_cm), pytest.raises(RuntimeError):
        await save_scan_to_history(payload, "Bearer token")
