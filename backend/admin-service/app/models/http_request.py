"""Modèle de stockage des requêtes HTTP.

Ce module définit la table pour stocker toutes les requêtes HTTP avec leurs données
(une entrée par requête) afin d'alimenter les statistiques et le tableau côté frontend
(moyennes, percentiles, minimums/maximums, variances par route).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base


class HttpRequest(Base):
    """Représente une requête HTTP enregistrée avec toutes ses données.

    Attributes:
        id (UUID): identifiant unique de la mesure.
        service_prefix (str): préfixe du service (ex: "admin", "user", "scan").
        endpoint (str): chemin complet de l'endpoint avec paramètres (ex: "/analytics-query/dvf/bbox-sales/40.21/-10.82").
        route (str | None): route de base sans paramètres ni valeurs numériques (ex: "/analytics-query/dvf/bbox-sales") (optionnel).
        method (str): méthode HTTP utilisée (GET, POST, PUT, DELETE, etc.).
        status_code (int): code de statut HTTP de la réponse (200, 404, 500, 504, etc.).
        duration_ms (float): durée de traitement de la requête en millisecondes.
        success (bool): indicateur de succès (true pour codes 2xx/3xx, false sinon).
        created_at (datetime): horodatage d'enregistrement en UTC.
        client_ip_hash (str | None): adresse IP du client pseudonymisée via HMAC-SHA256 pour RGPD (optionnel).
        request_params (dict | None): paramètres de la requête (query params, body) en JSONB (optionnel).
        user_id_hash (str | None): hash pseudonymisé HMAC-SHA256 de l'identifiant utilisateur pour RGPD (optionnel).
        request_size_bytes (int | None): taille de la requête envoyée en octets (pour corrélation taille/latence) (optionnel).
        response_size_bytes (int | None): taille de la réponse reçue en octets (pour métriques de volumétrie) (optionnel).
        request_size_kb (float | None): taille de la requête envoyée en kilooctets (calculée automatiquement) (optionnel).
        response_size_kb (float | None): taille de la réponse reçue en kilooctets (calculée automatiquement) (optionnel).
    """

    __tablename__ = "http_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    service_prefix = Column(String(64), nullable=False, index=True)
    endpoint = Column(String(256), nullable=False, index=True)
    route = Column(String(256), nullable=True, index=True)
    method = Column(String(16), nullable=False, index=True)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Float, nullable=False, index=True)
    success = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)

    # Métadonnées additionnelles (facultatives)
    client_ip_hash = Column(String(64), nullable=True)
    request_params = Column(JSONB, nullable=True)
    user_id_hash = Column(String(128), nullable=True, index=True)
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    request_size_kb = Column(Float, nullable=True)
    response_size_kb = Column(Float, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        """Retourne une représentation concise utile pour le debug.

        Returns:
            str: représentation texte de l'objet.
        """
        return (
            f"HttpRequest(service_prefix={self.service_prefix!r}, endpoint={self.endpoint!r}, "
            f"method={self.method!r}, status={self.status_code}, duration_ms={self.duration_ms})"
        )
