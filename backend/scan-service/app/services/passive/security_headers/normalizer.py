"""Normalisation des résultats Security Headers en list[Finding]."""

from app.catalogue.recommendations import get_recommendation, get_references
from app.config_loader import get_security_headers_settings
from app.models.finding import Finding
from app.services.passive.security_headers.checks import SecurityHeadersCheckResult


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


def normalize(result: SecurityHeadersCheckResult) -> list[Finding]:
    """Convertit SecurityHeadersCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        from app.constants import MSG_HEADERS_UNAVAILABLE

        findings.append(_finding("headers-connection-failed", "headers", "En-têtes inaccessibles", "high", MSG_HEADERS_UNAVAILABLE))
        return findings

    headers_config = get_security_headers_settings()
    header_to_slug = {cfg.name: cfg.slug for cfg in headers_config}
    header_to_severity = {cfg.name: cfg.severity for cfg in headers_config}

    for header_name in result.headers_missing:
        slug = header_to_slug.get(header_name, "headers-connection-failed")
        severity = header_to_severity.get(header_name, "medium")
        findings.append(_finding(slug, "headers", f"{header_name} absent", severity, f"{header_name} absent."))

    for msg in result.findings:
        msg_l = msg.lower()
        if "valeur incorrecte" in msg_l or "incorrecte" in msg_l:
            findings.append(_finding("headers-xcto-wrong-value", "headers", "X-Content-Type-Options valeur incorrecte", "medium", msg))
        elif "report-uri" in msg_l and "report-to" in msg_l and "sans" in msg_l:
            findings.append(_finding("headers-csp-no-report-uri", "headers", "CSP sans report-uri ni report-to", "low", msg))
        elif "unsafe-inline" in msg_l or "unsafe-eval" in msg_l:
            findings.append(_finding("headers-csp-unsafe-directives", "headers", "CSP avec directives unsafe", "low", msg))
    return findings
