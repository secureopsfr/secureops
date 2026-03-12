"""Modèles de données pour le scan multi-URL."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PageScanResult:
    """Résultat du scan de sécurité pour une URL individuelle.

    Attributes:
        url: URL scannée.
        score: Score de sécurité (0-100).
        findings: Liste des findings normalisés (scope domain + page).
        category_summaries: Résumés par catégorie.
        total_tests_count: Nombre total de tests effectués.
        error: Message d'erreur si la page était inaccessible.
    """

    url: str
    score: int
    findings: list[dict[str, Any]] = field(default_factory=list)
    category_summaries: list[dict[str, Any]] = field(default_factory=list)
    total_tests_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le résultat de page au format JSON-serializable."""
        d: dict[str, Any] = {
            "url": self.url,
            "score": self.score,
            "findings": self.findings,
            "category_summaries": self.category_summaries,
            "total_tests_count": self.total_tests_count,
        }
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class MultiScanResult:
    """Résultat agrégé d'un scan multi-URL sur un même domaine.

    Attributes:
        base_url: URL de base du domaine (ex. https://example.com/).
        urls: Liste des URLs scannées.
        score_global: Score global (moyenne pondérée des scores de pages).
        page_results: Résultats individuels par URL.
        timestamp: Horodatage ISO de fin de scan.
        duration: Durée totale en secondes.
        scan_type: Type de scan (toujours "frontend" en V1).
        status: Statut global ("success" même si certaines pages ont des erreurs).
    """

    base_url: str
    urls: list[str]
    score_global: int
    page_results: list[PageScanResult]
    timestamp: str
    duration: float
    scan_type: str = "frontend"
    status: str = "success"
    result_mode: str = "multi"

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le résultat agrégé multi-URL au format dict."""
        return {
            "result_mode": self.result_mode,
            "base_url": self.base_url,
            "urls": self.urls,
            "score_global": self.score_global,
            "page_results": [p.to_dict() for p in self.page_results],
            "timestamp": self.timestamp,
            "duration": self.duration,
            "scan_type": self.scan_type,
            "status": self.status,
        }
