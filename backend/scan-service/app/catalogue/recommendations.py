"""Catalogue des recommandations, détails et références par slug de finding.

Charge les entrées depuis recommendations.json. Chaque entrée associe un slug
à (recommendation, references, detail_fr, detail_en). Références : OWASP, MDN, etc.
"""

import json
from functools import lru_cache
from pathlib import Path


def _load_catalogue() -> dict[str, dict]:
    """Charge le catalogue depuis recommendations.json.

    Returns:
        dict[str, dict]: slug → {recommendation, references, detail_fr, detail_en}.
    """
    path = Path(__file__).resolve().parent / "recommendations.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _get_catalogue() -> dict[str, dict]:
    """Retourne le catalogue (mis en cache au premier accès)."""
    return _load_catalogue()


def get_recommendation(slug: str) -> str:
    """Retourne la recommandation pour un slug, ou une chaîne générique si absent.

    Args:
        slug: Identifiant du finding (ex. tls-https-disabled).

    Returns:
        str: Texte de recommandation.
    """
    entry = _get_catalogue().get(slug)
    if entry is not None:
        rec = entry.get("recommendation")
        if rec:
            return str(rec)
    return "Consulter la documentation de sécurité pour ce type de problème."


def get_references(slug: str) -> tuple[str, ...]:
    """Retourne les références (liens) pour un slug.

    Args:
        slug: Identifiant du finding.

    Returns:
        tuple[str, ...]: Liste des URLs de référence.
    """
    entry = _get_catalogue().get(slug)
    if entry is not None:
        refs = entry.get("references", [])
        return tuple(str(r) for r in refs)
    return ()


def get_detail(slug: str, lang: str) -> str:
    """Retourne le détail explicatif pour un slug (fr/en), ou chaîne vide si absent.

    Args:
        slug: Identifiant du finding.
        lang: Code langue (fr/en).

    Returns:
        str: Explication détaillée du problème ou chaîne vide.
    """
    entry = _get_catalogue().get(slug)
    if entry is None:
        return ""
    key = "detail_fr" if lang == "fr" else "detail_en"
    detail = entry.get(key) or entry.get("detail", "")
    return str(detail) if detail else ""
