"""Tests du routeur de scan (POST /api/scan, réponse SSE)."""

import pytest

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
    assert result_events[0][1]["valid"] is True
    assert "github.com" in result_events[0][1]["url"]
    assert "tls" in result_events[0][1]
    assert result_events[0][1]["tls"]["https_enabled"] is True
    assert result_events[0][1]["tls"]["http_redirects_to_https"] is True
    assert result_events[0][1]["tls"]["certificate_status"] == "valid"
    assert result_events[0][1]["tls"]["tls_versions_obsolete"] == []
    assert result_events[0][1]["tls"]["findings"] == []
    assert "directory_listing" in result_events[0][1]
    assert "robots_txt" in result_events[0][1]
    assert "tech_fingerprinting" in result_events[0][1]


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
