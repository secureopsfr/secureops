"""Tests unitaires pour les vérifications Exposed Files (app.services.exposed_files.checks)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.exposed_files import ExposedEndpoint, ExposedFilesCheckResult, run_exposed_files_checks


@pytest.mark.asyncio()
async def test_run_exposed_files_checks_aucune_exposition() -> None:
    """Toutes les requêtes retournent 404 → aucune exposition."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b""

    with patch("app.services.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_resp

        result = await run_exposed_files_checks("https://example.com")

    assert isinstance(result, ExposedFilesCheckResult)
    assert result.exposed == ()
    assert result.findings == ()
    assert result.fetch_ok is True


@pytest.mark.asyncio()
async def test_run_exposed_files_checks_env_expose() -> None:
    """GET /.env retourne 200 avec contenu .env → exposition détectée."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"DATABASE_URL=postgres://user:pass@host/db\nSECRET_KEY=abc123"

    async def _fetch_side_effect(url, **kwargs):
        if ".env" in url:
            return mock_resp
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_exposed_files_checks("https://example.com")

    assert len(result.exposed) >= 1
    env_finding = next((e for e in result.exposed if e.path == "/.env"), None)
    assert env_finding is not None
    assert env_finding.severity == "critical"
    assert "credentials" in env_finding.message.lower() or ".env" in env_finding.message.lower()
    assert result.fetch_ok is True


@pytest.mark.asyncio()
async def test_run_exposed_files_checks_git_config_expose() -> None:
    """GET /.git/config retourne 200 avec contenu Git → exposition détectée."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'[core]\nrepositoryformatversion = 0\n[remote "origin"]'

    async def _fetch_side_effect(url, **kwargs):
        if ".git/config" in url:
            return mock_resp
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_exposed_files_checks("https://example.com")

    git_finding = next((e for e in result.exposed if "/.git/config" in e.path), None)
    assert git_finding is not None
    assert git_finding.severity == "critical"


@pytest.mark.asyncio()
async def test_run_exposed_files_checks_zip_expose() -> None:
    """GET /backup.zip retourne 200 avec en-tête PK → exposition détectée."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"PK\x03\x04" + b"\x00" * 100

    async def _fetch_side_effect(url, **kwargs):
        if "backup.zip" in url:
            return mock_resp
        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_404.content = b""
        return resp_404

    with patch("app.services.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = _fetch_side_effect

        result = await run_exposed_files_checks("https://example.com")

    zip_finding = next((e for e in result.exposed if "backup.zip" in e.path), None)
    assert zip_finding is not None
    assert zip_finding.severity == "high"


@pytest.mark.asyncio()
async def test_run_exposed_files_checks_200_corps_vide_non_expose() -> None:
    """200 avec corps vide ne doit pas être considéré comme exposition."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b""

    with patch("app.services.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_resp

        result = await run_exposed_files_checks("https://example.com")

    assert result.exposed == ()
    assert result.findings == ()


@pytest.mark.asyncio()
async def test_run_exposed_files_checks_fetch_ok_false_si_toutes_echouent() -> None:
    """Si toutes les requêtes échouent (None), fetch_ok doit être False."""
    with patch("app.services.path_checks.core.fetch_url", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = None

        result = await run_exposed_files_checks("https://example.com")

    assert result.fetch_ok is False
    assert result.exposed == ()


def test_exposed_files_check_result_to_dict() -> None:
    """to_dict() sérialise correctement pour l'événement SSE result."""
    result = ExposedFilesCheckResult(
        exposed=(ExposedEndpoint("/.env", "critical", "Fichier .env exposé."),),
        findings=("Fichier .env exposé.",),
        fetch_ok=True,
    )
    d = result.to_dict()

    assert d["fetch_ok"] is True
    assert len(d["exposed"]) == 1
    assert d["exposed"][0]["path"] == "/.env"
    assert d["exposed"][0]["severity"] == "critical"
    assert d["exposed"][0]["message"] == "Fichier .env exposé."
    assert d["findings"] == ["Fichier .env exposé."]
