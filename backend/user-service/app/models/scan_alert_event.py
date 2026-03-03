"""Modèle SQLAlchemy pour la table scan_alert_events (historique des alertes)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class ScanAlertEvent(Base):
    """Événement d'alerte déclenché sur un scan planifié.

    Attributes:
        id: UUID interne.
        user_id: Utilisateur propriétaire.
        scheduled_scan_id: Scan planifié concerné (nullable si supprimé).
        url: URL scannée.
        alert_type: regression ou critical_finding.
        email_sent: True si l'email a été envoyé avec succès.
        triggered_at: Date/heure du déclenchement.
    """

    __tablename__ = "scan_alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_scan_id = Column(UUID(as_uuid=True), ForeignKey("scheduled_scans.id", ondelete="SET NULL"), nullable=True, index=True)
    url = Column(String(2048), nullable=False)
    alert_type = Column(String(50), nullable=False)
    email_sent = Column(Boolean, nullable=False, default=False)
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
