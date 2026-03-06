"""Catalogue des résumés par catégorie de vérification.

Charge category_summaries.json et fournit les métadonnées (label, description, checks)
pour chaque catégorie. Utilisé pour le rapport PDF.
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_CATEGORY_ORDER = (
    "tls",
    "headers",
    "cache",
    "integrity",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "sitemap",
    "tech_fingerprinting",
    "information_disclosure",
    "cors_cross_origin",
)


@dataclass
class CategorySummaryEntry:
    """Entrée du résumé pour une catégorie.

    Attributes:
        category: Identifiant (tls, headers, etc.).
        label_fr: Libellé français.
        label_en: Libellé anglais.
        description_fr: Description détaillée des vérifications (fr).
        description_en: Description détaillée des vérifications (en).
        checks_fr: Liste des checks effectués (fr).
        checks_en: Liste des checks effectués (en).
        anomaly_count: Nombre d'anomalies détectées.
        checks_count: Nombre de tests effectués dans cette catégorie.
    """

    category: str
    label_fr: str
    label_en: str
    description_fr: str
    description_en: str
    checks_fr: list[str]
    checks_en: list[str]
    anomaly_count: int
    checks_count: int

    def to_dict(self) -> dict:
        """Sérialise pour le payload JSON."""
        return {
            "category": self.category,
            "label_fr": self.label_fr,
            "label_en": self.label_en,
            "description_fr": self.description_fr,
            "description_en": self.description_en,
            "checks_fr": self.checks_fr,
            "checks_en": self.checks_en,
            "anomaly_count": self.anomaly_count,
            "checks_count": self.checks_count,
        }


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


def build_category_summaries(
    findings: Iterable[object],
    *,
    tls_posture: str | None = None,
    tls_version: str | None = None,
) -> list[dict]:
    """Construit la liste des résumés par catégorie (pour compatibilité catalogue).

    Args:
        findings: Liste des Finding (doit avoir un attribut category).
        tls_posture: Posture TLS pour la catégorie tls.
        tls_version: Version TLS pour la catégorie tls.

    Returns:
        list[dict]: Liste de CategorySummaryEntry sérialisées.
    """
    by_category: dict[str, int] = {}
    for f in findings:
        cat = getattr(f, "category", None)
        if cat:
            by_category[cat] = by_category.get(cat, 0) + 1

    catalogue = _load_category_summaries()
    result: list[dict] = []

    for cat in _CATEGORY_ORDER:
        entry = catalogue.get(cat)
        if entry is None:
            continue
        anomaly_count = by_category.get(cat, 0)
        checks_fr = list(entry.get("checks_fr", []))
        checks_en = list(entry.get("checks_en", []))
        checks_count = max(len(checks_fr), len(checks_en)) if checks_fr or checks_en else 0
        d = CategorySummaryEntry(
            category=cat,
            label_fr=str(entry.get("label_fr", cat)),
            label_en=str(entry.get("label_en", cat)),
            description_fr=str(entry.get("description_fr", "")),
            description_en=str(entry.get("description_en", "")),
            checks_fr=checks_fr,
            checks_en=checks_en,
            anomaly_count=anomaly_count,
            checks_count=checks_count,
        ).to_dict()
        if cat == "tls":
            if tls_posture is not None:
                d["tls_posture"] = tls_posture
            if tls_version is not None:
                d["tls_version"] = tls_version
        result.append(d)

    return result
