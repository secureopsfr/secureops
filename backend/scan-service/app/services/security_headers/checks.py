"""Vérifications des en-têtes de sécurité HTTP (roadmap §3.2).

Vérifie la présence de : Content-Security-Policy, Strict-Transport-Security,
X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.
"""

import ssl
from dataclasses import dataclass

import httpx

from app.config_loader import get_scan_timeouts
from app.utils.url_helpers import build_https_url

# En-têtes à vérifier (nom, message si absent, valeur attendue ou None)
_HEADERS_TO_CHECK: tuple[tuple[str, str, str | None], ...] = (
    ("Content-Security-Policy", "Content-Security-Policy absent : risque XSS accru.", None),
    ("Strict-Transport-Security", "Strict-Transport-Security absent : risque de downgrade HTTPS→HTTP.", None),
    ("X-Frame-Options", "X-Frame-Options absent : risque de clickjacking.", None),
    ("X-Content-Type-Options", "X-Content-Type-Options absent : risque de MIME sniffing.", "nosniff"),
    ("Referrer-Policy", "Referrer-Policy absent : risque de fuite d'URLs sensibles.", None),
    ("Permissions-Policy", "Permissions-Policy absent : APIs navigateur accessibles par défaut.", None),
)


def _ssl_context_for_scan() -> ssl.SSLContext:
    """Contexte SSL permissif pour le scan (certificats non vérifiés)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


@dataclass
class SecurityHeadersCheckResult:
    """Résultat des vérifications Security Headers.

    Attributes:
        headers_present (tuple[str, ...]): En-têtes présents dans la réponse.
        headers_missing (tuple[str, ...]): En-têtes absents.
        findings (tuple[str, ...]): Liste des findings (en-têtes manquants).
        fetch_ok (bool): True si la requête a abouti.
    """

    headers_present: tuple[str, ...]
    headers_missing: tuple[str, ...]
    findings: tuple[str, ...]
    fetch_ok: bool


async def run_security_headers_checks(url: str) -> SecurityHeadersCheckResult:
    """Vérifie la présence des en-têtes de sécurité sur la réponse HTTPS.

    Effectue un GET vers l'URL HTTPS (en suivant les redirections) et analyse
    les en-têtes de la réponse finale.

    Args:
        url: URL normalisée à scanner.

    Returns:
        SecurityHeadersCheckResult: En-têtes présents/absents et findings.
    """
    timeouts = get_scan_timeouts()
    https_url = build_https_url(url)
    findings: list[str] = []
    present: list[str] = []
    missing: list[str] = []

    try:
        async with httpx.AsyncClient(
            verify=_ssl_context_for_scan(),
            follow_redirects=True,
            timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
        ) as client:
            response = await client.get(https_url)
            headers_lower = {k.lower(): k for k in response.headers}

            for header_name, msg_absent, expected_value in _HEADERS_TO_CHECK:
                header_lower = header_name.lower()
                if header_lower in headers_lower:
                    if expected_value:
                        actual = response.headers.get(header_name, "").strip().lower()
                        if actual != expected_value.lower():
                            findings.append("X-Content-Type-Options présent mais valeur incorrecte (attendu : nosniff).")
                    present.append(header_name)
                else:
                    missing.append(header_name)
                    findings.append(msg_absent)

    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        findings.append("Impossible de récupérer les en-têtes (connexion refusée ou timeout).")
        return SecurityHeadersCheckResult(
            headers_present=(),
            headers_missing=tuple(h for h, _, _ in _HEADERS_TO_CHECK),
            findings=tuple(findings),
            fetch_ok=False,
        )
    except Exception as e:
        findings.append(f"Impossible de récupérer les en-têtes : {e!s}")
        return SecurityHeadersCheckResult(
            headers_present=(),
            headers_missing=tuple(h for h, _, _ in _HEADERS_TO_CHECK),
            findings=tuple(findings),
            fetch_ok=False,
        )

    return SecurityHeadersCheckResult(
        headers_present=tuple(present),
        headers_missing=tuple(missing),
        findings=tuple(findings),
        fetch_ok=True,
    )
