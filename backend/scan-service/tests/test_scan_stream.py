"""Tests unitaires du générateur SSE scan_stream."""

import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.errors.fetch_errors import FetchResult
from app.services.scan_stream import scan_stream_generator
from app.services.tls.checks import TlsCheckResult


def _parse_sse_chunk(chunk: str) -> tuple[str, dict]:
    event = "message"
    data = {}
    for line in chunk.strip().splitlines():
        if line.startswith("event: "):
            event = line[7:].strip()
        elif line.startswith("data: "):
            data = json.loads(line[6:])
    return event, data


@pytest.mark.asyncio()
async def test_scan_stream_emits_result_with_success_status() -> None:
    """Le stream SSE émet un result contenant status=success."""
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
        patch("app.services.scan_stream.scan_client", _fake_scan_client),
        patch("app.services.scan_stream.get_with_client_or_error", new_callable=AsyncMock, return_value=fetch_result_ok),
        patch("app.services.scan_stream.check_ssrf", new_callable=AsyncMock),
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
        chunks = []
        async for chunk in scan_stream_generator("https://example.com"):
            chunks.append(chunk)

    events = [_parse_sse_chunk(c) for c in chunks]
    result_data = [d for ev, d in events if ev == "result"][0]
    assert result_data["status"] == "success"
    assert result_data["scan_type"] == "frontend"
