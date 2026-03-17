"""Normalisation des résultats Information Disclosure en list[Finding].

Utilise les issues typées (InfoDiscIssue.kind) — aucune correspondance de chaînes.
"""

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.both.information_disclosure.checks import InformationDisclosureCheckResult

_ISSUE_MAP: dict[str, tuple[str, str, str]] = {
    # kind → (slug, title, severity)
    "stack_trace": ("info-disclosure-stack-trace", "Stack trace dans la réponse", "high"),
    "debug_mode": ("info-disclosure-debug-mode", "Mode debug exposé", "medium"),
    "secret": ("info-disclosure-secret", "Secret potentiel dans la réponse", "critical"),
    "debug_headers": ("info-disclosure-debug-headers", "En-têtes de débogage exposés", "medium"),
    "server_version": ("info-disclosure-server-version", "Version serveur exposée", "low"),
    "runtime_version": ("info-disclosure-powered-by-version", "Version runtime exposée", "low"),
    "aspnet_version": ("info-disclosure-aspnet-version", "Version ASP.NET exposée", "low"),
    "custom_header": ("info-disclosure-custom-header", "En-tête custom révélant la stack", "low"),
    "meta_generator": ("info-disclosure-meta-generator", "Meta generator exposant la stack", "info"),
    "connection_failed": ("info-disclosure-connection-failed", "Analyse fuites impossible", "info"),
}

_GENERIC = ("info-disclosure-generic", "Fuite d'information", "medium")


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


def normalize(result: InformationDisclosureCheckResult) -> list[Finding]:
    """Convertit InformationDisclosureCheckResult en list[Finding] via les issues typées."""
    findings: list[Finding] = []

    if not result.fetch_ok:
        findings.append(
            _finding(
                "info-disclosure-connection-failed",
                "information_disclosure",
                "Analyse fuites d'information impossible",
                "info",
                "Réponse HTTPS indisponible pour analyser les fuites d'information.",
            )
        )
        return findings

    for issue in result.issues:
        slug, title, severity = _ISSUE_MAP.get(issue.kind, _GENERIC)
        findings.append(_finding(slug, "information_disclosure", title, severity, issue.message))
    return findings
