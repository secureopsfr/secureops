"""Normalisation des résultats Sitemap en list[Finding]."""

from app.catalogue.owasp import get_owasp_categories
from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding
from app.services.passive.frontend.sitemap.checks import SitemapCheckResult


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


def normalize(result: SitemapCheckResult) -> list[Finding]:
    """Convertit SitemapCheckResult en list[Finding]."""
    findings: list[Finding] = []
    if not result.sitemap_found:
        if result.fetch_ok:
            findings.append(
                _finding(
                    "sitemap-not-found",
                    "sitemap",
                    "Sitemap non trouvé",
                    "info",
                    "Aucun sitemap trouvé (ni dans robots.txt, ni à /sitemap.xml). Recommandation : créer et déclarer un sitemap.",
                )
            )
        return findings
    if result.sitemap_undeclared:
        findings.append(
            _finding(
                "sitemap-undeclared",
                "sitemap",
                "Sitemap présent mais non déclaré dans robots.txt",
                "info",
                "Sitemap trouvé à /sitemap.xml mais absent de robots.txt. Recommandation : ajouter Sitemap: dans robots.txt.",
            )
        )
    for su in result.sensitive_urls:
        ev = f"URL sensible dans sitemap : {su.url} (motif : {su.pattern})."
        findings.append(
            _finding(
                "sitemap-sensitive-url",
                "sitemap",
                f"URL sensible exposée dans sitemap : {su.path}",
                su.severity.lower(),
                ev,
            )
        )
    return findings
