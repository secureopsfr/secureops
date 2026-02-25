"""Service de gestion de la mailing list (méthodes admin uniquement)."""

from typing import Any, Dict

from app.db_sync import get_sync_session
from app.models.user import Subscription, User
from app.schemas.common import make_pagination_meta


class MailingListService:
    """Service de gestion de la mailing list (méthodes admin uniquement)."""

    def __init__(self):
        """Initialise le service."""
        pass

    def get_mailing_list(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Récupère la liste des abonnés à la newsletter avec pagination.

        Args:
            limit: Nombre d'entrées par page
            offset: Décalage pour la pagination

        Returns:
            Liste des utilisateurs abonnés à la newsletter
        """
        with get_sync_session() as db:
            try:
                # Récupérer les utilisateurs avec newsletter_enabled=True via la jointure avec subscriptions
                query = (
                    db.query(User)
                    .join(Subscription, User.id == Subscription.user_id)
                    .filter(Subscription.newsletter_enabled.is_(True))
                    .filter(User.email.isnot(None))
                    .order_by(User.created_at.desc())
                )

                entries = query.offset(offset).limit(limit).all()
                total = query.count()

                entries_data = []
                for user in entries:
                    entry_dict = {
                        "id": str(user.id),
                        "email": user.email,
                        "is_verified": True,  # Les utilisateurs sont toujours considérés comme vérifiés
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.subscription.updated_at.isoformat() if user.subscription and user.subscription.updated_at else None,
                    }
                    entries_data.append(entry_dict)

                return {"entries": entries_data, **make_pagination_meta(total=total, limit=limit, offset=offset)}
            except Exception as e:
                raise e

    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Active la newsletter pour un utilisateur (équivalent à vérifier l'email).

        Args:
            email: Adresse email de l'utilisateur

        Returns:
            Informations de la vérification

        Raises:
            ValueError: Si l'utilisateur n'existe pas
        """
        with get_sync_session() as db:
            try:
                user = db.query(User).filter(User.email == email).first()
                if not user:
                    raise ValueError(f"Utilisateur avec l'email '{email}' non trouvé")

                # Récupérer ou créer la subscription
                subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                if not subscription:
                    # Créer une subscription par défaut si elle n'existe pas
                    subscription = Subscription(user_id=user.id, newsletter_enabled=True)
                    db.add(subscription)
                else:
                    subscription.newsletter_enabled = True

                db.commit()

                return {"email": email, "message": "Newsletter activée avec succès", "is_verified": True}
            except Exception as e:
                db.rollback()
                raise e

    def unsubscribe_email(self, email: str) -> Dict[str, Any]:
        """
        Désactive la newsletter pour un utilisateur.

        Args:
            email: Adresse email de l'utilisateur

        Returns:
            Informations de la désinscription

        Raises:
            ValueError: Si l'utilisateur n'existe pas
        """
        with get_sync_session() as db:
            try:
                user = db.query(User).filter(User.email == email).first()
                if not user:
                    raise ValueError(f"Utilisateur avec l'email '{email}' non trouvé")

                subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                if subscription:
                    subscription.newsletter_enabled = False
                    db.commit()
                else:
                    # Si pas de subscription, créer une avec newsletter désactivée
                    subscription = Subscription(user_id=user.id, newsletter_enabled=False)
                    db.add(subscription)
                    db.commit()

                return {"email": email, "message": "Désinscription réussie. Vous ne recevrez plus nos actualités."}
            except Exception as e:
                db.rollback()
                raise e

    def get_notification_subscribers(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Récupère la liste des abonnés aux notifications avec pagination.

        Args:
            limit: Nombre d'entrées par page
            offset: Décalage pour la pagination

        Returns:
            Liste des utilisateurs abonnés aux notifications
        """
        with get_sync_session() as db:
            try:
                # Récupérer les utilisateurs avec new_features_notifications_enabled=True via la jointure avec subscriptions
                query = (
                    db.query(User)
                    .join(Subscription, User.id == Subscription.user_id)
                    .filter(Subscription.new_features_notifications_enabled.is_(True))
                    .filter(User.email.isnot(None))
                    .order_by(User.created_at.desc())
                )

                entries = query.offset(offset).limit(limit).all()
                total = query.count()

                entries_data = []
                for user in entries:
                    entry_dict = {
                        "id": str(user.id),
                        "email": user.email,
                        "is_verified": True,  # Les utilisateurs sont toujours considérés comme vérifiés
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.subscription.updated_at.isoformat() if user.subscription and user.subscription.updated_at else None,
                    }
                    entries_data.append(entry_dict)

                return {"entries": entries_data, **make_pagination_meta(total=total, limit=limit, offset=offset)}
            except Exception as e:
                raise e
