"""Normalisation des résultats TLS en list[Finding]."""

import re

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.both.tls.checks import TlsCheckResult


def _finding(slug: str, category: str, title: str, severity: str, evidence: str) -> Finding:
    sev = severity.lower() if severity else "medium"
    return Finding(
        id=slug,
        category=category,
        title=title,
        severity=sev,
        evidence=evidence,
        recommendation=get_recommendation(slug),
        references=get_references(slug),
    )


def _extract_days_until_expiry(msg: str) -> int | None:
    m = re.search(r"(?:dans|in)\s+(\d+)\s+(?:jour|day)", msg, re.IGNORECASE)
    return int(m.group(1)) if m else None


def normalize(result: TlsCheckResult) -> list[Finding]:
    """Convertit TlsCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        from app.constants import MSG_HTTPS_UNAVAILABLE

        findings.append(_finding("tls-connection-failed", "tls", "Connexion HTTPS impossible", "high", MSG_HTTPS_UNAVAILABLE))
        return findings
    if not result.https_enabled:
        from app.constants import MSG_HTTPS_UNAVAILABLE

        findings.append(_finding("tls-https-disabled", "tls", "HTTPS non activé", "critical", MSG_HTTPS_UNAVAILABLE))
        return findings

    if result.http_redirects_to_https is False:
        findings.append(_finding("tls-no-redirect", "tls", "Pas de redirection HTTP→HTTPS", "high", "Pas de redirection HTTP→HTTPS détectée."))
    if result.certificate_status == "expired":
        findings.append(_finding("tls-cert-expired", "tls", "Certificat expiré", "critical", "Le certificat présenté par le serveur est expiré."))
    elif result.certificate_status == "self_signed":
        findings.append(
            _finding("tls-cert-self-signed", "tls", "Certificat auto-signé", "high", "Le certificat présenté par le serveur est auto-signé.")
        )
    elif result.certificate_status == "not_yet_valid":
        findings.append(
            _finding(
                "tls-cert-not-yet-valid",
                "tls",
                "Certificat pas encore valide",
                "medium",
                "Le certificat présenté par le serveur n'est pas encore valide.",
            )
        )
    elif result.certificate_status == "expires_soon":
        expiry_msg = next((m for m in result.findings if "expire bientôt" in m.lower() or "expires soon" in m.lower()), "")
        days = _extract_days_until_expiry(expiry_msg)
        severity = "low" if days is not None and days >= 15 else "medium"
        findings.append(
            _finding("tls-cert-expires-soon", "tls", "Certificat expire bientôt", severity, expiry_msg or "Le certificat approche de son expiration.")
        )
    if result.chain_incomplete or any("chaîne" in m.lower() and "incomplète" in m.lower() for m in result.findings):
        findings.append(
            _finding(
                "tls-chain-incomplete",
                "tls",
                "Chaîne de certificats incomplète",
                "medium",
                "La chaîne de certificats est incomplète (intermédiaires manquants).",
            )
        )
    if result.tls_versions_obsolete:
        versions = ", ".join(result.tls_versions_obsolete)
        findings.append(
            _finding("tls-versions-obsolete", "tls", "Versions TLS obsolètes", "medium", f"Versions TLS obsolètes détectées: {versions}.")
        )
    return findings
