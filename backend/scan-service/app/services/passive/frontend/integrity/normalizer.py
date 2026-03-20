"""Normalisation des résultats Intégrité en list[Finding].

Utilise les issues typées (IntegrityIssue.kind) — aucune correspondance de chaînes.
"""

from app.catalogue.owasp import get_owasp_categories
from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.frontend.integrity.checks import IntegrityCheckResult

_ISSUE_MAP: dict[str, tuple[str, str, str]] = {
    # kind → (slug, title, severity)
    "sri_missing": ("integrity-sri-external-missing", "Ressources externes sans SRI", "medium"),
    "csp_absent": ("integrity-csp-not-present-advanced-checks-skipped", "CSP absente : tests avancés non appliqués", "info"),
    "inline_no_nonce": ("integrity-script-inline-no-nonce", "Scripts inline sans nonce avec CSP", "medium"),
    "password_autocomplete": ("integrity-form-password-autocomplete", "Champs password sans autocomplete adapté", "low"),
    "target_blank": ("integrity-target-blank-noopener", 'Liens target="_blank" sans noopener', "low"),
    "robots_missing": ("integrity-meta-robots-missing", "Meta robots absente sur page sensible", "low"),
    "robots_no_noindex": ("integrity-meta-robots-no-noindex", "Meta robots sans noindex sur page sensible", "low"),
    "forms_post_without_csrf": ("integrity-forms-post-without-csrf", "Formulaires POST sans champ CSRF", "low"),
    "connection_failed": ("integrity-connection-failed", "Analyse d'intégrité impossible", "info"),
}

_GENERIC = ("integrity-generic", "Problème d'intégrité ou de sous-ressources", "medium")


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


def normalize(result: IntegrityCheckResult) -> list[Finding]:
    """Convertit IntegrityCheckResult en list[Finding] via les issues typées."""
    findings: list[Finding] = []

    if not result.fetch_ok and not result.issues:
        findings.append(
            _finding(
                "integrity-connection-failed",
                "integrity",
                "Analyse d'intégrité impossible",
                "info",
                "Vérifications d'intégrité impossibles : réponse HTTPS indisponible ou illisible.",
            )
        )
        return findings

    for issue in result.issues:
        slug, title, severity = _ISSUE_MAP.get(issue.kind, _GENERIC)
        findings.append(_finding(slug, "integrity", title, severity, issue.message))
    return findings
