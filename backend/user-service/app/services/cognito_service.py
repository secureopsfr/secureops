"""Service pour interagir avec AWS Cognito.

Ce module fournit des fonctions pour mettre à jour les attributs utilisateur
et changer le mot de passe via l'API Admin de Cognito.
"""

import logging
import os
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError
from common.cognito import REGION, USERPOOL_ID

from app.exceptions import FederatedUserError, UserNotFoundError

logger = logging.getLogger(__name__)


def get_cognito_client():
    """Crée un client Cognito Identity Provider.

    Utilise les credentials AWS depuis les variables d'environnement si disponibles,
    sinon utilise les credentials par défaut de boto3 (~/.aws/credentials ou IAM role).

    Returns:
        boto3.client: Client Cognito configuré.
    """
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    # Créer le client
    if aws_access_key_id and aws_secret_access_key:
        # Utiliser les credentials explicites depuis les variables d'environnement
        client = boto3.client(
            "cognito-idp",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=REGION,
        )
    else:
        # Utiliser les credentials par défaut de boto3
        client = boto3.client("cognito-idp", region_name=REGION)

    return client


def delete_user(username: str) -> None:
    """Supprime un utilisateur dans Cognito.

    Args:
        username (str): Nom d'utilisateur (sub) à supprimer.

    Raises:
        UserNotFoundError: Si l'utilisateur n'existe pas dans Cognito.
        ClientError: Pour les autres erreurs Cognito.
    """
    client = get_cognito_client()

    try:
        client.admin_delete_user(UserPoolId=USERPOOL_ID, Username=username)
        logger.info("Utilisateur supprimé de Cognito: username=%s", username)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "UserNotFoundException":
            logger.warning("Utilisateur non trouvé dans Cognito: username=%s", username)
            raise UserNotFoundError(f"Utilisateur {username} non trouvé dans Cognito")
        logger.error("Erreur lors de la suppression de l'utilisateur dans Cognito: %s", e, exc_info=True)
        raise


def update_user_attributes(username: str, attributes: Dict[str, str]) -> None:
    """Met à jour les attributs d'un utilisateur dans Cognito.

    Args:
        username (str): Nom d'utilisateur (sub ou email).
        attributes (Dict[str, str]): Dictionnaire des attributs à mettre à jour.
            Clés possibles : given_name, family_name, phone_number, etc.

    Raises:
        ValueError: Si les attributs sont vides ou invalides.
        ClientError: Si l'appel à Cognito échoue.
    """
    if not attributes:
        raise ValueError("Aucun attribut à mettre à jour")

    if not USERPOOL_ID:
        raise ValueError("COGNITO_USER_POOL_ID doit être défini")

    # Convertir les attributs au format attendu par Cognito
    cognito_attributes = [{"Name": key, "Value": value} for key, value in attributes.items()]

    try:
        client = get_cognito_client()
        client.admin_update_user_attributes(
            UserPoolId=USERPOOL_ID,
            Username=username,
            UserAttributes=cognito_attributes,
        )
        logger.debug("Attributs mis à jour pour l'utilisateur: %s", username)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", "")
        logger.error("Erreur Cognito lors de la mise à jour des attributs: %s - %s", error_code, error_message)
        raise


