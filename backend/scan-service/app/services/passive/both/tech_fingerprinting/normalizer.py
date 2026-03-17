"""Normalisation des résultats Tech Fingerprinting en list[Finding]."""

from app.catalogue.owasp import get_owasp_categories
from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.both.tech_fingerprinting.checks import TechFingerprintingCheckResult


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
        owasp_categories=get_owasp_categories(slug),
    )


def normalize(result: TechFingerprintingCheckResult) -> list[Finding]:
    """Convertit TechFingerprintingCheckResult en list[Finding] (severity info)."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        from app.constants import MSG_HEADERS_ANALYSIS_UNAVAILABLE

        findings.append(
            _finding(
                "tech_fingerprinting-connection-failed", "tech_fingerprinting", "En-têtes inaccessibles", "info", MSG_HEADERS_ANALYSIS_UNAVAILABLE
            )
        )
        return findings
    for v in result.vulnerable_versions:
        ev = f"{v.product} {v.version} (version minimale recommandée : {v.min_safe_version})"
        findings.append(
            _finding(
                "tech_fingerprinting-vulnerable-version",
                "tech_fingerprinting",
                f"Version potentiellement vulnérable : {v.product} {v.version}",
                "medium",
                ev,
            )
        )
    if result.server:
        findings.append(
            _finding("tech_fingerprinting-server-detected", "tech_fingerprinting", "Serveur détecté", "info", f"Serveur détecté : {result.server}")
        )
    if result.runtime:
        findings.append(
            _finding("tech_fingerprinting-runtime-detected", "tech_fingerprinting", "Runtime détecté", "info", f"Runtime détecté : {result.runtime}")
        )
    if result.framework_cms:
        txt = result.framework_cms if not result.framework_cms_version else f"{result.framework_cms} {result.framework_cms_version}"
        findings.append(
            _finding(
                "tech_fingerprinting-framework-detected", "tech_fingerprinting", "Framework/CMS détecté", "info", f"Framework/CMS détecté : {txt}"
            )
        )
    if not findings:
        findings.append(
            _finding(
                "tech_fingerprinting-stack-unknown", "tech_fingerprinting", "Stack non identifiée", "info", "Stack : non identifiée (ou masquée)."
            )
        )
    return findings
