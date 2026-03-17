"""Normalisation des résultats Méthodes HTTP en list[Finding]."""

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.both.methodes_http_et_redirections.checks import MethodesHttpCheckResult

_ISSUE_MAP: dict[str, tuple[str, str, str | None]] = {
    # dangerous_methods: severity selon scan_type (None = à calculer)
    "dangerous_methods": ("methodes-http-dangerous-methods", "Méthodes PUT/DELETE/PATCH exposées", None),
    "trace_enabled": ("methodes-http-trace-enabled", "TRACE activé (risque XST)", "high"),
    "head_unsupported": ("methodes-http-head-unsupported", "HEAD non supporté", "info"),
    "redirect_chain_excessive": ("methodes-http-redirect-chain-excessive", "Chaîne de redirection excessive", "low"),
    "redirect_301_302_form": ("methodes-http-redirect-301-302-form", "Redirection 301/302 sur formulaire sensible", "info"),
}

_GENERIC = ("methodes-http-generic", "Problème Méthodes HTTP ou redirections", "info")


def _finding(slug: str, category: str, title: str, severity: str, evidence: str) -> Finding:
    return Finding(
        id=slug,
        category=category,
        title=title,
        severity=severity.lower() if severity else "info",
        evidence=evidence,
        recommendation=get_recommendation(slug),
        references=get_references(slug),
    )


def normalize(result: MethodesHttpCheckResult) -> list[Finding]:
    """Convertit MethodesHttpCheckResult en list[Finding].

    Ajuste la sévérité selon scan_type : dangerous_methods → Low si frontend, Info si backend.
    """
    findings: list[Finding] = []
    is_backend = (result.scan_type or "").lower() == "backend"
    for issue in result.issues:
        slug, title, severity = _ISSUE_MAP.get(issue.kind, _GENERIC)
        if severity is None and issue.kind == "dangerous_methods":
            severity = "info" if is_backend else "low"
        findings.append(_finding(slug, "methodes_http_et_redirections", title, severity or "info", issue.message))
    return findings
