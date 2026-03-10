"""Schémas de réponse API communs à tous les micro-services.

Ces modèles Pydantic fournissent un typage strict et uniforme
pour les réponses JSON les plus fréquentes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ──────────────────────────── Réponses génériques ────────────────────────────


class SuccessResponse(BaseModel):
    """Réponse générique de succès."""

    success: bool = Field(default=True, description="Opération réussie")
    message: str = Field(description="Message de confirmation")


class ErrorResponse(BaseModel):
    """Réponse générique d'erreur."""

    success: bool = Field(default=False, description="Opération échouée")
    error: str = Field(description="Message d'erreur")
    detail: Optional[str] = Field(default=None, description="Détails additionnels")


class DeleteResponse(BaseModel):
    """Réponse de suppression réussie."""

    success: bool = Field(default=True, description="Suppression réussie")
    message: str = Field(default="Suppression effectuée", description="Message de confirmation")


class PaginatedResponse(BaseModel):
    """Réponse paginée générique."""

    items: List[Dict[str, Any]] = Field(description="Éléments de la page")
    total: int = Field(description="Nombre total d'éléments")
    limit: int = Field(description="Taille de la page")
    offset: int = Field(description="Décalage courant")


def make_pagination_meta(*, total: int, limit: int, offset: int) -> dict:
    """Calcule les métadonnées de pagination à partir de limit/offset.

    Args:
        total: Nombre total d'éléments.
        limit: Nombre d'éléments demandés (per_page).
        offset: Décalage (0-indexé).

    Returns:
        dict avec total, page, per_page, total_pages.
    """
    per_page = max(limit, 1)
    page = (offset // per_page) + 1
    total_pages = max((total + per_page - 1) // per_page, 1) if total > 0 else 0
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }
