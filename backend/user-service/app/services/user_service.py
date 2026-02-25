"""Service métier pour la gestion des utilisateurs.

Ce module contient la logique métier pour les opérations utilisateur,
séparée de la logique d'accès à Cognito et de la logique de routage.
"""

import logging
from typing import Dict, Optional

from common.cognito import CLIENT_ID

from app.exceptions import CognitoConfigurationError, FederatedUserError, InvalidPasswordError
from app.schemas.user import ServiceResult
from app.services.cognito_service import change_user_password, update_user_attributes, verify_user_password

logger = logging.getLogger(__name__)


def update_user_profile(user_claims: Dict, given_name: Optional[str], family_name: Optional[str]) -> ServiceResult:
    """Met à jour le profil utilisateur (prénom, nom).

    Args:
        user_claims (Dict): Claims du token JWT de l'utilisateur.
        given_name (Optional[str]): Nouveau prénom de l'utilisateur.
        family_name (Optional[str]): Nouveau nom de famille de l'utilisateur.

    Returns:
        ServiceResult: Résultat de l'opération avec success et message.

    Raises:
        ValueError: Si les données sont invalides ou si l'identité ne peut pas être déterminée.
    """
    # Extraire le username (sub) depuis le token JWT
    username = user_claims.get("sub")
    email = user_claims.get("email")

    if not username:
        raise ValueError("Impossible de déterminer l'identité de l'utilisateur")

    # Préparer les attributs à mettre à jour
    attributes = {}
    if given_name is not None:
        attributes["given_name"] = given_name
    if family_name is not None:
        attributes["family_name"] = family_name

    if not attributes:
        raise ValueError("Aucun attribut à mettre à jour")

    # Mettre à jour dans Cognito
    # Utiliser l'email comme username si disponible, sinon le sub
    cognito_username = email if email else username
    update_user_attributes(cognito_username, attributes)

    return ServiceResult(
        success=True,
        message="Profil mis à jour avec succès",
    )


def change_user_password_service(user_claims: Dict, current_password: str, new_password: str) -> ServiceResult:
    """Change le mot de passe de l'utilisateur.

    Args:
        user_claims (Dict): Claims du token JWT de l'utilisateur.
        current_password (str): Mot de passe actuel de l'utilisateur.
        new_password (str): Nouveau mot de passe de l'utilisateur.

    Returns:
        ServiceResult: Résultat de l'opération avec success et message.

    Raises:
        ValueError: Si les données sont invalides ou si l'identité ne peut pas être déterminée.
        CognitoConfigurationError: Si la configuration Cognito est incomplète.
        InvalidPasswordError: Si le mot de passe actuel est incorrect.
        FederatedUserError: Si l'utilisateur est fédéré (pas de mot de passe stocké).
    """
    # Extraire le username depuis le token JWT
    # Le token contient "sub" (UUID) et "username" (peut être l'email ou le sub selon la config Cognito)
    username = user_claims.get("username")

    if not username:
        raise ValueError("Impossible de déterminer l'identité de l'utilisateur (username manquant)")

    if not CLIENT_ID:
        raise CognitoConfigurationError("Configuration Cognito incomplète (CLIENT_ID manquant)")

    # Vérifier le mot de passe actuel avant de le changer
    # Cela nécessite que ALLOW_ADMIN_USER_PASSWORD_AUTH soit activé dans Cognito
    # Note: Pour les utilisateurs fédérés (Google, Facebook, etc.), ils n'ont pas de mot de passe
    # stocké dans Cognito, donc la vérification échouera. On gère ce cas avec une exception spécifique.
    try:
        is_valid = verify_user_password(username, current_password, CLIENT_ID)
        if not is_valid:
            raise InvalidPasswordError("Mot de passe actuel incorrect")
    except FederatedUserError:
        # Utilisateur fédéré détecté, on permet la création d'un nouveau mot de passe
        # Pour les utilisateurs fédérés, on peut directement créer un mot de passe
        # Cela leur permettra de se connecter avec email/mot de passe en plus du provider externe
        pass
    except InvalidPasswordError:
        # Mot de passe incorrect, propager l'erreur
        raise

    # Changer le mot de passe (ou le créer pour les utilisateurs fédérés)
    # Utiliser le username pour admin_set_user_password
    change_user_password(username, new_password, permanent=True)

    return ServiceResult(
        success=True,
        message="Mot de passe changé avec succès",
    )
