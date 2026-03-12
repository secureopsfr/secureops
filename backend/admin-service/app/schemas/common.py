"""Schémas communs pour l'application."""

from typing import List, Optional

from common.schemas import make_pagination_meta  # noqa: F401
from pydantic import BaseModel, EmailStr, Field


class ErrorResponse(BaseModel):
    """Schéma de réponse pour les erreurs."""

    error: str
    detail: Optional[str] = None


class PaginationMeta(BaseModel):
    """Métadonnées de pagination incluses dans toutes les réponses paginées."""

    total: int = Field(..., description="Nombre total d'éléments")
    page: int = Field(..., ge=1, description="Numéro de page actuel (1-indexé)")
    per_page: int = Field(..., ge=1, description="Nombre d'éléments par page")
    total_pages: int = Field(..., ge=0, description="Nombre total de pages")


class ContactMessageResponse(BaseModel):
    """Schéma de réponse pour un message de contact."""

    id: int
    first_name: str
    last_name: str
    email: str
    subject: str
    message: str
    status: str
    created_at: str
    updated_at: str


class ContactMessageUpdateRequest(BaseModel):
    """Schéma de requête pour la mise à jour d'un message de contact."""

    status: str


class ContactMessageRequest(BaseModel):
    """Schéma de requête pour un message de contact."""

    first_name: str = Field(..., max_length=100, description="Prénom (max 100 caractères)")
    last_name: str = Field(..., max_length=100, description="Nom (max 100 caractères)")
    email: EmailStr = Field(..., max_length=255, description="Adresse email (max 255 caractères)")
    subject: str = Field(..., max_length=100, description="Sujet (max 100 caractères)")
    message: str = Field(..., max_length=5000, description="Message de contact (max 5000 caractères)")
    turnstile_token: str = Field(..., description="Token de vérification Cloudflare Turnstile")


class ContactMessageCreateResponse(BaseModel):
    """Schéma de réponse pour la création d'un message de contact."""

    id: int
    message: str


class MailingListResponse(BaseModel):
    """Schéma de réponse pour la mailing list."""

    entries: List[dict]
    total: int
    page: int = 1
    per_page: int = 100
    total_pages: int = 0


class MailingListSubscribeResponse(BaseModel):
    """Schéma de réponse pour l'inscription à la mailing list."""

    success: bool
    message: str
    email: str


class NewsletterEmailRequest(BaseModel):
    """Schéma de requête pour un email newsletter."""

    subject: str
    content: str
    template_name: Optional[str] = None


class NewsletterEmailResponse(BaseModel):
    """Schéma de réponse pour un email newsletter."""

    id: int
    subject: str
    content: str
    sent_at: str
    recipients_count: int
    status: str
    scheduled_at: Optional[str] = None
    is_scheduled: bool


class NewsletterEmailCreateResponse(BaseModel):
    """Schéma de réponse pour la création d'un email newsletter."""

    id: int
    subject: str
    message: str


class NewsletterEmailScheduleRequest(BaseModel):
    """Schéma de requête pour programmer un email newsletter."""

    email_id: int
    scheduled_at: str


class NewsletterSendRequest(BaseModel):
    """Schéma de requête pour envoyer un email newsletter."""

    email_id: int


class NotificationEmailRequest(BaseModel):
    """Schéma de requête pour créer/mettre à jour un email de notification."""

    subject: str
    content: str
    template_name: Optional[str] = None


class NotificationEmailResponse(BaseModel):
    """Schéma de réponse pour un email de notification."""

    id: int
    subject: str
    content: str
    sent_at: Optional[str] = None
    recipients_count: int
    status: str
    scheduled_at: Optional[str] = None
    is_scheduled: bool


class NotificationEmailCreateResponse(BaseModel):
    """Schéma de réponse pour la création d'un email de notification."""

    id: int
    subject: str
    message: str


class NotificationEmailScheduleRequest(BaseModel):
    """Schéma de requête pour programmer un email de notification."""

    email_id: int
    scheduled_at: str  # Format ISO datetime


class NotificationSendRequest(BaseModel):
    """Schéma de requête pour envoyer un email de notification."""

    email_id: int
