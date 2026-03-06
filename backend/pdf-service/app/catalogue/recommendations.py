"""Catalogue des recommandations, détails et références par slug de finding.

Charge les entrées depuis recommendations.json. Support i18n pour PDF fr/en.
"""

import json
from functools import lru_cache
from pathlib import Path


def _load_catalogue() -> dict:
    """Charge le catalogue depuis recommendations.json."""
    path = Path(__file__).resolve().parent / "recommendations.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _get_catalogue() -> dict:
    """Retourne le catalogue (mis en cache au premier accès)."""
    return _load_catalogue()


def _lang_key(lang: str, suffix: str) -> str:
    """Retourne la clé catalogue (ex. detail_en) selon la langue."""
    return f"{suffix}_en" if lang == "en" else f"{suffix}_fr"


def get_recommendation(slug: str, lang: str = "fr") -> str:
    """Retourne la recommandation pour un slug (fr/en)."""
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
    """Retourne les références (liens) pour un slug."""
    entry = _get_catalogue().get(slug)
    if entry is not None:
        refs = entry.get("references", [])
        return tuple(str(r) for r in refs)
    return ()


def get_title(slug: str, lang: str) -> str:
    """Retourne le titre i18n pour un slug (fr/en)."""
    entry = _get_catalogue().get(slug)
    if entry is None:
        return ""
    key = _lang_key(lang, "title")
    val = entry.get(key) or entry.get("title_fr") or entry.get("title_en")
    return str(val) if val else ""


def get_evidence(slug: str, lang: str) -> str:
    """Retourne l'evidence i18n pour un slug (fr/en)."""
    entry = _get_catalogue().get(slug)
    if entry is None:
        return ""
    key = _lang_key(lang, "evidence")
    val = entry.get(key) or entry.get("evidence_fr") or entry.get("evidence_en")
    return str(val) if val else ""


def get_detail(slug: str, lang: str) -> str:
    """Retourne le détail explicatif pour un slug (fr/en)."""
    entry = _get_catalogue().get(slug)
    if entry is None:
        return ""
    key = _lang_key(lang, "detail")
    detail = entry.get(key) or entry.get("detail", "")
    return str(detail) if detail else ""
