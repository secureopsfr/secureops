"""Normalisation des résultats Formats en list[Finding]."""

from app.catalogue.owasp import get_owasp_categories
from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.both.formats.checks import FormatsCheckResult

_ISSUE_MAP: dict[str, tuple[str, str, str]] = {
    "content_type_wrong": ("formats-content-type-wrong", "Content-Type incorrect", "medium"),
    "xcto_missing": ("formats-xcto-missing", "X-Content-Type-Options: nosniff absent", "low"),
    "no_compression": ("formats-no-compression", "Réponse sans compression", "info"),
}

_GENERIC = ("formats-generic", "Problème format de réponse", "info")


def _finding(slug: str, title: str, severity: str, evidence: str) -> Finding:
    return Finding(
        id=slug,
        category="apis_et_formats",
        title=title,
        severity=severity.lower() if severity else "info",
        evidence=evidence,
        recommendation=get_recommendation(slug),
        references=get_references(slug),
        owasp_categories=get_owasp_categories(slug),
    )


def normalize(result: FormatsCheckResult) -> list[Finding]:
    """Convertit FormatsCheckResult en list[Finding]."""
    findings: list[Finding] = []
    for issue in result.issues:
        slug, title, severity = _ISSUE_MAP.get(issue.kind, _GENERIC)
        findings.append(_finding(slug, title, severity or "info", issue.message))
    return findings
