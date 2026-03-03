"""Catalogue des résumés par catégorie de vérification.

Charge category_summaries.json et fournit les métadonnées (label, description, checks)
pour chaque catégorie. Utilisé pour construire la section « Résumé des vérifications »
dans la réponse du scan et le frontend.
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_CATEGORY_ORDER = (
    "tls",
    "headers",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "tech_fingerprinting",
)


@dataclass
class CategorySummaryEntry:
    """Entrée du résumé pour une catégorie.

    Attributes:
        category (str): Identifiant (tls, headers, etc.).
        label_fr (str): Libellé français.
        label_en (str): Libellé anglais.
        description_fr (str): Description détaillée des vérifications (fr).
        description_en (str): Description détaillée des vérifications (en).
        checks_fr (list[str]): Liste des checks effectués (fr).
        checks_en (list[str]): Liste des checks effectués (en).
        anomaly_count (int): Nombre d'anomalies détectées.
    """

    category: str
    label_fr: str
    label_en: str
    description_fr: str
    description_en: str
    checks_fr: list[str]
    checks_en: list[str]
    anomaly_count: int

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
        }


@lru_cache(maxsize=1)
def _load_category_summaries() -> dict[str, dict]:
    """Charge le catalogue depuis category_summaries.json."""
    path = Path(__file__).resolve().parent / "category_summaries.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_category_summaries(
    findings: Iterable[object],
    *,
    tls_posture: str | None = None,
    tls_version: str | None = None,
) -> list[dict]:
    """Construit la liste des résumés par catégorie pour la réponse du scan.

    Args:
        findings: Liste des Finding (doit avoir un attribut category).
        tls_posture: Posture TLS ("ok", "warning", "critical") pour la catégorie tls.
        tls_version: Version TLS négociée (ex. "TLS 1.2", "TLS 1.3") pour la catégorie tls.

    Returns:
        list[dict]: Liste de CategorySummaryEntry sérialisées, ordre fixe.
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
        d = CategorySummaryEntry(
            category=cat,
            label_fr=str(entry.get("label_fr", cat)),
            label_en=str(entry.get("label_en", cat)),
            description_fr=str(entry.get("description_fr", "")),
            description_en=str(entry.get("description_en", "")),
            checks_fr=list(entry.get("checks_fr", [])),
            checks_en=list(entry.get("checks_en", [])),
            anomaly_count=anomaly_count,
        ).to_dict()
        if cat == "tls":
            if tls_posture is not None:
                d["tls_posture"] = tls_posture
            if tls_version is not None:
                d["tls_version"] = tls_version
        result.append(d)

    return result
