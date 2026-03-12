"""Modèle SQLAlchemy pour la table scans (historique des scans de posture sécurité)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class Scan(Base):
    """Modèle représentant un scan de posture sécurité sauvegardé dans l'historique.

    Attributes:
        id: UUID interne (clé primaire).
        user_id: Référence vers l'utilisateur propriétaire.
        url: URL scannée.
        status: Statut du scan (success, error).
        score: Note /100 (nullable si erreur avant fin).
        findings_json: Findings normalisés (JSONB).
        timestamp: Horodatage ISO du scan.
        duration: Durée du scan en secondes.
        created_at: Date de création en base.
    """

    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, comment="UUID interne (clé primaire)")

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence vers l'utilisateur",
    )

    url = Column(String(2048), nullable=False, comment="URL scannée")

    scan_type = Column(
        String(20),
        nullable=False,
        default="frontend",
        comment="Type de scan : frontend, backend, custom",
    )
    result_mode = Column(
        String(10),
        nullable=False,
        default="single",
        comment="Mode du résultat : single ou multi",
    )

    status = Column(String(50), nullable=False, default="success", comment="Statut du scan (success, error)")

    score = Column(Integer, nullable=True, comment="Note /100 (nullable si erreur)")

    findings_json = Column(JSONB, nullable=False, comment="Findings normalisés (liste de dicts)")

    category_summaries_json = Column(
        JSONB,
        nullable=True,
        comment="Résumés par catégorie (checks_count, label, etc.)",
    )
    page_results_json = Column(
        JSONB,
        nullable=True,
        comment="Résultats par page pour un scan multi-URL",
    )
    urls_json = Column(
        JSONB,
        nullable=True,
        comment="Liste des URLs scannées pour un scan multi-URL",
    )

    timestamp = Column(DateTime(timezone=True), nullable=False, comment="Horodatage ISO du scan")

    duration = Column(Float, nullable=False, comment="Durée du scan en secondes")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True, comment="Date de création")

    user = relationship("User", back_populates="scans")

    def __repr__(self) -> str:
        """Représentation string du scan."""
        return f"<Scan(id={self.id}, user_id={self.user_id}, url={self.url[:50]}..., score={self.score})>"
