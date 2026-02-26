"""Vérifications des en-têtes de sécurité HTTP (roadmap §3.2).

Vérifie la présence des en-têtes configurés dans security_headers (settings.yml).
"""

from dataclasses import dataclass

import httpx

from app.config_loader import get_security_headers_settings
from app.utils.headers import get_header_insensitive


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

    def to_dict(self) -> dict:
        """Sérialise le résultat pour l'événement SSE result."""
        return {
            "headers_present": list(self.headers_present),
            "headers_missing": list(self.headers_missing),
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


def check_security_headers_from_response(response: httpx.Response | None) -> SecurityHeadersCheckResult:
    """Vérifie la présence des en-têtes de sécurité sur une réponse HTTPS.

    Analyse les en-têtes de la réponse (sans effectuer de requête). Utilisé avec
    la réponse pré-fetchée par get_with_client (scan_client) pour éviter les appels dupliqués.

    Args:
        response: Réponse HTTP (ou None si le fetch a échoué).

    Returns:
        SecurityHeadersCheckResult: En-têtes présents/absents et findings.
    """
    findings: list[str] = []
    present: list[str] = []
    missing: list[str] = []

    headers_config = get_security_headers_settings()

    if response is None:
        findings.append("Impossible de récupérer les en-têtes (connexion refusée ou timeout).")
        return SecurityHeadersCheckResult(
            headers_present=(),
            headers_missing=tuple(h.name for h in headers_config),
            findings=tuple(findings),
            fetch_ok=False,
        )

    for cfg in headers_config:
        header_name = cfg.name
        msg_absent = cfg.message_absent
        expected_value = cfg.expected_value
        actual_value = get_header_insensitive(response, header_name)
        if actual_value is not None and expected_value and actual_value.strip().lower() != expected_value.lower():
            findings.append(f"{header_name} présent mais valeur incorrecte (attendu : {expected_value}).")
        if actual_value is not None:
            present.append(header_name)
        else:
            missing.append(header_name)
            findings.append(msg_absent)

    return SecurityHeadersCheckResult(
        headers_present=tuple(present),
        headers_missing=tuple(missing),
        findings=tuple(findings),
        fetch_ok=True,
    )
