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
    return max(0.0, 100.0 - float(total_penalty))


def compute_score(findings: tuple[Finding, ...]) -> int:
    """Calcule le score global /100 à partir des findings.

    Le score est une moyenne pondérée des scores par catégorie :
    somme(score_cat * weight_cat) / somme(weight_cat), arrondie à l'entier le plus proche,
    puis bornée entre 0 et 100.

    Ce calcul garantit qu'ajouter une nouvelle catégorie avec un score inférieur ou égal
    au score global ne peut pas augmenter artificiellement la moyenne.

    Args:
        findings: Liste des findings normalisés.

    Returns:
        int: Score entre 0 et 100.
    """
    if not findings:
        return 100

    settings = get_scoring_settings()
    findings_list = list(findings)

    total_weight = float(sum(settings.category_weights.values()) or 1)
    weighted_sum = 0.0
    for category, weight in settings.category_weights.items():
        cat_score = _category_score(findings_list, category)
        weighted_sum += cat_score * float(weight)

    raw_score = weighted_sum / total_weight
    score = int(round(raw_score))
    return max(0, min(100, score))
