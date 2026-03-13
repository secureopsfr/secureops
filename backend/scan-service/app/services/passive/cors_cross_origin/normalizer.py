"""Normalisation des résultats CORS/cross-origin en list[Finding].

Utilise les issues typées (CorsIssue.kind) — aucune correspondance de chaînes.
"""

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.cors_cross_origin.checks import CorsCrossOriginCheckResult

_ISSUE_MAP: dict[str, tuple[str, str, str]] = {
    # kind → (slug, title, severity)
    "acao_star_sensitive": ("cors-allow-origin-star-sensitive", "Access-Control-Allow-Origin: * sur endpoint sensible", "high"),
    "credentials_origin_star": ("cors-credentials-origin-star", "Incohérence CORS (Credentials + Allow-Origin: *)", "critical"),
    "origin_reflection": ("cors-credentials-origin-reflection", "Réflexion d'origine non validée (CORS)", "critical"),
    "dangerous_methods": ("cors-allow-methods-dangerous", "Méthodes CORS dangereuses exposées (PUT/DELETE/PATCH)", "info"),
    "expose_headers_sensitive": ("cors-expose-headers-sensitive", "En-tête sensible exposé (Access-Control-Expose-Headers)", "medium"),
    "corp_missing_main": ("corp-missing-main", "Cross-Origin-Resource-Policy manquant (page principale)", "low"),
    "corp_missing_sensitive": ("corp-missing", "Cross-Origin-Resource-Policy manquant", "low"),
    "mixed_content": ("mixed-content-http-on-https", "Mixed content (HTTP sur page HTTPS)", "high"),
    "connection_failed": ("cors-connection-failed", "CORS et cross-origin inaccessibles", "high"),
}

_GENERIC = ("cors-generic", "Problème CORS ou cross-origin", "medium")


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


def normalize(result: CorsCrossOriginCheckResult) -> list[Finding]:
    """Convertit CorsCrossOriginCheckResult en list[Finding] via les issues typées."""
    findings: list[Finding] = []

    if not result.fetch_ok and not result.issues:
        findings.append(
            _finding(
                "cors-connection-failed",
                "cors_cross_origin",
                "CORS et cross-origin inaccessibles",
                "high",
                "CORS et cross-origin inaccessibles : réponse HTTPS indisponible.",
            )
        )
        return findings

    for issue in result.issues:
        slug, title, severity = _ISSUE_MAP.get(issue.kind, _GENERIC)
        findings.append(_finding(slug, "cors_cross_origin", title, severity, issue.message))
    return findings
