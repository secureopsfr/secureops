"""Service de gestion des utilisateurs pour l'admin.

Ce module fournit des opérations CRUD et de gestion Cognito
pour les utilisateurs depuis le panel d'administration.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError
from common.cognito import REGION, USERPOOL_ID
from common.logging_config import mask_email

from app.db_sync import get_sync_session
from app.models.user import Subscription, User

logger = logging.getLogger(__name__)


def _get_cognito_client():
    """Crée un client Cognito Identity Provider.

    Returns:
        boto3.client: Client Cognito configuré.
    """
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if aws_access_key_id and aws_secret_access_key:
        return boto3.client(
            "cognito-idp",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=REGION,
        )
    return boto3.client("cognito-idp", region_name=REGION)


class UserManagementService:
    """Service de gestion des utilisateurs (méthodes admin uniquement)."""

    VALID_GROUPS = ["admin", "beta", "user"]

    def __init__(self):
        """Initialise le service."""
        pass

    def get_users(
        self,
        search: Optional[str] = None,
        plan_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Récupère la liste des utilisateurs avec recherche et filtres.

        Args:
            search: Terme de recherche (email)
            plan_filter: Filtrer par plan (free, premium)
            status_filter: Filtrer par statut d'abonnement (active, canceled, trial, suspended)
            limit: Nombre maximum de résultats
            offset: Décalage pour la pagination

        Returns:
            Dictionnaire contenant les utilisateurs et le total
        """
        with get_sync_session() as db:
            try:
                query = db.query(User).outerjoin(Subscription, User.id == Subscription.user_id)

                # Recherche par email
                if search:
                    search_term = f"%{search.lower()}%"
                    query = query.filter(User.email.ilike(search_term))

                # Filtre par plan
                if plan_filter:
                    query = query.filter(Subscription.plan == plan_filter)

                # Filtre par statut
                if status_filter:
                    query = query.filter(Subscription.status == status_filter)

                # Total avant pagination
                total = query.count()

                # Pagination et tri
                users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

                users_data = []
                for user in users:
                    sub = user.subscription
                    user_dict = {
                        "id": str(user.id),
                        "cognito_sub": user.cognito_sub,
                        "email": user.email,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "subscription_id": str(sub.id) if sub else None,
                        "plan": sub.plan if sub else "free",
                        "status": sub.status if sub else "active",
                        "stripe_customer_id": sub.stripe_customer_id if sub else None,
                        "newsletter_enabled": sub.newsletter_enabled if sub else False,
                        "notifications_enabled": sub.new_features_notifications_enabled if sub else False,
                        "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
                        "updated_at": sub.updated_at.isoformat() if sub and sub.updated_at else None,
                    }
                    users_data.append(user_dict)

                from app.schemas.common import make_pagination_meta

                return {"users": users_data, **make_pagination_meta(total=total, limit=limit, offset=offset)}
            except Exception as e:
                logger.error("Erreur lors de la récupération des utilisateurs: %s", e)
                raise

    def get_user_detail(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère le détail d'un utilisateur (DB + groupes Cognito).

        Args:
            user_id: UUID de l'utilisateur

        Returns:
            Détail complet de l'utilisateur

        Raises:
            ValueError: Si l'utilisateur n'existe pas
        """
        with get_sync_session() as db:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError(f"Utilisateur avec l'ID {user_id} non trouvé")

                sub = user.subscription

                user_dict = {
                    "id": str(user.id),
                    "cognito_sub": user.cognito_sub,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "subscription_id": str(sub.id) if sub else None,
                    "plan": sub.plan if sub else "free",
                    "status": sub.status if sub else "active",
                    "stripe_customer_id": sub.stripe_customer_id if sub else None,
                    "newsletter_enabled": sub.newsletter_enabled if sub else False,
                    "notifications_enabled": sub.new_features_notifications_enabled if sub else False,
                    "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
                    "updated_at": sub.updated_at.isoformat() if sub and sub.updated_at else None,
                    "cognito_groups": [],
                    "cognito_status": None,
                }

                # Récupérer les groupes Cognito
                if USERPOOL_ID and user.cognito_sub:
                    try:
                        client = _get_cognito_client()
                        groups_response = client.admin_list_groups_for_user(
                            UserPoolId=USERPOOL_ID,
                            Username=user.cognito_sub,
                        )
                        user_dict["cognito_groups"] = [g["GroupName"] for g in groups_response.get("Groups", [])]

                        # Récupérer le statut Cognito
                        cognito_user = client.admin_get_user(
                            UserPoolId=USERPOOL_ID,
                            Username=user.cognito_sub,
                        )
                        user_dict["cognito_status"] = cognito_user.get("UserStatus")
                        user_dict["cognito_enabled"] = cognito_user.get("Enabled", True)
                    except ClientError as e:
                        error_code = e.response.get("Error", {}).get("Code", "")
                        if error_code == "UserNotFoundException":
                            logger.warning("Utilisateur Cognito non trouvé: %s", user.cognito_sub)
                            user_dict["cognito_groups"] = []
                            user_dict["cognito_status"] = "NOT_FOUND"
                            user_dict["cognito_enabled"] = False
                        else:
                            logger.error("Erreur Cognito: %s", e)
                            user_dict["cognito_groups"] = []
                            user_dict["cognito_status"] = "ERROR"

                return user_dict
            except ValueError:
                raise
            except Exception as e:
                logger.error("Erreur lors de la récupération du détail utilisateur: %s", e)
                raise

    def update_user_group(self, user_id: str, group: str) -> Dict[str, Any]:  # noqa: C901
        """
        Change le groupe Cognito d'un utilisateur.

        Args:
            user_id: UUID de l'utilisateur
            group: Nouveau groupe (admin, beta, user)

        Returns:
            Résultat de l'opération

        Raises:
            ValueError: Si le groupe est invalide ou l'utilisateur n'existe pas
        """
        if group not in self.VALID_GROUPS:
            raise ValueError(f"Groupe invalide: {group}. Groupes valides: {', '.join(self.VALID_GROUPS)}")

        if not USERPOOL_ID:
            raise ValueError("COGNITO_USER_POOL_ID doit être défini")

        with get_sync_session() as db:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError(f"Utilisateur avec l'ID {user_id} non trouvé")

                client = _get_cognito_client()

                # Récupérer les groupes actuels
                groups_response = client.admin_list_groups_for_user(
                    UserPoolId=USERPOOL_ID,
                    Username=user.cognito_sub,
                )
                current_groups = [g["GroupName"] for g in groups_response.get("Groups", [])]

                # Retirer des anciens groupes (seulement ceux dans VALID_GROUPS)
                for old_group in current_groups:
                    if old_group in self.VALID_GROUPS and old_group != group:
                        try:
                            client.admin_remove_user_from_group(
                                UserPoolId=USERPOOL_ID,
                                Username=user.cognito_sub,
                                GroupName=old_group,
                            )
                            logger.info("Utilisateur %s retiré du groupe %s", mask_email(user.email), old_group)
                        except ClientError as e:
                            logger.warning("Impossible de retirer du groupe %s: %s", old_group, e)

                # Ajouter au nouveau groupe (le groupe "user" est implicite, on ne l'ajoute pas dans Cognito)
                if group != "user":
                    try:
                        client.admin_add_user_to_group(
                            UserPoolId=USERPOOL_ID,
                            Username=user.cognito_sub,
                            GroupName=group,
                        )
                        logger.info("Utilisateur %s ajouté au groupe %s", mask_email(user.email), group)
                    except ClientError as e:
                        error_code = e.response.get("Error", {}).get("Code", "")
                        if error_code == "ResourceNotFoundException":
                            # Le groupe n'existe pas dans Cognito, on le crée
                            try:
                                client.create_group(
                                    GroupName=group,
                                    UserPoolId=USERPOOL_ID,
                                    Description=f"Groupe {group}",
                                )
                                client.admin_add_user_to_group(
                                    UserPoolId=USERPOOL_ID,
                                    Username=user.cognito_sub,
                                    GroupName=group,
                                )
                                logger.info("Groupe %s créé et utilisateur ajouté", group)
                            except ClientError as create_err:
                                logger.error("Impossible de créer le groupe %s: %s", group, create_err)
                                raise ValueError(f"Impossible de créer le groupe {group}") from create_err
                        else:
                            raise

                return {
                    "success": True,
                    "message": f"Utilisateur {user.email} assigné au groupe {group}",
                    "user_id": str(user.id),
                    "group": group,
                }
            except ValueError:
                raise
            except Exception as e:
                logger.error("Erreur lors du changement de groupe: %s", e)
                raise

    def toggle_user_status(self, user_id: str, action: str) -> Dict[str, Any]:  # noqa: C901
        """
        Active ou désactive un utilisateur (ban/suspend).

        Args:
            user_id: UUID de l'utilisateur
            action: Action à effectuer (disable, enable)

        Returns:
            Résultat de l'opération

        Raises:
            ValueError: Si l'action est invalide ou l'utilisateur n'existe pas
        """
        if action not in ("disable", "enable"):
            raise ValueError(f"Action invalide: {action}. Actions valides: disable, enable")

        if not USERPOOL_ID:
            raise ValueError("COGNITO_USER_POOL_ID doit être défini")

        with get_sync_session() as db:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError(f"Utilisateur avec l'ID {user_id} non trouvé")

                client = _get_cognito_client()

                if action == "disable":
                    client.admin_disable_user(
                        UserPoolId=USERPOOL_ID,
                        Username=user.cognito_sub,
                    )
                    # Mettre à jour le statut en base
                    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                    if sub:
                        sub.status = "suspended"
                        sub.updated_at = datetime.now(timezone.utc)
                        db.commit()

                    logger.info("Utilisateur %s désactivé (suspendu)", mask_email(user.email))
                    return {
                        "success": True,
                        "message": f"Utilisateur {user.email} suspendu avec succès",
                        "user_id": str(user.id),
                        "action": "disabled",
                    }
                else:
                    client.admin_enable_user(
                        UserPoolId=USERPOOL_ID,
                        Username=user.cognito_sub,
                    )
                    # Remettre le statut en active
                    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                    if sub and sub.status == "suspended":
                        sub.status = "active"
                        sub.updated_at = datetime.now(timezone.utc)
                        db.commit()

                    logger.info("Utilisateur %s réactivé", mask_email(user.email))
                    return {
                        "success": True,
                        "message": f"Utilisateur {user.email} réactivé avec succès",
                        "user_id": str(user.id),
                        "action": "enabled",
                    }
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "UserNotFoundException":
                    raise ValueError(f"Utilisateur Cognito non trouvé pour {user_id}") from e
                logger.error("Erreur Cognito lors du changement de statut: %s", e)
                raise
            except ValueError:
                raise
            except Exception as e:
                db.rollback()
                logger.error("Erreur lors du changement de statut utilisateur: %s", e)
                raise

    def get_users_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques globales des utilisateurs.

        Returns:
            Statistiques agrégées des utilisateurs
        """
        with get_sync_session() as db:
            try:
                total_users = db.query(User).count()

                from sqlalchemy import func

                plan_counts = db.query(Subscription.plan, func.count(Subscription.id)).group_by(Subscription.plan).all()

                status_counts = db.query(Subscription.status, func.count(Subscription.id)).group_by(Subscription.status).all()

                # Utilisateurs récents (7 derniers jours)
                from datetime import timedelta

                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                recent_users = db.query(User).filter(User.created_at >= seven_days_ago).count()

                # Newsletter et notifications
                newsletter_count = db.query(Subscription).filter(Subscription.newsletter_enabled.is_(True)).count()
                notifications_count = db.query(Subscription).filter(Subscription.new_features_notifications_enabled.is_(True)).count()

                return {
                    "total_users": total_users,
                    "recent_users_7d": recent_users,
                    "plans": dict(plan_counts),
                    "statuses": dict(status_counts),
                    "newsletter_subscribers": newsletter_count,
                    "notification_subscribers": notifications_count,
                }
            except Exception as e:
                logger.error("Erreur lors de la récupération des stats utilisateurs: %s", e)
                raise
