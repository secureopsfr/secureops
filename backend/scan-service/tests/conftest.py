"""Fixtures partagées pour les tests du scan-service."""

import json
from contextlib import asynccontextmanager, contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.errors.fetch_errors import FetchResult
from app.main import app
from app.services.directory_listing import DirectoryListingCheckResult
from app.services.exposed_files import ExposedFilesCheckResult
from app.services.robots_txt import RobotsTxtCheckResult
from app.services.tls.checks import TlsCheckResult


@contextmanager
def patch_scan_checks(**overrides):
    """Mocke tous les checks du scan avec des résultats par défaut.

    Surcharge possible via overrides (ex. run_exposed_files_checks=custom_result).
    Utilisé pour les tests du routeur sans requêtes réseau.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.content = b""

    tls_result = overrides.pop("tls_result", None) or TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(),
    )
    exposed_result = overrides.pop("exposed_result", None) or ExposedFilesCheckResult(exposed=(), findings=(), fetch_ok=True)
    directory_listing_result = overrides.pop("directory_listing_result", None) or DirectoryListingCheckResult(exposed=(), findings=(), fetch_ok=True)
    robots_txt_result = overrides.pop("robots_txt_result", None) or RobotsTxtCheckResult(
        disallow_paths=(), sensitive_routes=(), findings=(), fetch_ok=True
    )

    @asynccontextmanager
    async def _fake_scan_client():
        yield MagicMock()

    fetch_result_ok = FetchResult(
        success=True,
        response=mock_response,
        error_type="",
        message="",
        status_code=200,
        details=None,
    )
    with (
        patch("app.services.scan_stream.check_ssrf", new_callable=AsyncMock),
        patch("app.services.scan_stream.scan_client", _fake_scan_client),
        patch("app.services.scan_stream.get_with_client_or_error", new_callable=AsyncMock, return_value=fetch_result_ok),
        patch("app.services.scan_stream.run_tls_checks", new_callable=AsyncMock, return_value=tls_result),
        patch("app.services.scan_stream.run_exposed_files_checks", new_callable=AsyncMock, return_value=exposed_result),
        patch(
            "app.services.scan_stream.run_directory_listing_checks",
            new_callable=AsyncMock,
            return_value=directory_listing_result,
        ),
        patch(
            "app.services.scan_stream.run_robots_txt_checks",
            new_callable=AsyncMock,
            return_value=robots_txt_result,
        ),
    ):
        yield


def parse_sse_events(response) -> list[tuple[str, dict]]:
    """Parse le corps SSE en liste de (event, data).

    Args:
        response: Réponse HTTP avec body text (stream SSE).

    Returns:
        list[tuple[str, dict]]: Liste de (event_type, data_dict).
    """
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


@pytest.fixture()
def client() -> TestClient:
    """Client de test FastAPI pour les routes."""
    return TestClient(app)
