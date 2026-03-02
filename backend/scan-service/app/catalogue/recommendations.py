"""Catalogue des recommandations et références par slug de finding.

Charge les entrées depuis recommendations.json. Chaque entrée associe un slug
à (recommendation, references). Références : OWASP, MDN, Mozilla, etc.
"""

import json
from functools import lru_cache
from pathlib import Path


def _load_catalogue() -> dict[str, tuple[str, tuple[str, ...]]]:
    """Charge le catalogue depuis recommendations.json.

    Returns:
        dict[str, tuple[str, tuple[str, ...]]]: slug → (recommendation, references).
    """
    path = Path(__file__).resolve().parent / "recommendations.json"
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    result: dict[str, tuple[str, tuple[str, ...]]] = {}
    for slug, entry in raw.items():
        rec = str(entry.get("recommendation", ""))
        refs = tuple(str(r) for r in entry.get("references", []))
        result[slug] = (rec, refs)
    return result


@lru_cache(maxsize=1)
def _get_catalogue() -> dict[str, tuple[str, tuple[str, ...]]]:
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
        return entry[0]
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
        return entry[1]
    return ()
