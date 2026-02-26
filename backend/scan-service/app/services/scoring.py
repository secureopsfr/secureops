"""Système de scoring : note /100 avec pondération par catégorie (roadmap §5).

Pondération : TLS 25, Headers 25, Cookies 20, Exposure 20, Fingerprinting/robots 10.
Mapping sévérité : critical, high, medium, low, info.
"""

from app.models.finding import Finding

# Pondération par catégorie (total = 100)
_CATEGORY_WEIGHTS: dict[str, int] = {
    "tls": 25,
    "headers": 25,
    "cookies": 20,
    "exposed_files": 10,
    "directory_listing": 10,
    "robots_txt": 5,
    "tech_fingerprinting": 5,
}

# Pénalité par sévérité (points retirés du score de la catégorie)
_SEVERITY_PENALTY: dict[str, int] = {
    "critical": 100,
    "high": 50,
    "medium": 25,
    "low": 10,
    "info": 0,
}


def _category_score(findings: list[Finding], category: str) -> float:
    """Calcule le score (0–100) pour une catégorie à partir de ses findings.

    Chaque finding retire des points selon sa sévérité. Le score est plafonné à 0.
    """
    cat_findings = [f for f in findings if f.category == category]
    if not cat_findings:
        return 100.0
    total_penalty = sum(_SEVERITY_PENALTY.get(f.severity.lower(), 25) for f in cat_findings)
    return max(0, 100 - total_penalty)


def compute_score(findings: tuple[Finding, ...]) -> int:
    """Calcule le score global /100 à partir des findings.

    Pondération : TLS 25, Headers 25, Cookies 20, Exposure (exposed+dir) 20, Fingerprinting+robots 10.
    Chaque catégorie contribue (score_cat / 100) * weight au total.

    Args:
        findings: Liste des findings normalisés.

    Returns:
        int: Score entre 0 et 100.
    """
    if not findings:
        return 100
    findings_list = list(findings)
    weighted_sum = 0.0
    for category, weight in _CATEGORY_WEIGHTS.items():
        cat_score = _category_score(findings_list, category)
        weighted_sum += (cat_score / 100.0) * weight
    return min(100, max(0, int(round(weighted_sum))))
