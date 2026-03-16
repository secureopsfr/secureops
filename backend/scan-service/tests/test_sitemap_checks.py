"""Tests unitaires pour les vérifications sitemap (passive)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.passive.frontend.robots_txt.checks import RobotsTxtCheckResult
from app.services.passive.frontend.sitemap import SensitiveSitemapUrl, SitemapCheckResult, run_sitemap_checks


@pytest.mark.asyncio()
async def test_run_sitemap_checks_no_sitemap_found() -> None:
    """Aucun sitemap trouvé (ni déclaré ni fallback) → sitemap_found False."""
    with patch("app.services.passive.frontend.sitemap.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(status_code=404, text="")
        robots_result = RobotsTxtCheckResult(
            disallow_paths=(),
            allow_paths=(),
            sensitive_routes=(),
            findings=(),
            fetch_ok=True,
            found=True,
            crawl_delay=None,
            sitemap_urls=(),
        )
        result = await run_sitemap_checks(
            "https://example.com",
            robots_txt_result=robots_result,
            client=MagicMock(),
        )

    assert result.sitemap_found is False
    assert result.sitemap_undeclared is False  # Pas de sitemap trouvé → undeclared n'a pas de sens
    assert result.sensitive_urls == ()
    assert result.fetch_ok is True


@pytest.mark.asyncio()
async def test_run_sitemap_checks_sitemap_with_sensitive_url() -> None:
    """Sitemap avec URL sensible (admin) → finding."""
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/admin/dashboard</loc></url>
  <url><loc>https://example.com/blog</loc></url>
</urlset>"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/xml"}
    mock_resp.text = sitemap_xml

    with patch("app.services.passive.frontend.sitemap.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        robots_result = RobotsTxtCheckResult(
            disallow_paths=(),
            allow_paths=(),
            sensitive_routes=(),
            findings=(),
            fetch_ok=True,
            found=True,
            crawl_delay=None,
            sitemap_urls=(),
        )
        result = await run_sitemap_checks(
            "https://example.com",
            robots_txt_result=robots_result,
            client=MagicMock(),
        )

    assert result.sitemap_found is True
    assert result.sitemap_undeclared is True
    assert len(result.sensitive_urls) == 1
    assert result.sensitive_urls[0].path == "/admin/dashboard"
    assert result.sensitive_urls[0].pattern == "admin"


@pytest.mark.asyncio()
async def test_run_sitemap_checks_uses_robots_sitemap_url() -> None:
    """Si robots.txt a Sitemap:, utilise cette URL."""
    sitemap_xml = """<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://example.com/</loc></url></urlset>"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/xml"}
    mock_resp.text = sitemap_xml

    with patch("app.services.passive.frontend.sitemap.checks.get_with_client", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        robots_result = RobotsTxtCheckResult(
            disallow_paths=(),
            allow_paths=(),
            sensitive_routes=(),
            findings=(),
            fetch_ok=True,
            found=True,
            crawl_delay=None,
            sitemap_urls=("https://example.com/sitemap.xml",),
        )
        result = await run_sitemap_checks(
            "https://example.com",
            robots_txt_result=robots_result,
            client=MagicMock(),
        )

    assert result.sitemap_found is True
    assert result.sitemap_undeclared is False
    mock_get.assert_called_once()
    # get_with_client(client, url, ...) : 2e arg = url
    called_url = mock_get.call_args[0][1]
    assert "sitemap.xml" in str(called_url)


def test_sitemap_check_result_to_dict() -> None:
    """to_dict() sérialise correctement."""
    result = SitemapCheckResult(
        sitemap_found=True,
        sitemap_undeclared=True,
        sensitive_urls=(SensitiveSitemapUrl("https://ex.com/admin", "/admin", "admin", "high"),),
        fetch_ok=True,
    )
    d = result.to_dict()

    assert d["sitemap_found"] is True
    assert d["sitemap_undeclared"] is True
    assert len(d["sensitive_urls"]) == 1
    assert d["sensitive_urls"][0]["path"] == "/admin"
    assert d["sensitive_urls"][0]["pattern"] == "admin"
