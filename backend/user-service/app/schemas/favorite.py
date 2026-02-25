"""Schémas Pydantic pour les endpoints de favoris."""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class FavoriteCreateRequest(BaseModel):
    """Schéma pour la création d'un favori."""

    search_type: str = Field(..., description="Type de recherche effectuée")
    query_json: Dict[str, Any] = Field(..., description="Données JSON de la requête")


class FavoriteResponse(BaseModel):
    """Schéma pour la réponse d'un favori."""

    id: str = Field(..., description="UUID du favori")
    user_id: str = Field(..., description="UUID de l'utilisateur")
    search_type: str = Field(..., description="Type de recherche")
    query_json: Dict[str, Any] = Field(..., description="Données JSON de la requête")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        """Configuration Pydantic."""

        from_attributes = True


class FavoriteListResponse(BaseModel):
    """Schéma pour la réponse d'une liste de favoris avec pagination."""

    items: list[FavoriteResponse] = Field(..., description="Liste des entrées de favoris")
    total: int = Field(..., description="Nombre total d'entrées")
    page: int = Field(1, ge=1, description="Numéro de page actuel (1-indexé)")
    per_page: int = Field(20, ge=1, description="Nombre d'éléments par page")
    total_pages: int = Field(0, ge=0, description="Nombre total de pages")
