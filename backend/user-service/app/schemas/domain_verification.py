"""Schémas Pydantic pour la vérification DNS des domaines."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DomainVerificationChallengeCreateRequest(BaseModel):
    """URL ou domaine à préparer pour la vérification TXT."""

    url: str = Field(..., min_length=1, description="URL complète ou hostname (https://example.com ou example.com)")


class DomainVerificationChallengeResponse(BaseModel):
    """Instructions DNS + token à publier (une seule fois)."""

    domain: str
    txt_name: str = Field(..., description="Nom DNS du TXT (FQDN)")
    txt_value: str = Field(..., description="Valeur exacte du TXT")
    challenge_expires_at: datetime
    already_verified: bool = False


class DomainVerificationVerifyRequest(BaseModel):
    """Lancer la vérification DNS pour un domaine (challenge en cours)."""

    domain: str = Field(..., min_length=1)


class DomainVerificationItem(BaseModel):
    """Domaine vérifié."""

    id: UUID
    domain: str
    verified_at: datetime
    expires_at: datetime


class DomainVerificationAssertRequest(BaseModel):
    """[Interne] Vérifie qu'un utilisateur peut scanner ce domaine en mode non passif."""

    cognito_sub: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1, description="Domaine eTLD+1 déjà normalisé")


class DomainVerificationAssertResponse(BaseModel):
    """Réponse de la route interne assert (scan autorisé ou non)."""

    allowed: bool
    reason: Optional[str] = None
