"""Check : LFI / RFI — Local/Remote File Inclusion (Phase B — P1).

Spec : docs/verifications/intrusive/file-inclusion-lfi-rfi.md
Domaine : per-page
"""

from __future__ import annotations

import logging

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_path_traversal
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient
from app.services.intrusive.lib.param_extractor import COMMON_FILE_PARAMS, extract_query_params, inject_query_param
from app.services.intrusive.lib.payload_engine import PayloadCategory, get_payloads

logger = logging.getLogger(__name__)

_CATEGORY = "lfi_rfi"
_MAX_PARAMS = 3

_PHP_WRAPPER_PAYLOADS = [
    "php://filter/convert.base64-encode/resource=index.php",
    "php://filter/read=convert.base64-encode/resource=../config.php",
    "php://input",
]


async def run(  # noqa: C901
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités LFI/RFI."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    candidate_names: set[str] = set(COMMON_FILE_PARAMS)
    for p in extract_query_params(url):
        candidate_names.add(p.name)

    payloads = get_payloads(PayloadCategory.PATH, budget=cfg.max_requests_per_param)

    for param_name in list(candidate_names)[:_MAX_PARAMS]:
        # LFI standard
        for payload in payloads[:2]:
            probe_url = inject_query_param(url, param_name, payload.raw)
            try:
                result = await client.get(probe_url)
                if not result.success:
                    continue
                detection = detect_path_traversal(result.body)
                if detection.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-lfi",
                            category=_CATEGORY,
                            title="LFI détectée — inclusion de fichier local",
                            severity="high",
                            evidence=(f"Param '{param_name}' → payload: {payload.raw!r} " f"→ {detection.evidence}"),
                        )
                    )
                    return findings
            except Exception:
                logger.debug("lfi probe failed param=%s", param_name, exc_info=True)

        # PHP wrappers (si PHP suspecté)
        for wrapper in _PHP_WRAPPER_PAYLOADS[:1]:
            probe_url = inject_query_param(url, param_name, wrapper)
            try:
                result = await client.get(probe_url)
                if result.success and result.status_code == 200 and len(result.body) > 100:
                    import base64

                    # Vérifier si le résultat est du base64 (PHP filter output)
                    try:
                        decoded = base64.b64decode(result.body.strip())
                        if b"<?php" in decoded or b"<?PHP" in decoded:
                            findings.append(
                                make_finding(
                                    slug="intrusive-lfi-php-wrapper",
                                    category=_CATEGORY,
                                    title="LFI via PHP filter — source PHP exposée",
                                    severity="critical",
                                    evidence=f"Param '{param_name}' → {wrapper!r} → source PHP décodée ({len(decoded)} octets)",
                                )
                            )
                            return findings
                    except Exception:
                        pass
            except Exception:
                pass

    return findings
