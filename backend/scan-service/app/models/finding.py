"""Schéma Finding : représentation normalisée d'un problème de sécurité détecté."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """Finding normalisé : id, catégorie, titre, sévérité, preuve, recommandation, références.

    Attributes:
        id (str): Slug déterministe (ex. tls-https-disabled, headers-csp-absent).
        category (str): Domaine (tls, headers, cookies, exposed_files, directory_listing, robots_txt, tech_fingerprinting).
        title (str): Libellé court du problème.
        severity (str): critical, high, medium, low, info.
        evidence (str): Détail technique (message ou extrait).
        recommendation (str): Action corrective (texte ou clé catalogue).
        references (tuple[str, ...]): Liens OWASP, MDN, etc.
    """

    id: str
    category: str
    title: str
    severity: str
    evidence: str
    recommendation: str
    references: tuple[str, ...]
    owasp_categories: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        """Sérialise pour le payload SSE."""
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "references": list(self.references),
            "owasp_categories": list(self.owasp_categories),
        }
