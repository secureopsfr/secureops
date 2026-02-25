"""Modèle de stockage des événements analytics côté site.

Ce module définit la table pour stocker les événements de tracking utilisateur
(page views, durée de visite, scroll depth, clics, etc.) afin d'alimenter
le dashboard analytics dans l'admin.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base


class AnalyticsEvent(Base):
    """Représente un événement analytics enregistré depuis le frontend.

    Attributes:
        id (UUID): identifiant unique de l'événement.
        session_id (str): identifiant de session (UUID généré côté client en sessionStorage).
        user_id_hash (str | None): hash HMAC-SHA256 de l'identifiant utilisateur (RGPD).
        event_type (str): type d'événement (page_view, page_exit, session_start, click, scroll_depth).
        page (str): URL/chemin de la page concernée.
        referrer (str | None): referrer HTTP (d'où vient l'utilisateur).
        duration_ms (float | None): temps passé sur la page en millisecondes (pour page_exit).
        metadata (dict | None): données additionnelles flexibles (scroll_depth, click_target, etc.).
        viewport (str | None): dimensions du viewport client (ex: "1920x1080").
        device_type (str | None): type d'appareil (desktop, mobile, tablet).
        language (str | None): langue du navigateur (ex: "fr-FR").
        created_at (datetime): horodatage de l'événement en UTC.
    """

    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    session_id = Column(String(64), nullable=False, index=True)
    user_id_hash = Column(String(128), nullable=True, index=True)
    event_type = Column(String(32), nullable=False, index=True)
    page = Column(String(512), nullable=False, index=True)
    referrer = Column(String(512), nullable=True)
    duration_ms = Column(Float, nullable=True)
    event_metadata = Column("event_metadata", JSONB, nullable=True)
    viewport = Column(String(32), nullable=True)
    device_type = Column(String(16), nullable=True)
    language = Column(String(16), nullable=True)
    country = Column(String(2), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self) -> str:  # pragma: no cover
        """Retourne une représentation concise utile pour le debug.

        Returns:
            str: représentation texte de l'objet.
        """
        return f"AnalyticsEvent(session_id={self.session_id!r}, event_type={self.event_type!r}, " f"page={self.page!r}, created_at={self.created_at})"
