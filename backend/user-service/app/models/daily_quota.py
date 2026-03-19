"""Modèle SQLAlchemy pour la table daily_quotas."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class DailyQuota(Base):
    """Quota journalier d'utilisation (scans + crawls cumulés) par utilisateur.

    Identifié par cognito_sub (stable, unique par utilisateur).
    Reset automatique chaque jour UTC (nouvelle ligne par date).
    """

    __tablename__ = "daily_quotas"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="UUID interne (clé primaire)",
    )

    cognito_sub = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Identifiant Cognito de l'utilisateur",
    )

    date_utc = Column(
        Date,
        nullable=False,
        comment="Date UTC du quota (YYYY-MM-DD)",
    )

    jobs_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Nombre de jobs (scans + crawls) lancés ce jour",
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="Date de création de la ligne",
    )

    __table_args__ = (UniqueConstraint("cognito_sub", "date_utc", name="uq_daily_quotas_sub_date"),)

    def __repr__(self) -> str:
        """Représentation string pour debug."""
        return f"<DailyQuota(cognito_sub={self.cognito_sub!r}, date={self.date_utc}, count={self.jobs_count})>"
