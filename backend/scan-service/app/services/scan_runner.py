"""Exécution du scan et retour du résultat en JSON (pour appels internes, ex. scheduler)."""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.catalogue.category_summaries import build_category_summaries
from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.errors.fetch_errors import build_sse_error_payload
from app.models.scan_result import ScanResult
from app.services.cache import checks as cache_checks
from app.services.cookies import check_cookies_from_response
from app.services.directory_listing import run_directory_listing_checks
from app.services.exposed_files import run_exposed_files_checks
from app.services.normalization import normalize_results
from app.services.robots_txt import run_robots_txt_checks
from app.services.scoring import compute_score
from app.services.security_headers import check_security_headers_from_response
from app.services.sitemap import run_sitemap_checks
from app.services.tech_fingerprinting import check_tech_fingerprinting_from_response
from app.services.tls import run_tls_checks
from app.services.tls.posture import compute_tls_posture
from app.utils.http_fetch import get_with_client_or_error, scan_client
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import build_https_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


@dataclass
class ScanContext:
    """Contexte partagé entre les étapes (réutilisé depuis scan_stream)."""

    normalized_url: str
    https_url: str
    client: object
    https_response: object
    results: dict = field(default_factory=dict)


class ScanRunError(Exception):
    """Erreur lors de l'exécution du scan (site inaccessible, timeout, etc.)."""

    def __init__(self, message: str, status_code: int = 500):
        """Initialise l'exception avec un message et un code HTTP.

        Args:
            message: Message d'erreur descriptif.
            status_code: Code HTTP associé (défaut 500).
        """
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# Étapes identiques à scan_stream
_SCAN_STEPS: list[tuple[str, Callable]] = [
    ("tls", lambda ctx: run_tls_checks(ctx.normalized_url, https_response=ctx.https_response, client=ctx.client)),
    ("headers", lambda ctx: check_security_headers_from_response(ctx.https_response)),
    (
        "cache",
        lambda ctx: cache_checks.check_cache_from_response(
            ctx.https_response,
            ctx.https_url,
            ctx.client,
        ),
    ),
    ("cookies", lambda ctx: check_cookies_from_response(ctx.https_response, is_https=ctx.results["tls"].https_enabled)),
    ("exposed_files", lambda ctx: run_exposed_files_checks(ctx.https_url, client=ctx.client)),
    ("directory_listing", lambda ctx: run_directory_listing_checks(ctx.https_url, client=ctx.client)),
    ("robots_txt", lambda ctx: run_robots_txt_checks(ctx.https_url, client=ctx.client)),
    (
        "sitemap",
        lambda ctx: run_sitemap_checks(
            ctx.https_url,
            robots_txt_result=ctx.results.get("robots_txt"),
            client=ctx.client,
        ),
    ),
    ("tech_fingerprinting", lambda ctx: check_tech_fingerprinting_from_response(ctx.https_response)),
]


async def run_scan_to_result(url: str) -> dict:
    """Exécute le scan et retourne le payload dict (success).

    Utilisé par le scheduler user-service pour les scans planifiés.

    Args:
        url: URL à scanner.

    Returns:
        dict: Payload avec url, timestamp, duration, score, findings, status.

    Raises:
        URLValidationError: URL invalide.
        ScanRunError: Site inaccessible, timeout, erreur TLS, etc.
    """
    start = time.monotonic()
    scan_global = get_scan_timeouts().scan_global

    def _over_global() -> bool:
        return (time.monotonic() - start) > scan_global

    normalized_url = validate_and_normalize_url(url)

    if _over_global():
        raise ScanRunError("Timeout global dépassé", status_code=408)

    await check_ssrf(normalized_url, timeout=get_ssrf_settings().dns_timeout)

    if _over_global():
        raise ScanRunError("Timeout global dépassé", status_code=408)

    https_url = build_https_url(normalized_url)

    async with scan_client() as client:
        fetch_result = await get_with_client_or_error(client, https_url, follow_redirects=True)

        if not fetch_result.success:
            payload = build_sse_error_payload(fetch_result)
            raise ScanRunError(
                payload.get("message", "Site inaccessible"),
                status_code=payload.get("status_code", 503),
            )

        https_response = fetch_result.response
        ctx = ScanContext(
            normalized_url=normalized_url,
            https_url=https_url,
            client=client,
            https_response=https_response,
        )

        for step_name, step_fn in _SCAN_STEPS:
            if _over_global():
                raise ScanRunError("Timeout global dépassé", status_code=408)
            result = step_fn(ctx)
            if asyncio.iscoroutine(result):
                result = await result
            ctx.results[step_name] = result

    findings = normalize_results(ctx.results)
    findings_tuple = tuple(findings)
    score = compute_score(findings_tuple)
    duration = time.monotonic() - start
    timestamp = datetime.now(timezone.utc).isoformat()

    scan_result = ScanResult(
        url=normalized_url,
        timestamp=timestamp,
        duration=duration,
        score=score,
        findings=findings_tuple,
    )
    payload = scan_result.to_dict()
    tls_result = ctx.results["tls"]
    tls_posture = compute_tls_posture(tls_result)
    tls_version = getattr(tls_result, "tls_version", None)
    category_summaries = build_category_summaries(findings_tuple, tls_posture=tls_posture, tls_version=tls_version)
    payload["category_summaries"] = category_summaries
    payload["total_tests_count"] = sum(s.get("checks_count", 0) for s in category_summaries)
    payload["status"] = "success"
    return payload
