"""Modèle SQLAlchemy pour la table scheduled_scans (scans planifiés)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class ScheduledScan(Base):
    """Modèle représentant un scan planifié (monitoring continu).

    Attributes:
        id: UUID interne (clé primaire).
        user_id: Référence vers l'utilisateur propriétaire.
        url: URL à scanner.
        frequency: Fréquence (daily, weekly, monthly).
        schedule_hour: Heure d'exécution (0-23).
        schedule_minute: Minute d'exécution (0-59).
        schedule_day_of_week: Jour de la semaine pour weekly (0=lundi, 6=dimanche).
        schedule_day_of_month: Jour du mois pour monthly (1-31).
        timezone: Fuseau utilisateur (ex. Europe/Paris) pour interpréter schedule_hour/minute.
        next_run_at: Prochaine exécution planifiée.
        enabled: Scan actif ou en pause.
        created_at: Date de création.
        updated_at: Dernière modification.
    """

    __tablename__ = "scheduled_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, comment="UUID interne (clé primaire)")

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence vers l'utilisateur",
    )

    url = Column(String(2048), nullable=False, comment="URL à scanner")

    scan_type = Column(
        String(20),
        nullable=False,
        default="frontend",
        comment="Type de scan : frontend, backend, custom",
    )

    frequency = Column(String(20), nullable=False, comment="Fréquence : daily, weekly, monthly")

    schedule_hour = Column(Integer, nullable=False, default=2, comment="Heure d'exécution (0-23)")
    schedule_minute = Column(Integer, nullable=False, default=0, comment="Minute d'exécution (0-59)")
    schedule_day_of_week = Column(Integer, nullable=True, comment="Jour semaine pour weekly (0=lundi, 6=dimanche)")
    schedule_day_of_month = Column(Integer, nullable=True, comment="Jour du mois pour monthly (1-31)")

    timezone = Column(String(64), nullable=True, comment="Fuseau utilisateur (ex. Europe/Paris) pour schedule_hour/minute")

    next_run_at = Column(DateTime(timezone=True), nullable=False, index=True, comment="Prochaine exécution planifiée")

    enabled = Column(Boolean, nullable=False, default=True, comment="Scan actif ou en pause")

    scan_alerts_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Alertes email pour régression score ou finding critical (ce scan)",
    )

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, comment="Date de création")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        comment="Dernière modification",
    )

    user = relationship("User", back_populates="scheduled_scans")

    def __repr__(self) -> str:
        """Représentation string du scan planifié."""
        return f"<ScheduledScan(id={self.id}, url={self.url[:50]}..., frequency={self.frequency})>"
