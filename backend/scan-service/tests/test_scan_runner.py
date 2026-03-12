"""Tests unitaires du scan runner (endpoint interne scheduler)."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.errors.fetch_errors import FetchResult
from app.services.scan_runner import ScanRunError, run_scan_to_result
from app.services.tls.checks import TlsCheckResult


@pytest.mark.asyncio()
async def test_run_scan_to_result_success() -> None:
    """run_scan_to_result retourne un payload succès normalisé."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.content = b""
    mock_response.text = ""
    fetch_result_ok = FetchResult(
        success=True,
        response=mock_response,
        error_type="",
        message="",
        status_code=200,
        details=None,
    )
    tls_result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(),
        fetch_ok=True,
        tls_version="TLS 1.3",
    )

    @asynccontextmanager
    async def _fake_scan_client():
        yield MagicMock()

    with (
        patch("app.services.scan_runner.scan_client", _fake_scan_client),
        patch("app.services.scan_runner.get_with_client_or_error", new_callable=AsyncMock, return_value=fetch_result_ok),
        patch("app.services.scan_runner.check_ssrf", new_callable=AsyncMock),
        patch("app.services._scan_core.run_tls_checks", new_callable=AsyncMock, return_value=tls_result),
        patch("app.services._scan_core.check_security_headers_from_response", return_value=MagicMock(findings=(), headers_missing=(), fetch_ok=True)),
        patch(
            "app.services._scan_core.cache_checks.check_cache_from_response",
            new_callable=AsyncMock,
            return_value=MagicMock(findings=(), fetch_ok=True),
        ),
        patch("app.services._scan_core.check_cookies_from_response", return_value=MagicMock(findings=(), cookies=(), fetch_ok=True)),
        patch(
            "app.services._scan_core.run_exposed_files_checks",
            new_callable=AsyncMock,
            return_value=MagicMock(exposed=(), findings=(), fetch_ok=True, exposed_403=()),
        ),
        patch(
            "app.services._scan_core.run_directory_listing_checks",
            new_callable=AsyncMock,
            return_value=MagicMock(exposed=(), findings=(), fetch_ok=True, exposed_403=()),
        ),
        patch(
            "app.services._scan_core.run_robots_txt_checks",
            new_callable=AsyncMock,
            return_value=MagicMock(fetch_ok=True, sensitive_routes=(), findings=(), crawl_delay=None),
        ),
        patch(
            "app.services._scan_core.run_sitemap_checks",
            new_callable=AsyncMock,
            return_value=MagicMock(sitemap_found=False, sitemap_undeclared=False, sensitive_urls=(), fetch_ok=True),
        ),
        patch(
            "app.services._scan_core.check_tech_fingerprinting_from_response",
            return_value=MagicMock(server=None, runtime=None, framework_cms=None, vulnerable_versions=(), findings=(), fetch_ok=True),
        ),
        patch("app.services._scan_core.check_information_disclosure_from_response", return_value=MagicMock(findings=(), fetch_ok=True)),
        patch("app.services._scan_core.check_integrity_from_response", return_value=MagicMock(findings=(), fetch_ok=True)),
        patch("app.services._scan_core.run_cors_cross_origin_checks", new_callable=AsyncMock, return_value=MagicMock(findings=(), fetch_ok=True)),
    ):
        result = await run_scan_to_result("https://example.com")

    assert result["status"] == "success"
    assert result["scan_type"] == "frontend"
    assert "score" in result
    assert "findings" in result


@pytest.mark.asyncio()
async def test_run_scan_to_result_fetch_error_raises_scan_run_error() -> None:
    """run_scan_to_result remonte une ScanRunError si fetch HTTPS échoue."""
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
        patch("app.services.scan_runner.scan_client", _fake_scan_client),
        patch("app.services.scan_runner.get_with_client_or_error", new_callable=AsyncMock, return_value=fetch_result_fail),
        patch("app.services.scan_runner.check_ssrf", new_callable=AsyncMock),
        pytest.raises(ScanRunError) as exc,
    ):
        await run_scan_to_result("https://example.com")

    assert exc.value.status_code == 503