def change_user_password(username: str, new_password: str, permanent: bool = True) -> None:
    """Change le mot de passe d'un utilisateur dans Cognito.

    Args:
        username (str): Nom d'utilisateur (sub ou email).
        new_password (str): Nouveau mot de passe.
        permanent (bool): Si True, le mot de passe est permanent (pas de changement forcé).

    Raises:
        ValueError: Si le mot de passe est vide ou invalide.
        ClientError: Si l'appel à Cognito échoue.
    """
    if not new_password:
        raise ValueError("Le mot de passe ne peut pas être vide")

    if len(new_password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères")

    if not USERPOOL_ID:
        raise ValueError("COGNITO_USER_POOL_ID doit être défini")

    try:
        client = get_cognito_client()
        client.admin_set_user_password(
            UserPoolId=USERPOOL_ID,
            Username=username,
            Password=new_password,
            Permanent=permanent,
        )
        logger.debug("Mot de passe changé pour l'utilisateur: %s", username)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", "")
        logger.error("Erreur Cognito lors du changement de mot de passe: %s - %s", error_code, error_message)
        raise


def get_user_email(username: str) -> Optional[str]:
    """Récupère l'email d'un utilisateur depuis Cognito.

    Args:
        username (str): Nom d'utilisateur (sub ou email).

    Returns:
        Optional[str]: L'email de l'utilisateur si trouvé, None si l'utilisateur n'a pas d'email.

    Raises:
        ValueError: Si COGNITO_USER_POOL_ID n'est pas défini.
        UserNotFoundError: Si l'utilisateur n'existe pas dans Cognito.
        ClientError: Pour les autres erreurs Cognito (permissions, etc.).
    """
    if not USERPOOL_ID:
        raise ValueError("COGNITO_USER_POOL_ID doit être défini")

    try:
        client = get_cognito_client()
        response = client.admin_get_user(
            UserPoolId=USERPOOL_ID,
            Username=username,
        )

        # Chercher l'attribut email dans les attributs utilisateur
        for attr in response.get("UserAttributes", []):
            if attr.get("Name") == "email":
                return attr.get("Value")

        return None
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", "")

        if error_code == "UserNotFoundException":
            logger.error("Utilisateur non trouvé: %s", username)
            raise UserNotFoundError(f"Utilisateur non trouvé: {username}") from e

        # Pour les autres erreurs (permissions, etc.), propager l'erreur
        logger.error("Erreur Cognito lors de la récupération de l'email: %s - %s", error_code, error_message)
        raise


def verify_user_password(username: str, password: str, client_id: str) -> bool:
    """Vérifie le mot de passe actuel d'un utilisateur.

    Utilise admin_initiate_auth pour vérifier le mot de passe.

    Args:
        username (str): Nom d'utilisateur (email).
        password (str): Mot de passe à vérifier.
        client_id (str): ID du client Cognito.

    Returns:
        bool: True si le mot de passe est correct, False sinon.

    Raises:
        ValueError: Si les paramètres sont invalides.
        ClientError: Si l'appel à Cognito échoue.
    """
    if not username or not password:
        return False

    if not USERPOOL_ID:
        raise ValueError("COGNITO_USER_POOL_ID doit être défini")

    if not client_id:
        raise ValueError("CLIENT_ID doit être défini")

    try:
        client = get_cognito_client()
        # Utiliser admin_initiate_auth pour vérifier le mot de passe
        # ADMIN_USER_PASSWORD_AUTH est le flow standard pour vérifier un mot de passe avec les APIs admin
        client.admin_initiate_auth(
            UserPoolId=USERPOOL_ID,
            ClientId=client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
            },
        )
        # Si on arrive ici, l'authentification a réussi
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", "")
        if error_code == "NotAuthorizedException":
            # Mot de passe incorrect OU utilisateur fédéré sans mot de passe
            if "federated" in error_message.lower() or "external" in error_message.lower():
                logger.debug("Utilisateur fédéré détecté pour %s", username)
                raise FederatedUserError("Utilisateur fédéré sans mot de passe")
            # Sinon, c'est probablement un mauvais mot de passe
            return False
        elif error_code == "InvalidParameterException":
            # Flow d'authentification non activé OU utilisateur fédéré
            if "password" in error_message.lower() and ("not set" in error_message.lower() or "not found" in error_message.lower()):
                logger.debug("Utilisateur fédéré détecté pour %s", username)
                raise FederatedUserError("Utilisateur fédéré sans mot de passe")
            # Flow d'authentification non activé
            logger.error("Flow d'authentification non activé: %s", error_message)
            raise ValueError(f"Configuration Cognito invalide: {error_message}")
        # Autre erreur
        logger.error("Erreur Cognito lors de la vérification du mot de passe: %s", error_code)
        raise


def revoke_all_user_tokens(username: str) -> None:
    """Révoque tous les refresh tokens d'un utilisateur Cognito.

    Cela force la déconnexion de tous les appareils où l'utilisateur est connecté.
    Les tokens d'accès et refresh existants deviendront invalides.

    Args:
        username (str): Nom d'utilisateur (sub ou email).

    Raises:
        ValueError: Si COGNITO_USER_POOL_ID n'est pas défini.
        UserNotFoundError: Si l'utilisateur n'existe pas dans Cognito.
        ClientError: Pour les autres erreurs Cognito.
    """
    if not USERPOOL_ID:
        raise ValueError("COGNITO_USER_POOL_ID doit être défini")

    try:
        client = get_cognito_client()
        client.admin_user_global_sign_out(UserPoolId=USERPOOL_ID, Username=username)
        logger.info("Tous les tokens révoqués pour l'utilisateur: username=%s", username)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", "")

        if error_code == "UserNotFoundException":
            logger.warning("Utilisateur non trouvé dans Cognito: username=%s", username)
            raise UserNotFoundError(f"Utilisateur {username} non trouvé dans Cognito") from e

        logger.error("Erreur Cognito lors de la révocation des tokens: %s - %s", error_code, error_message)
        raise
