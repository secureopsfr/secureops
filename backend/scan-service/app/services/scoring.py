"""Système de scoring : note /100 avec pondération par catégorie (roadmap §5).

Charge la config depuis settings.yml (scoring.category_weights, scoring.severity_penalties).
"""

from app.config_loader import get_scoring_settings
from app.models.finding import Finding


def _category_score(findings: list[Finding], category: str) -> float:
    """Calcule le score (0–100) pour une catégorie à partir de ses findings.

    Chaque finding retire des points selon sa sévérité. Le score est plafonné à 0.
    """
    settings = get_scoring_settings()
    cat_findings = [f for f in findings if f.category == category]
    if not cat_findings:
        return 100.0
    total_penalty = sum(settings.severity_penalties.get(f.severity.lower(), 25) for f in cat_findings)
    return max(0, 100 - total_penalty)


def compute_score(findings: tuple[Finding, ...]) -> int:
    """Calcule le score global /100 à partir des findings.

    Pondération depuis settings.yml. Chaque catégorie contribue (score_cat / 100) * weight au total.

    Args:
        findings: Liste des findings normalisés.

    Returns:
        int: Score entre 0 et 100.
    """
    if not findings:
        return 100
    settings = get_scoring_settings()
    findings_list = list(findings)
    weighted_sum = 0.0
    for category, weight in settings.category_weights.items():
        cat_score = _category_score(findings_list, category)
        weighted_sum += (cat_score / 100.0) * weight
    return min(100, max(0, int(round(weighted_sum))))
