"""Schémas Pydantic pour les endpoints des clés API."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from app.models.api_key import ApiKey


class ApiKeyCreateRequest(BaseModel):
    """Requête de création d'une clé API."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nom de la clé (unique par utilisateur)",
    )
    ttl_days: int | None = Field(
        default=None,
        description="Durée de validité en jours (null = défaut config, typiquement 30). Ignoré si expires_at fourni.",
    )
    expires_at: str | None = Field(
        default=None,
        description="Date d'expiration au format AAAA-MM-JJ. Prioritaire sur ttl_days.",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags optionnels (ex. production, CI). Max 10 tags de 50 caractères.",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Description optionnelle de la clé.",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Valide et nettoie les tags (max 10, 50 caractères chacun)."""
        if not v:
            return v
        if len(v) > 10:
            raise ValueError("Maximum 10 tags")
        for t in v:
            if len(t) > 50:
                raise ValueError("Chaque tag doit faire au plus 50 caractères")
        return [t.strip() for t in v if t and t.strip()] or None


class ApiKeyUpdateExpiryRequest(BaseModel):
    """Requête pour modifier la date d'expiration d'une clé API.

    Fournir soit ttl_days, soit expires_at (priorité à expires_at si les deux).
    """

    ttl_days: int | None = Field(
        default=None,
        description="Durée de validité en jours (0 = pas d'expiration).",
    )
    expires_at: str | None = Field(
        default=None,
        description="Date d'expiration au format ISO AAAA-MM-JJ.",
    )


class ApiKeyUpdateRequest(BaseModel):
    """Requête pour modifier une clé API (nom, validité, tags, restriction IP)."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nouveau nom (unique par utilisateur). Si absent, conservé.",
    )
    ttl_days: int | None = Field(
        default=None,
        description="Durée de validité en jours (0 = pas d'expiration). Ignoré si expires_at fourni.",
    )
    expires_at: str | None = Field(
        default=None,
        description="Date d'expiration au format AAAA-MM-JJ. Prioritaire sur ttl_days.",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags optionnels. Liste vide = supprimer tous les tags.",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Description optionnelle. Chaîne vide = supprimer.",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Valide et nettoie les tags (max 10, 50 caractères chacun)."""
        if not v:
            return v
        if len(v) > 10:
            raise ValueError("Maximum 10 tags")
        for t in v:
            if len(t) > 50:
                raise ValueError("Chaque tag doit faire au plus 50 caractères")
        return [t.strip() for t in v if t and t.strip()] or None


class ApiKeyCreateResponse(BaseModel):
    """Réponse à la création — contient la clé en clair (affichée une seule fois)."""

    id: str = Field(..., description="UUID de la clé")
    key: str = Field(..., description="Clé en clair (à copier immédiatement, jamais réaffichée)")
    name: str = Field(..., description="Nom de la clé")
    created_at: datetime = Field(..., description="Date de création")
    expires_at: datetime | None = Field(None, description="Date d'expiration (null = jamais)")


class ApiKeyListItem(BaseModel):
    """Élément de liste des clés (sans valeur)."""

    id: str = Field(..., description="UUID de la clé")
    name: str = Field(..., description="Nom de la clé")
    prefix: str = Field(..., description="Préfixe affiché (ex. sk_xxx...)")
    created_at: datetime = Field(..., description="Date de création")
    last_used_at: Optional[datetime] = Field(None, description="Dernière utilisation")
    expires_at: Optional[datetime] = Field(None, description="Date d'expiration (null = jamais)")
    tags: Optional[list[str]] = Field(None, description="Tags optionnels")
    description: Optional[str] = Field(None, description="Description optionnelle")

    @classmethod
    def from_model(cls, api_key: "ApiKey") -> "ApiKeyListItem":
        """Convertit un modèle ApiKey en ApiKeyListItem."""
        return cls(
            id=str(api_key.id),
            name=api_key.name,
            prefix=api_key.prefix,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            tags=api_key.tags,
            description=api_key.description,
        )

    class Config:
        """Configuration Pydantic pour sérialisation depuis les modèles ORM."""

        from_attributes = True


class ApiKeyListResponse(BaseModel):
    """Liste des clés API de l'utilisateur."""

    items: List[ApiKeyListItem] = Field(..., description="Liste des clés")
