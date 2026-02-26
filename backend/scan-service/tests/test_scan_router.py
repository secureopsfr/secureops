"""Tests du routeur de scan (POST /api/scan, réponse SSE)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.tls.checks import TlsCheckResult

client = TestClient(app)


def _parse_sse_events(response) -> list[tuple[str, dict]]:
    """Parse le corps SSE en liste de (event, data)."""
    events = []
    for block in response.text.strip().split("\n\n"):
        if not block:
            continue
        event, data = "message", {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                event = line[7:].strip()
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        events.append((event, data))
    return events


def test_post_scan_accepte_url_valide() -> None:
    """POST /api/scan avec URL valide retourne 200 et stream avec result.

    Mock des appels réseau (fetch_https, run_tls_checks, check_ssrf) pour fiabilité en CI.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    tls_result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(),
    )

    with (
        patch("app.services.scan_stream.check_ssrf", new_callable=AsyncMock),
        patch("app.services.scan_stream.fetch_https", new_callable=AsyncMock, return_value=mock_response),
        patch("app.services.scan_stream.run_tls_checks", new_callable=AsyncMock, return_value=tls_result),
    ):
        response = client.post("/api/scan", json={"url": "https://github.com"})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    events = _parse_sse_events(response)
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


def test_post_scan_refuse_url_avec_credentials() -> None:
    """POST /api/scan avec user:pass@ envoie un événement error."""
    response = client.post("/api/scan", json={"url": "http://user:pass@example.com"})
    assert response.status_code == 200
    events = _parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    assert "credentials" in error_events[0][1].get("message", "").lower()


def test_post_scan_refuse_schema_file() -> None:
    """POST /api/scan avec file:// envoie un événement error."""
    response = client.post("/api/scan", json={"url": "file:///etc/passwd"})
    assert response.status_code == 200
    events = _parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "http" in msg or "schéma" in msg


def test_post_scan_refuse_port_8080() -> None:
    """POST /api/scan avec port 8080 envoie un événement error."""
    response = client.post("/api/scan", json={"url": "http://example.com:8080"})
    assert response.status_code == 200
    events = _parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    assert "port" in error_events[0][1].get("message", "").lower()


def test_post_scan_refuse_localhost_ssrf() -> None:
    """POST /api/scan refuse localhost (SSRF) via événement error."""
    response = client.post("/api/scan", json={"url": "http://localhost/"})
    assert response.status_code == 200
    events = _parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "localhost" in msg or "127.0.0.1" in msg or "autorisées" in msg


def test_post_scan_refuse_127_0_0_1_ssrf() -> None:
    """POST /api/scan refuse 127.0.0.1 (SSRF) via événement error."""
    response = client.post("/api/scan", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 200
    events = _parse_sse_events(response)
    error_events = [e for e in events if e[0] == "error"]
    assert len(error_events) == 1
    msg = error_events[0][1].get("message", "").lower()
    assert "localhost" in msg or "127" in msg or "autorisées" in msg
