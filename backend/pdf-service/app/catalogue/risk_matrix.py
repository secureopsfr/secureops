"""Catalogue gravité/vraisemblance par slug pour les matrices de risque PDF.

Charge les entrées depuis risk_matrix.json. Chaque entrée associe un slug
à (gravité, vraisemblance) pour afficher la croix dans la matrice prédéfinie.
"""

import json
from functools import lru_cache
from pathlib import Path

_GRAVITE_DEFAULT = "Significative"
_VRAISEMBLANCE_DEFAULT = "Forte"

_GRAVITES = ("Mineure", "Significative", "Importante", "Majeure")
_VRAISEMBLANCES = ("Très faible", "Faible", "Forte", "Très forte")


def _load_risk_matrix() -> dict:
    """Charge le catalogue depuis risk_matrix.json.

    Returns:
        dict: slug → {gravite, vraisemblance}.
    """
    path = Path(__file__).resolve().parent / "risk_matrix.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _get_risk_matrix() -> dict:
    """Retourne le catalogue (mis en cache au premier accès)."""
    return _load_risk_matrix()


def get_gravite(slug: str) -> str:
    """Retourne la gravité pour un slug, ou une valeur par défaut si absent.

    Args:
        slug: Identifiant du finding (ex. tls-https-disabled).

    Returns:
        str: Mineure | Significative | Importante | Majeure.
    """
    entry = _get_risk_matrix().get(slug)
    if entry:
        g = entry.get("gravite")
        if g in _GRAVITES:
            return g
    return _GRAVITE_DEFAULT


def get_vraisemblance(slug: str) -> str:
    """Retourne la vraisemblance pour un slug, ou une valeur par défaut si absent.

    Args:
        slug: Identifiant du finding.

    Returns:
        str: Très faible | Faible | Forte | Très forte.
    """
    entry = _get_risk_matrix().get(slug)
    if entry:
        v = entry.get("vraisemblance")
        if v in _VRAISEMBLANCES:
            return v
    return _VRAISEMBLANCE_DEFAULT


def get_risk_position(slug: str) -> tuple[str, str]:
    """Retourne (gravité, vraisemblance) pour un slug.

    Args:
        slug: Identifiant du finding.

    Returns:
        tuple[str, str]: (gravité, vraisemblance).
    """
    return (get_gravite(slug), get_vraisemblance(slug))
