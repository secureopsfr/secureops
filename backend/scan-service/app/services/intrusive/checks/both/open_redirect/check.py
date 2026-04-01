"""Check : Open Redirect actif (Phase A — P0).

Spec : docs/verifications/intrusive/redirections-actives.md
Domaine : per-page
scan_type : frontend (HTML links + query) | backend (query + body JSON)
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_REDIRECT_PARAMS, extract_html_params, extract_query_params
from app.services.intrusive.lib.redirect_module import probe_open_redirect

logger = logging.getLogger(__name__)

_CATEGORY = "open_redirect"
_MAX_PARAMS = 8


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les redirections ouvertes non contrôlées."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )

    # Récupérer la page pour extraire les paramètres HTML (frontend)
    html_body = ""
    if scan_type == "frontend":
        try:
            page = await client.get(url)
            if page.success:
                html_body = page.body
        except Exception:
            pass

    # Collecter les paramètres candidats
    candidate_names: set[str] = set(COMMON_REDIRECT_PARAMS)
    for p in extract_query_params(url):
        candidate_names.add(p.name)
    if scan_type == "frontend" and html_body:
        for p in extract_html_params(html_body, url):
            candidate_names.add(p.name)

    target_host = urlparse(url).netloc.split(":")[0]
    findings: list[Finding] = []
    tested = 0

    for param_name in list(candidate_names)[:_MAX_PARAMS]:
        if tested >= cfg.budget_per_category:
            break
        try:
            external = await probe_open_redirect(client, url, param_name, target_host)
            tested += 1
            if external:
                # Sévérité selon si les credentials sont transmis à la cible externe
                severity = "medium"
                findings.append(
                    make_finding(
                        slug="intrusive-open-redirect",
                        category=_CATEGORY,
                        title="Open redirect détecté",
                        severity=severity,
                        evidence=f"Paramètre '{param_name}' redirige vers {external}",
                    )
                )
                break  # Un finding suffit par URL
        except Exception:
            logger.debug("open_redirect probe failed for param=%s url=%s", param_name, url, exc_info=True)

    return findings
