"""Exécution du scan et retour du résultat en JSON (pour appels internes, ex. scheduler)."""

import asyncio
import logging
import time

from app.config_loader import get_scan_timeouts, get_ssrf_settings
from app.errors.fetch_errors import build_sse_error_payload
from app.services.passive._scan_core import SCAN_STEPS, ScanContext, build_result_payload
from app.utils.http_fetch import get_with_client_or_error, http_request_category, log_http_metrics, scan_client
from app.utils.ssrf import check_ssrf
from app.utils.url_helpers import get_scan_base_url
from app.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


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

    https_url = get_scan_base_url(normalized_url)

    async with scan_client() as client:
        try:
            with http_request_category("initial_fetch"):
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

            for step_name, step_fn in SCAN_STEPS:
                if _over_global():
                    raise ScanRunError("Timeout global dépassé", status_code=408)
                with http_request_category(step_name):
                    result = step_fn(ctx)
                    if asyncio.iscoroutine(result):
                        result = await result
                ctx.results[step_name] = result
        finally:
            log_http_metrics(client, "scan-runner", url=https_url)

    return build_result_payload(normalized_url, ctx.results, start)
