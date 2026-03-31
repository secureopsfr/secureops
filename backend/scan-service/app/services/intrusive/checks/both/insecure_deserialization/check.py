"""Check : Insecure Deserialization (Phase B — P1).

Spec : docs/verifications/intrusive/insecure-deserialization.md
Domaine : per-page
"""

from __future__ import annotations

import base64
import logging
import re

from app.config_loader import get_intrusive_scan_settings
from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.detector import detect_deserialization_error
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)

_CATEGORY = "insecure_deserialization"

# Marqueurs d'objets sérialisés dans cookies et corps
_JAVA_MAGIC = b"\xac\xed\x00\x05"  # Java ObjectOutputStream magic
_PHP_OBJECT_RE = re.compile(r'O:\d+:"[^"]+":')
_PYTHON_PICKLE_RE = re.compile(r"[\x80\x04\x95]")

# Probe inoffensif Java sérialisé (marqueur unique, pas d'exécution)
_JAVA_PROBE = base64.b64encode(b"\xac\xed\x00\x05ur\x00\x12[Ljava.lang.String;\xad\xd9\x95\x97\xd6\x97k\x03\x00\x00xp\x00\x00\x00\x00").decode()


def _looks_like_serialized(value: str) -> bool:
    """Heuristique : la valeur ressemble-t-elle à un objet sérialisé."""
    try:
        decoded = base64.b64decode(value + "==")
        if decoded[:4] == _JAVA_MAGIC:
            return True
    except Exception:
        pass
    if _PHP_OBJECT_RE.search(value):
        return True
    return False


async def run(
    url: str,
    *,
    scan_type: str = "frontend",
    credentials: ScanCredentials | None = None,
) -> list[Finding]:
    """Détecte les vulnérabilités de désérialisation non sécurisée."""
    cfg = get_intrusive_scan_settings()
    client = IntrusiveHTTPClient(
        credentials=credentials,
        timeout=cfg.probe_timeout,
        jitter_min_ms=cfg.jitter_min_ms,
        jitter_max_ms=cfg.jitter_max_ms,
    )
    findings: list[Finding] = []

    # Récupérer la page pour analyser les cookies et le corps
    try:
        page = await client.get(url)
        if not page.success:
            return []
    except Exception:
        return []

    # Vérifier les cookies de session pour des marqueurs de sérialisation
    set_cookie = page.headers.get("set-cookie") or ""
    cookie_match = re.search(r"([^=;\s]+)=([^;\s]+)", set_cookie)
    if cookie_match:
        cookie_value = cookie_match.group(2)
        if _looks_like_serialized(cookie_value):
            # Envoyer un probe Java sérialisé modifié
            try:
                modified_client = IntrusiveHTTPClient(
                    credentials=None,
                    timeout=cfg.probe_timeout,
                    jitter_min_ms=50,
                    jitter_max_ms=100,
                )
                probe = await modified_client.get(
                    url,
                    headers={"Cookie": f"{cookie_match.group(1)}={_JAVA_PROBE}"},
                )
                detection = detect_deserialization_error(probe.body)
                if detection.matched:
                    findings.append(
                        make_finding(
                            slug="intrusive-insecure-deserialization",
                            category=_CATEGORY,
                            title="Désérialisation non sécurisée — erreur révélatrice",
                            severity="critical",
                            evidence=(f"Cookie '{cookie_match.group(1)}' semble sérialisé. " f"Probe Java → {detection.evidence}"),
                        )
                    )
            except Exception:
                logger.debug("deserialization probe failed for %s", url, exc_info=True)

    return findings
