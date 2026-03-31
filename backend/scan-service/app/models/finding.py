"""Schéma Finding : représentation normalisée d'un problème de sécurité détecté."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """Finding normalisé : id, catégorie, titre, sévérité, preuve, recommandation, références.

    Attributes:
        id (str): Slug déterministe (ex. tls-https-disabled, headers-csp-absent).
        category (str): Domaine (tls, headers, cookies, open_redirect, sqli, …).
        title (str): Libellé court du problème.
        severity (str): critical, high, medium, low, info.
        evidence (str): Détail technique (message ou extrait).
        recommendation (str): Action corrective (texte ou clé catalogue).
        references (tuple[str, ...]): Liens OWASP, MDN, etc.
        owasp_categories (tuple[str, ...]): Catégories OWASP Top 10.

    Champs de traçabilité pour les scans intrusifs (optionnels) :
        request_method (str | None): Méthode HTTP utilisée pour le probe (GET, POST…).
        request_url (str | None): URL complète du probe envoyé.
        request_headers (tuple[tuple[str, str], ...] | None): Headers HTTP du probe.
        request_body (str | None): Corps du probe (tronqué à 2 Ko max).
        payload_id (str | None): Identifiant du payload utilisé (de payload_engine).
        raw_evidence (str | None): Extrait brut de la réponse (tronqué à 4 Ko).
    """

    id: str
    category: str
    title: str
    severity: str
    evidence: str
    recommendation: str
    references: tuple[str, ...]
    owasp_categories: tuple[str, ...] = ()
    # Champs de traçabilité intrusif (défaut None = compatibilité avec le passif)
    request_method: str | None = None
    request_url: str | None = None
    request_headers: tuple[tuple[str, str], ...] | None = None
    request_body: str | None = None
    payload_id: str | None = None
    raw_evidence: str | None = None

    def to_dict(self) -> dict:
        """Sérialise pour le payload SSE et le PDF."""
        d: dict = {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "references": list(self.references),
            "owasp_categories": list(self.owasp_categories),
        }
        # Inclure les champs de traçabilité uniquement s'ils sont renseignés
        if self.request_method is not None:
            d["request_method"] = self.request_method
        if self.request_url is not None:
            d["request_url"] = self.request_url
        if self.request_headers is not None:
            d["request_headers"] = dict(self.request_headers)
        if self.request_body is not None:
            d["request_body"] = self.request_body[:2048]
        if self.payload_id is not None:
            d["payload_id"] = self.payload_id
        if self.raw_evidence is not None:
            d["raw_evidence"] = self.raw_evidence[:4096]
        return d
