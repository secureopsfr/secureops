"""Normalisation des résultats Cache en list[Finding].

Utilise les issues typées (CacheIssue.kind) — aucune correspondance de chaînes.
"""

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.both.cache.checks import CacheCheckResult

_ISSUE_MAP: dict[str, tuple[str, str, str]] = {
    # kind → (slug, title, severity)
    "sensitive_public": ("cache-sensitive-page-public", "Page sensible cacheable publiquement", "high"),
    "no_cache_control": ("cache-no-cache-control", "Absence de Cache-Control sur page sensible", "medium"),
    "pragma_incoherent": ("cache-pragma-incoherent", "Incohérence Pragma / Cache-Control", "low"),
    "immutable_bad_cache": ("cache-immutable-no-long-cache", "Asset immuable sans cache long", "info"),
    "connection_failed": ("cache-connection-failed", "En-têtes de cache inaccessibles", "high"),
}

_GENERIC = ("cache-generic-issue", "Problème de configuration de cache", "medium")


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


def normalize(result: CacheCheckResult) -> list[Finding]:
    """Convertit CacheCheckResult en list[Finding] via les issues typées."""
    findings: list[Finding] = []

    if not result.fetch_ok:
        from app.constants import MSG_HEADERS_UNAVAILABLE

        findings.append(_finding("cache-connection-failed", "cache", "En-têtes de cache inaccessibles", "high", MSG_HEADERS_UNAVAILABLE))
        return findings

    for issue in result.issues:
        slug, title, severity = _ISSUE_MAP.get(issue.kind, _GENERIC)
        findings.append(_finding(slug, "cache", title, severity, issue.message))
    return findings
