"""Tests du routeur de scan (POST /api/scan, réponse SSE)."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.errors.fetch_errors import FetchResult
from tests.conftest import parse_sse_events, patch_scan_checks


def test_post_scan_accepte_url_valide(client) -> None:
    """POST /api/scan avec URL valide retourne 200 et stream avec result.

    Mock des appels réseau via patch_scan_checks pour fiabilité en CI.
    """
    with patch_scan_checks():
        response = client.post("/api/scan", json={"url": "https://github.com"})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    events = parse_sse_events(response)
    result_events = [e for e in events if e[0] == "result"]
    assert len(result_events) == 1
    data = result_events[0][1]
    assert "github.com" in data["url"]
    assert "timestamp" in data
    assert "duration" in data
    assert "score" in data
    assert isinstance(data["score"], int)
    assert 0 <= data["score"] <= 100
    assert "findings" in data
    assert isinstance(data["findings"], list)


def test_post_scan_refuse_url_avec_credentials(client) -> None:
    """POST /api/scan avec user:pass@ envoie un événement error."""
    response = client.post("/api/scan", json={"url": "http://user:pass@example.com"})
    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    assert "credentials" in error_events[0][1].get("message", "").lower()


def test_post_scan_refuse_schema_file(client) -> None:
    """POST /api/scan avec file:// envoie un événement error."""
    response = client.post("/api/scan", json={"url": "file:///etc/passwd"})
    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "http" in msg or "schéma" in msg


def test_post_scan_refuse_port_8080(client) -> None:
    """POST /api/scan avec port 8080 envoie un événement error."""
    response = client.post("/api/scan", json={"url": "http://example.com:8080"})
    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    assert "port" in error_events[0][1].get("message", "").lower()


def test_post_scan_refuse_localhost_ssrf(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/scan refuse localhost (SSRF) via événement error (sans SCAN_ALLOW_LOCALHOST)."""
    monkeypatch.delenv("SCAN_ALLOW_LOCALHOST", raising=False)
    response = client.post("/api/scan", json={"url": "http://localhost/"})
    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "localhost" in msg or "127.0.0.1" in msg or "autorisées" in msg


def test_post_scan_refuse_127_0_0_1_ssrf(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/scan refuse 127.0.0.1 (SSRF) via événement error (sans SCAN_ALLOW_LOCALHOST)."""
    monkeypatch.delenv("SCAN_ALLOW_LOCALHOST", raising=False)
    response = client.post("/api/scan", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "localhost" in msg or "127" in msg or "autorisées" in msg


def test_post_scan_site_inaccessible_emits_error(client) -> None:
    """Fetch HTTPS échoue (site inaccessible) → événement error, pas de result."""
    fetch_result_fail = FetchResult(
        success=False,
        response=None,
        error_type="connection_failed",
        message="Le site est inaccessible (connexion refusée ou DNS).",
        status_code=503,
        details=None,
    )

    @asynccontextmanager
    async def _fake_scan_client():
        yield MagicMock()

    with (
        patch("app.services.scan_stream.check_ssrf", new_callable=AsyncMock),
        patch("app.services.scan_stream.scan_client", _fake_scan_client),
        patch("app.services.scan_stream.get_with_client_or_error", new_callable=AsyncMock, return_value=fetch_result_fail),
    ):
        response = client.post("/api/scan", json={"url": "https://example.invalid"})

    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    result_events = [e for e in events if e[0] == "result"]
    assert len(error_events) == 1
    assert len(result_events) == 0
    assert error_events[0][1]["message"] == "Le site est inaccessible (connexion refusée ou DNS)."
    assert error_events[0][1]["status_code"] == 503
    assert error_events[0][1]["error_type"] == "connection_failed"


@pytest.mark.integration()
def test_post_scan_integration_reel(client) -> None:
    """Test d'intégration : scan réel vers https://github.com (sans mock).

    Exclure en CI avec : pytest -m 'not integration'
    """
    response = client.post("/api/scan", json={"url": "https://github.com"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    events = parse_sse_events(response)
    result_events = [e for e in events if e[0] == "result"]
    assert len(result_events) == 1
    data = result_events[0][1]
    assert "github.com" in data["url"]
    assert "score" in data
    assert "findings" in data
