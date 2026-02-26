"""Tests du routeur de scan (POST /api/scan, réponse SSE)."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.exposed_files import ExposedFilesCheckResult
from app.services.tls.checks import TlsCheckResult
from tests.conftest import parse_sse_events


@asynccontextmanager
async def _fake_scan_client():
    """Fake scan_client pour tests (évite requêtes réseau)."""
    yield MagicMock()


def test_post_scan_accepte_url_valide(client) -> None:
    """POST /api/scan avec URL valide retourne 200 et stream avec result.

    Mock des appels réseau (scan_client, get_with_client, run_tls_checks, run_exposed_files_checks,
    check_ssrf) pour fiabilité en CI.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.content = b""
    tls_result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(),
    )
    exposed_result = ExposedFilesCheckResult(exposed=(), findings=(), fetch_ok=True)

    with (
        patch("app.services.scan_stream.check_ssrf", new_callable=AsyncMock),
        patch("app.services.scan_stream.scan_client", _fake_scan_client),
        patch("app.services.scan_stream.get_with_client", new_callable=AsyncMock, return_value=mock_response),
        patch("app.services.scan_stream.run_tls_checks", new_callable=AsyncMock, return_value=tls_result),
        patch("app.services.scan_stream.run_exposed_files_checks", new_callable=AsyncMock, return_value=exposed_result),
    ):
        response = client.post("/api/scan", json={"url": "https://github.com"})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    events = parse_sse_events(response)
    result_events = [e for e in events if e[0] == "result"]
    assert len(result_events) == 1
    assert result_events[0][1]["valid"] is True
    assert "github.com" in result_events[0][1]["url"]
    assert "tls" in result_events[0][1]
    assert result_events[0][1]["tls"]["https_enabled"] is True
    assert result_events[0][1]["tls"]["http_redirects_to_https"] is True
    assert result_events[0][1]["tls"]["certificate_status"] == "valid"
    assert result_events[0][1]["tls"]["tls_versions_obsolete"] == []
    assert result_events[0][1]["tls"]["findings"] == []


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


def test_post_scan_refuse_localhost_ssrf(client) -> None:
    """POST /api/scan refuse localhost (SSRF) via événement error."""
    response = client.post("/api/scan", json={"url": "http://localhost/"})
    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "localhost" in msg or "127.0.0.1" in msg or "autorisées" in msg


def test_post_scan_refuse_127_0_0_1_ssrf(client) -> None:
    """POST /api/scan refuse 127.0.0.1 (SSRF) via événement error."""
    response = client.post("/api/scan", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 200
    events = parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "localhost" in msg or "127" in msg or "autorisées" in msg


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
    assert "tls" in data
    assert data["tls"]["https_enabled"] is True
    assert "headers" in data
    assert "cookies" in data
