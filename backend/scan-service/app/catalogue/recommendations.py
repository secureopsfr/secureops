"""Catalogue des recommandations, détails et références par slug de finding.

Charge les entrées depuis recommendations.json. Chaque entrée associe un slug
à (recommendation, recommendation_en, title_fr, title_en, evidence_fr, evidence_en,
detail_fr, detail_en, references). Support i18n fr/en (scan et pdf-service).
"""

import json
from functools import lru_cache
from pathlib import Path


def _load_catalogue() -> dict[str, dict]:
    """Charge le catalogue depuis recommendations.json.

    Returns:
        dict[str, dict]: slug → {recommendation, references, detail_fr, detail_en, ...}.
    """
    path = Path(__file__).resolve().parent / "recommendations.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _get_catalogue() -> dict[str, dict]:
    """Retourne le catalogue (mis en cache au premier accès)."""
    return _load_catalogue()


def _lang_key(lang: str, suffix: str) -> str:
    """Retourne la clé catalogue (ex. detail_en) selon la langue."""
    return f"{suffix}_en" if lang == "en" else f"{suffix}_fr"


def get_recommendation(slug: str, lang: str = "fr") -> str:
    """Retourne la recommandation pour un slug (fr/en), ou une chaîne générique si absent.

    Args:
        slug: Identifiant du finding (ex. tls-https-disabled).
        lang: Code langue (fr/en). Défaut fr.

    Returns:
        str: Texte de recommandation.
    """
    entry = _get_catalogue().get(slug)
    if entry is not None:
        key = _lang_key(lang, "recommendation")
        rec = entry.get(key) or entry.get("recommendation")
        if rec:
            return str(rec)
    return (
        "Consulter la documentation de sécurité pour ce type de problème."
        if lang == "fr"
        else "Consult security documentation for this type of issue."
    )


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


def get_title(slug: str, lang: str) -> str:
    """Retourne le titre i18n pour un slug (fr/en), ou chaîne vide si absent.

    Args:
        slug: Identifiant du finding.
        lang: Code langue (fr/en).

    Returns:
        str: Titre traduit ou chaîne vide si non défini dans le catalogue.
    """
    entry = _get_catalogue().get(slug)
    if entry is None:
        return ""
    key = _lang_key(lang, "title")
    val = entry.get(key) or entry.get("title_fr") or entry.get("title_en")
    return str(val) if val else ""


def get_evidence(slug: str, lang: str) -> str:
    """Retourne l'evidence i18n pour un slug (fr/en), ou chaîne vide si absent.

    Args:
        slug: Identifiant du finding.
        lang: Code langue (fr/en).

    Returns:
        str: Evidence traduite ou chaîne vide si non définie dans le catalogue.
    """
    entry = _get_catalogue().get(slug)
    if entry is None:
        return ""
    key = _lang_key(lang, "evidence")
    val = entry.get(key) or entry.get("evidence_fr") or entry.get("evidence_en")
    return str(val) if val else ""


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
    key = _lang_key(lang, "detail")
    detail = entry.get(key) or entry.get("detail", "")
    return str(detail) if detail else ""
