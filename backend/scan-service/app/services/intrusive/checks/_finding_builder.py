"""Helper partagé pour construire des Finding dans les checks intrusifs.

Évite la duplication du boilerplate Finding(...) dans chaque check.
"""

from __future__ import annotations

from app.catalogue.owasp import get_owasp_categories
from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding


def make_finding(
    *,
    slug: str,
    category: str,
    title: str,
    severity: str,
    evidence: str,
    detail: str = "",
) -> Finding:
    """Construit un Finding en récupérant recommandation, références et OWASP du catalogue."""
    return Finding(
        id=slug,
        category=category,
        title=title,
        severity=severity,
        evidence=evidence,
        recommendation=get_recommendation(slug) or detail or "",
        references=tuple(get_references(slug)),
        owasp_categories=tuple(get_owasp_categories(slug)),
    )
