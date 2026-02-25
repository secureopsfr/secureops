"""Tests du routeur de scan (POST /api/scan)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _error_message(response) -> str:
    """Message d'erreur retourné par le common (details ou error, pas detail)."""
    body = response.json()
    return body.get("details") or body.get("error") or body.get("detail") or ""


def test_post_scan_accepte_url_valide() -> None:
    """POST /api/scan avec URL valide retourne 200 et URL normalisée."""
    response = client.post("/api/scan", json={"url": "https://example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["url"] == "https://example.com/"


def test_post_scan_refuse_url_avec_credentials() -> None:
    """POST /api/scan avec user:pass@ retourne 400."""
    response = client.post("/api/scan", json={"url": "http://user:pass@example.com"})
    assert response.status_code == 400
    assert "credentials" in _error_message(response).lower()


def test_post_scan_refuse_schema_file() -> None:
    """POST /api/scan avec file:// retourne 400."""
    response = client.post("/api/scan", json={"url": "file:///etc/passwd"})
    assert response.status_code == 400
    msg = _error_message(response).lower()
    assert "http" in msg or "schéma" in msg


def test_post_scan_refuse_port_8080() -> None:
    """POST /api/scan avec port 8080 retourne 400."""
    response = client.post("/api/scan", json={"url": "http://example.com:8080"})
    assert response.status_code == 400
    assert "port" in _error_message(response).lower()


def test_post_scan_refuse_localhost_ssrf() -> None:
    """POST /api/scan refuse localhost (protection SSRF)."""
    response = client.post("/api/scan", json={"url": "http://localhost/"})
    assert response.status_code == 400
    msg = _error_message(response).lower()
    assert "localhost" in msg or "127.0.0.1" in msg or "autorisées" in msg


def test_post_scan_refuse_127_0_0_1_ssrf() -> None:
    """POST /api/scan refuse 127.0.0.1 (protection SSRF)."""
    response = client.post("/api/scan", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 400
    msg = _error_message(response).lower()
    assert "localhost" in msg or "127" in msg or "autorisées" in msg
