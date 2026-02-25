"""Modèles pour le système d'alerting / monitoring proactif.

Ce module définit les tables pour stocker les règles d'alerte configurées
par les admins et les événements d'alerte déclenchés.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class AlertRule(Base):
    """Règle d'alerte configurable par l'administrateur.

    Attributes:
        id (UUID): identifiant unique de la règle.
        name (str): nom lisible de la règle (ex: "Taux d'erreurs élevé").
        metric (str): métrique surveillée (error_rate, service_down, response_time).
        condition (str): condition de déclenchement (gt, lt, eq — greater than, less than, equal).
        threshold (float): seuil de déclenchement.
        window_minutes (int): fenêtre temporelle pour évaluer la métrique.
        service_filter (str | None): filtre sur un service spécifique (None = tous).
        notify_email (bool): envoyer un email à l'admin lors du déclenchement.
        enabled (bool): si la règle est active.
        cooldown_minutes (int): délai minimum entre deux alertes (évite le spam).
        created_at (datetime): date de création.
        updated_at (datetime): date de dernière modification.
    """

    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False)
    metric = Column(String(50), nullable=False, index=True)
    condition = Column(String(10), nullable=False, default="gt")
    threshold = Column(Float, nullable=False)
    window_minutes = Column(Integer, nullable=False, default=5)
    service_filter = Column(String(64), nullable=True)
    notify_email = Column(Boolean, nullable=False, default=True)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    cooldown_minutes = Column(Integer, nullable=False, default=30)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def __repr__(self) -> str:  # pragma: no cover
        """Retourne une représentation concise utile pour le debug."""
        return f"AlertRule(name={self.name!r}, metric={self.metric!r}, threshold={self.threshold}, enabled={self.enabled})"


class AlertEvent(Base):
    """Événement d'alerte déclenché lorsqu'une règle est violée.

    Attributes:
        id (UUID): identifiant unique de l'événement.
        rule_id (UUID): référence vers la règle qui a déclenché l'alerte.
        rule_name (str): nom de la règle (dénormalisé pour historique).
        metric (str): métrique concernée.
        current_value (float): valeur actuelle qui a déclenché l'alerte.
        threshold (float): seuil configuré.
        severity (str): gravité (warning, critical).
        message (str): message descriptif.
        acknowledged (bool): si l'alerte a été acquittée par un admin.
        acknowledged_by (str | None): email de l'admin qui a acquitté.
        acknowledged_at (datetime | None): date d'acquittement.
        created_at (datetime): date de déclenchement.
    """

    __tablename__ = "alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    rule_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    rule_name = Column(String(255), nullable=False)
    metric = Column(String(50), nullable=False, index=True)
    current_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False, default="warning", index=True)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, nullable=False, default=False, index=True)
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self) -> str:  # pragma: no cover
        """Retourne une représentation concise utile pour le debug."""
        return (
            f"AlertEvent(rule={self.rule_name!r}, metric={self.metric!r}, "
            f"value={self.current_value}, severity={self.severity!r}, ack={self.acknowledged})"
        )
