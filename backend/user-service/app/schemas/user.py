"""Schémas Pydantic pour les endpoints utilisateur."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LanguageEnum(str, Enum):
    """Langues supportées."""

    FR = "fr"
    EN = "en"


class ServiceResult(BaseModel):
    """Schéma de base pour les résultats des services métier.

    Attributes:
        success (bool): Indique si l'opération a réussi.
        message (str): Message de confirmation ou d'erreur.
    """

    success: bool = Field(description="Indique si l'opération a réussi")
    message: str = Field(description="Message de confirmation ou d'erreur")


class ProfileUpdateRequest(BaseModel):
    """Schéma pour la mise à jour du profil utilisateur.

    Attributes:
        given_name (Optional[str]): Prénom de l'utilisateur.
        family_name (Optional[str]): Nom de famille de l'utilisateur.
    """

    given_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Prénom de l'utilisateur")
    family_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Nom de famille de l'utilisateur")


class ProfileUpdateResponse(BaseModel):
    """Schéma de réponse pour la mise à jour du profil.

    Attributes:
        success (bool): Indique si la mise à jour a réussi.
        message (str): Message de confirmation.
    """

    success: bool = Field(description="Indique si la mise à jour a réussi")
    message: str = Field(description="Message de confirmation")


class ChangePasswordRequest(BaseModel):
    """Schéma pour le changement de mot de passe.

    Attributes:
        current_password (str): Mot de passe actuel.
        new_password (str): Nouveau mot de passe.
    """

    current_password: str = Field(..., min_length=1, description="Mot de passe actuel")
    new_password: str = Field(..., min_length=8, max_length=128, description="Nouveau mot de passe")


class ChangePasswordResponse(BaseModel):
    """Schéma de réponse pour le changement de mot de passe.

    Attributes:
        success (bool): Indique si le changement a réussi.
        message (str): Message de confirmation.
    """

    success: bool = Field(description="Indique si le changement a réussi")
    message: str = Field(description="Message de confirmation")


class SubscriptionResponse(BaseModel):
    """Schéma de réponse pour l'abonnement utilisateur.

    Attributes:
        plan (str): Plan d'abonnement (free / premium).
        status (str): Statut de l'abonnement (active / canceled / trial).
        stripe_customer_id (Optional[str]): Identifiant Stripe du client.
        current_period_end (Optional[str]): Date de fin de la période courante au format ISO.
        newsletter_enabled (bool): Inscription à la newsletter.
        new_features_notifications_enabled (bool): Notifications par mail pour nouvelles données ou features.
    """

    plan: str = Field(description="Plan d'abonnement (free / premium)")
    status: str = Field(description="Statut de l'abonnement (active / canceled / trial)")
    stripe_customer_id: Optional[str] = Field(None, description="Identifiant Stripe du client")
    current_period_end: Optional[str] = Field(None, description="Date de fin de la période courante au format ISO")
    newsletter_enabled: bool = Field(default=False, description="Inscription à la newsletter")
    new_features_notifications_enabled: bool = Field(default=False, description="Notifications par mail pour nouvelles données ou features")

    class Config:
        """Configuration Pydantic."""

        from_attributes = True


class ThemePreferenceUpdateRequest(BaseModel):
    """Schéma pour la mise à jour de la préférence de thème.

    Attributes:
        dark_mode (bool): True pour le mode sombre, False pour le mode clair.
    """

    dark_mode: bool = Field(..., description="True pour le mode sombre, False pour le mode clair")


class ThemePreferenceResponse(BaseModel):
    """Schéma de réponse pour la préférence de thème.

    Attributes:
        success (bool): Indique si la mise à jour a réussi.
        dark_mode (bool): Valeur actuelle de la préférence de thème.
    """

    success: bool = Field(description="Indique si la mise à jour a réussi")
    dark_mode: bool = Field(description="Valeur actuelle de la préférence de thème")


class LanguagePreferenceUpdateRequest(BaseModel):
    """Schéma pour la mise à jour de la préférence de langue.

    Attributes:
        language (LanguageEnum): Langue préférée (fr ou en).
    """

    language: LanguageEnum = Field(..., description="Langue préférée (fr ou en)")


class LanguagePreferenceResponse(BaseModel):
    """Schéma de réponse pour la préférence de langue.

    Attributes:
        success (bool): Indique si la mise à jour a réussi.
        language (str): Valeur actuelle de la langue.
    """

    success: bool = Field(description="Indique si la mise à jour a réussi")
    language: str = Field(description="Valeur actuelle de la langue")


class SubscriptionPreferencesUpdateRequest(BaseModel):
    """Schéma pour la mise à jour des préférences d'abonnement.

    Attributes:
        newsletter_enabled (Optional[bool]): Inscription à la newsletter.
        new_features_notifications_enabled (Optional[bool]): Notifications par mail pour nouvelles données ou features.
    """

    newsletter_enabled: Optional[bool] = Field(None, description="Inscription à la newsletter")
    new_features_notifications_enabled: Optional[bool] = Field(None, description="Notifications par mail pour nouvelles données ou features")
