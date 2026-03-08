"""Tests unitaires pour les vérifications robots.txt (app.services.robots_txt.checks)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.robots_txt import RobotsTxtCheckResult, SensitiveRoute, run_robots_txt_checks


@pytest.mark.asyncio()
async def test_run_robots_txt_checks_404() -> None:
    """404 sur robots.txt → pas de findings, fetch_ok True."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = ""

    with patch("app.services.robots_txt.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        result = await run_robots_txt_checks("https://example.com", client=MagicMock())

    assert isinstance(result, RobotsTxtCheckResult)
    assert result.disallow_paths == ()
    assert result.sensitive_routes == ()
    assert result.findings == ()
    assert result.fetch_ok is True


@pytest.mark.asyncio()
async def test_run_robots_txt_checks_extract_disallow() -> None:
    """robots.txt avec Disallow → chemins extraits et routes sensibles signalées."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /config/
# Comment
Disallow: /backup/
"""

    with patch("app.services.robots_txt.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        result = await run_robots_txt_checks("https://example.com", client=MagicMock())

    assert len(result.disallow_paths) >= 4
    assert "/admin/" in result.disallow_paths
    assert "/api/" in result.disallow_paths
    assert "/config/" in result.disallow_paths
    assert "/backup/" in result.disallow_paths
    assert len(result.sensitive_routes) >= 4
    assert any(r.path == "/admin/" for r in result.sensitive_routes)
    assert result.fetch_ok is True
    assert len(result.findings) >= 4


@pytest.mark.asyncio()
async def test_run_robots_txt_checks_api_public_exception() -> None:
    """Disallow: /api/public/ n'est pas signalé comme sensible (exception)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """User-agent: *
Disallow: /api/public/
"""

    with patch("app.services.robots_txt.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        result = await run_robots_txt_checks("https://example.com", client=MagicMock())

    assert "/api/public/" in result.disallow_paths
    assert not any(r.path == "/api/public/" for r in result.sensitive_routes)
    assert result.fetch_ok is True


@pytest.mark.asyncio()
async def test_run_robots_txt_checks_crawl_delay_and_sitemap() -> None:
    """robots.txt avec Crawl-delay et Sitemap: → extraits."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """User-agent: *
Crawl-delay: 10
Sitemap: https://example.com/sitemap.xml
Disallow: /admin/
"""

    with patch("app.services.robots_txt.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        result = await run_robots_txt_checks("https://example.com", client=MagicMock())

    assert result.fetch_ok is True
    assert result.crawl_delay == 10
    assert result.sitemap_urls == ("https://example.com/sitemap.xml",)
    assert result.allow_paths == ()
    assert any("Crawl-delay" in f for f in result.findings)


@pytest.mark.asyncio()
async def test_run_robots_txt_checks_fetch_fails() -> None:
    """get_with_client retourne None → fetch_ok False."""
    with patch("app.services.robots_txt.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        result = await run_robots_txt_checks("https://example.com", client=MagicMock())

    assert result.fetch_ok is False
    assert len(result.findings) >= 1
    assert "Impossible" in result.findings[0]


def test_robots_txt_check_result_to_dict() -> None:
    """to_dict() sérialise correctement pour l'événement SSE result."""
    result = RobotsTxtCheckResult(
        disallow_paths=("/admin/", "/api/"),
        allow_paths=(),
        sensitive_routes=(SensitiveRoute("/admin/", "admin", "high"),),
        findings=("Disallow: /admin/ (route potentiellement sensible : admin).",),
        fetch_ok=True,
        found=True,
        crawl_delay=None,
        sitemap_urls=(),
    )
    d = result.to_dict()

    assert d["fetch_ok"] is True
    assert d["disallow_paths"] == ["/admin/", "/api/"]
    assert d["allow_paths"] == []
    assert len(d["sensitive_routes"]) == 1
    assert d["sensitive_routes"][0]["path"] == "/admin/"
    assert d["sensitive_routes"][0]["pattern"] == "admin"
    assert d["sensitive_routes"][0]["severity"] == "high"
    assert d["findings"] == ["Disallow: /admin/ (route potentiellement sensible : admin)."]
