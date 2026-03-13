"""Tests unitaires pour les vérifications Directory Listing (passive)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.passive.directory_listing import DirectoryListingCheckResult, DirectoryListingEntry, run_directory_listing_checks


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_aucun_listing() -> None:
    """Toutes les requêtes retournent 404 → aucun listing détecté."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b""

    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_resp

        result = await run_directory_listing_checks("https://example.com")

    assert isinstance(result, DirectoryListingCheckResult)
    assert result.exposed == ()
    assert result.findings == ()
    assert result.fetch_ok is True


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_apache_listing_uploads() -> None:
    """GET /uploads/ retourne 200 avec signature Apache → listing détecté."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'<title>Index of /uploads/</title>\n<h1>Index of /uploads/</h1>\n<a href="?C=N;O=D">Name</a>'

    async def _fetch_side_effect(url, **kwargs):
        if "uploads" in url:
            return mock_resp
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_directory_listing_checks("https://example.com")

    assert len(result.exposed) >= 1
    uploads_finding = next((e for e in result.exposed if "/uploads/" in e.path), None)
    assert uploads_finding is not None
    assert uploads_finding.severity == "high"
    assert "uploads" in uploads_finding.message.lower()
    assert result.fetch_ok is True


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_nginx_listing_static() -> None:
    """GET /static/ retourne 200 avec signature Nginx → listing détecté."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'<title>Index of /static/</title>\n<hr><pre><a href="main.js">main.js</a>\nnginx'

    async def _fetch_side_effect(url, **kwargs):
        if "static" in url:
            return mock_resp
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_directory_listing_checks("https://example.com")

    static_finding = next((e for e in result.exposed if "/static/" in e.path), None)
    assert static_finding is not None
    assert static_finding.severity == "medium"


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_200_sans_signature_non_listing() -> None:
    """200 avec page SPA (pas de signature listing) ne doit pas être considéré comme listing."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"<html><body>Welcome to our app. Index of products.</body></html>"

    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_resp

        result = await run_directory_listing_checks("https://example.com")

    # "index of" présent mais pas de signature Apache/Nginx supplémentaire → pas de listing
    assert result.exposed == ()
    assert result.findings == ()


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_parent_directory_signature() -> None:
    """Signature 'Parent Directory' (Apache) déclenche la détection."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"Index of /assets/\nParent Directory\nfile.css"

    async def _fetch_side_effect(url, **kwargs):
        if "assets" in url:
            return mock_resp
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_directory_listing_checks("https://example.com")

    assets_finding = next((e for e in result.exposed if "/assets/" in e.path), None)
    assert assets_finding is not None


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_fetch_ok_false_si_toutes_echouent() -> None:
    """Si toutes les requêtes échouent (None), fetch_ok doit être False."""
    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = None

        result = await run_directory_listing_checks("https://example.com")

    assert result.fetch_ok is False
    assert result.exposed == ()


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_partial_listing() -> None:
    """Listing partiel : HTML avec liens vers fichiers (sans signature Apache/Nginx)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""<html><body><h1>Files</h1>
    <a href="report.pdf">report.pdf</a>
    <a href="data.csv">data.csv</a>
    <a href="backup.zip">backup.zip</a>
    </body></html>"""

    async def _fetch_side_effect(url, **kwargs):
        if "uploads" in url:
            return mock_resp
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_directory_listing_checks("https://example.com")

    uploads_finding = next((e for e in result.exposed if "/uploads/" in e.path), None)
    assert uploads_finding is not None


@pytest.mark.asyncio()
async def test_run_directory_listing_checks_403_sensitive_path() -> None:
    """403 sur /config/ (chemin sensible) → finding exposed_403."""
    mock_resp_403 = MagicMock()
    mock_resp_403.status_code = 403
    mock_resp_403.content = b"Forbidden"

    async def _fetch_side_effect(url, **kwargs):
        if "config" in url:
            return mock_resp_403
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.passive.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_directory_listing_checks("https://example.com")

    assert len(result.exposed_403) >= 1
    config_finding = next((e for e in result.exposed_403 if "/config/" in e.path), None)
    assert config_finding is not None
    assert "403" in config_finding.message
    assert result.fetch_ok is True


def test_directory_listing_check_result_to_dict() -> None:
    """to_dict() sérialise correctement pour l'événement SSE result."""
    result = DirectoryListingCheckResult(
        exposed=(DirectoryListingEntry("/uploads/", "high", "Listing activé sur /uploads/."),),
        findings=("Listing activé sur /uploads/.",),
        fetch_ok=True,
    )
    d = result.to_dict()

    assert d["fetch_ok"] is True
    assert len(d["exposed"]) == 1
    assert d["exposed"][0]["path"] == "/uploads/"
    assert d["exposed"][0]["severity"] == "high"
    assert d["exposed"][0]["message"] == "Listing activé sur /uploads/."
    assert d["findings"] == ["Listing activé sur /uploads/."]
    assert "exposed_403" in d
    assert d["exposed_403"] == []


def test_directory_listing_check_result_to_dict_with_exposed_403() -> None:
    """to_dict() inclut exposed_403 quand présent."""
    pf_403 = DirectoryListingEntry("/config/", "medium", "Répertoire sensible /config/ retourne 403.")
    result = DirectoryListingCheckResult(
        exposed=(),
        findings=(),
        fetch_ok=True,
        exposed_403=(pf_403,),
    )
    d = result.to_dict()

    assert d["exposed_403"] == [{"path": "/config/", "severity": "medium", "message": pf_403.message}]
