"""Catalogue des résumés par catégorie de vérification.

Charge category_summaries.json et fournit les métadonnées (description, checks)
pour chaque catégorie. Utilisé pour le rapport PDF.

Les libellés de catégories (labels_fr / labels_en) sont définis dans config/settings.yml
et chargés via get_category_labels() — ne pas les dupliquer ici.
"""

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_category_summaries() -> dict:
    """Charge le catalogue depuis category_summaries.json."""
    path = Path(__file__).resolve().parent / "category_summaries.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_category_description(cat: str, lang: str) -> str:
    """Retourne la description d'une catégorie (depuis le catalogue).

    Args:
        cat: Identifiant de catégorie (tls, headers, etc.).
        lang: Code langue (fr/en).

    Returns:
        str: Description ou chaîne vide si absent.
    """
    catalogue = _load_category_summaries()
    entry = catalogue.get(cat)
    if not entry:
        return ""
    key = "description_en" if lang == "en" else "description_fr"
    return str(entry.get(key, ""))


def get_checks_count(cat: str) -> int:
    """Retourne le nombre de tests pour une catégorie (depuis le catalogue).

    Args:
        cat: Identifiant de catégorie (tls, headers, etc.).

    Returns:
        int: Nombre de checks définis dans le catalogue, ou 0 si absent.
    """
    catalogue = _load_category_summaries()
    entry = catalogue.get(cat)
    if not entry:
        return 0
    checks_fr = entry.get("checks_fr", [])
    checks_en = entry.get("checks_en", [])
    return max(len(checks_fr), len(checks_en)) if checks_fr or checks_en else 0
