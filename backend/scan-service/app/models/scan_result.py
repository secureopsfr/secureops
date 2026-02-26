"""Schéma ScanResult : résultat global du scan (url, timestamp, durée, score, findings)."""

from dataclasses import dataclass

from app.models.finding import Finding


@dataclass
class ScanResult:
    """Résultat normalisé du scan.

    Attributes:
        url (str): URL scannée (normalisée).
        timestamp (str): Horodatage ISO (début ou fin du scan).
        duration (float): Durée en secondes.
        score (int): Note /100 (0–100).
        findings (tuple[Finding, ...]): Liste des findings normalisés.
    """

    url: str
    timestamp: str
    duration: float
    score: int
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict:
        """Sérialise pour le payload SSE."""
        return {
            "url": self.url,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "score": self.score,
            "findings": [f.to_dict() for f in self.findings],
        }
