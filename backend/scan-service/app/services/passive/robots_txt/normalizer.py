"""Normalisation des résultats robots.txt en list[Finding]."""

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.robots_txt.checks import RobotsTxtCheckResult


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


def normalize(result: RobotsTxtCheckResult) -> list[Finding]:
    """Convertit RobotsTxtCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.fetch_ok:
        from app.constants import MSG_ROBOTS_TXT_UNAVAILABLE

        findings.append(_finding("robots_txt-connection-failed", "robots_txt", "robots.txt inaccessible", "high", MSG_ROBOTS_TXT_UNAVAILABLE))
        return findings
    for route in result.sensitive_routes:
        ev = f"Disallow: {route.path} (motif : {route.pattern}). Vérifier la protection."
        findings.append(_finding("robots_txt-sensitive-route", "robots_txt", f"Route sensible : {route.path}", route.severity.lower(), ev))
    if result.crawl_delay is not None:
        ev = f"Crawl-delay: {result.crawl_delay}s (directive non standard, certains moteurs l'ignorent)."
        findings.append(_finding("robots_txt-crawl-delay", "robots_txt", "Crawl-delay détecté", "info", ev))
    return findings
