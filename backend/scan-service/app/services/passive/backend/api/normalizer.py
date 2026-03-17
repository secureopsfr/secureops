"""Normalisation des résultats API en list[Finding]."""

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.backend.api.checks import ApiCheckResult

_ISSUE_MAP: dict[str, tuple[str, str, str]] = {
    "graphql_introspection": ("api-graphql-introspection", "Introspection GraphQL activée", "high"),
    "swagger_exposed": ("api-swagger-exposed", "Swagger/OpenAPI exposé sans auth", "high"),
    "rest_unpaginated": ("api-rest-unpaginated", "Liste REST non paginée", "info"),
    "content_type_wrong": ("formats-content-type-wrong", "Content-Type incorrect", "medium"),
    "xcto_missing": ("formats-xcto-missing", "X-Content-Type-Options: nosniff absent", "low"),
    "no_compression": ("formats-no-compression", "Réponse sans compression", "info"),
}

_GENERIC = ("api-generic", "Problème API ou format", "info")


def _finding(slug: str, title: str, severity: str, evidence: str) -> Finding:
    return Finding(
        id=slug,
        category="apis_et_formats",
        title=title,
        severity=severity.lower() if severity else "info",
        evidence=evidence,
        recommendation=get_recommendation(slug),
        references=get_references(slug),
    )


def normalize(result: ApiCheckResult) -> list[Finding]:
    """Convertit ApiCheckResult en list[Finding]."""
    findings: list[Finding] = []
    for issue in result.issues:
        slug, title, severity = _ISSUE_MAP.get(issue.kind, _GENERIC)
        findings.append(_finding(slug, title, severity or "info", issue.message))
    return findings
