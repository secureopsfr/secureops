"""Système de scoring : note /100 avec pondération par catégorie (roadmap §5).

Charge la config depuis settings.yml (scoring.category_weights, scoring.severity_penalties).
Pour le Scanner 2 (intrusif), utiliser compute_intrusive_score() avec les poids intrusif_scan.
"""

from collections import defaultdict

from app.config_loader import get_intrusive_scan_settings, get_scoring_settings
from app.models.finding import Finding


def compute_score(findings: tuple[Finding, ...]) -> int:
    """Calcule le score global /100 à partir des findings.

    Le score est une moyenne pondérée des scores par catégorie :
    somme(score_cat * weight_cat) / somme(weight_cat), arrondie à l'entier le plus proche,
    puis bornée entre 0 et 100.

    Complexité : O(M + N) — un seul parcours de findings pour grouper par catégorie,
    puis un parcours des N catégories pour le scoring. Évite le O(N×M) de la version
    précédente (filtre findings par catégorie à chaque itération).

    Args:
        findings: Tuple des findings normalisés.

    Returns:
        int: Score entre 0 et 100.
    """
    if not findings:
        return 100

    settings = get_scoring_settings()

    # Groupement en un seul passage O(M)
    by_category: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_category[f.category].append(f)

    total_weight = float(sum(settings.category_weights.values()) or 1)
    weighted_sum = 0.0
    for category, weight in settings.category_weights.items():
        cat_findings = by_category.get(category)
        if not cat_findings:
            cat_score = 100.0
        else:
            total_penalty = sum(settings.severity_penalties.get(f.severity.lower(), 25) for f in cat_findings)
            cat_score = max(0.0, 100.0 - float(total_penalty))
        weighted_sum += cat_score * float(weight)

    raw_score = weighted_sum / total_weight
    return max(0, min(100, int(round(raw_score))))


def compute_intrusive_score(findings: list[Finding] | tuple[Finding, ...]) -> int:
    """Calcule le score intrusif /100 selon les poids de intrusive_scan dans settings.yml.

    Même algorithme que compute_score : moyenne pondérée par catégorie.
    Les catégories inconnues (non dans les poids) utilisent une pénalité directe.
    """
    if not findings:
        return 100

    settings = get_intrusive_scan_settings()
    by_category: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_category[f.category].append(f)

    total_weight = float(sum(settings.category_weights.values()) or 1)
    weighted_sum = 0.0
    for category, weight in settings.category_weights.items():
        cat_findings = by_category.get(category)
        if not cat_findings:
            cat_score = 100.0
        else:
            total_penalty = sum(settings.severity_penalties.get(f.severity.lower(), 25) for f in cat_findings)
            cat_score = max(0.0, 100.0 - float(total_penalty))
        weighted_sum += cat_score * float(weight)

    raw_score = weighted_sum / total_weight
    return max(0, min(100, int(round(raw_score))))
