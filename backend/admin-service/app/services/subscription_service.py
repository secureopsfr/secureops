"""Service de gestion des abonnements pour l'admin.

Ce module fournit des opérations de consultation et de gestion
des abonnements utilisateur depuis le panel d'administration.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func

from app.db_sync import get_sync_session
from app.models.user import Subscription, User

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service de gestion des abonnements (méthodes admin uniquement)."""

    VALID_PLANS = ["free", "premium"]
    VALID_STATUSES = ["active", "canceled", "trial", "suspended"]

    def get_subscriptions(
        self,
        plan_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        has_stripe: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Récupère la liste des abonnements avec filtres.

        Args:
            plan_filter: Filtrer par plan (free, premium)
            status_filter: Filtrer par statut (active, canceled, trial, suspended)
            search: Recherche par email
            has_stripe: Filtrer par présence d'un Stripe customer ID
            limit: Nombre maximum de résultats
            offset: Décalage pour la pagination

        Returns:
            Dictionnaire contenant les abonnements et le total
        """
        with get_sync_session() as db:
            try:
                query = db.query(Subscription, User).join(User, User.id == Subscription.user_id)

                if plan_filter:
                    query = query.filter(Subscription.plan == plan_filter)

                if status_filter:
                    query = query.filter(Subscription.status == status_filter)

                if search:
                    search_term = f"%{search.lower()}%"
                    query = query.filter(User.email.ilike(search_term))

                if has_stripe is True:
                    query = query.filter(Subscription.stripe_customer_id.isnot(None))
                elif has_stripe is False:
                    query = query.filter(Subscription.stripe_customer_id.is_(None))

                total = query.count()

                rows = query.order_by(Subscription.updated_at.desc()).offset(offset).limit(limit).all()

                subscriptions = []
                for sub, user in rows:
                    subscriptions.append(self._serialize_subscription(sub, user))

                from app.schemas.common import make_pagination_meta

                return {"subscriptions": subscriptions, **make_pagination_meta(total=total, limit=limit, offset=offset)}
            except Exception as e:
                logger.error("Erreur lors de la récupération des abonnements: %s", e)
                raise

    def get_subscription_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques agrégées des abonnements.

        Returns:
            Statistiques KPI pour le dashboard abonnements
        """
        with get_sync_session() as db:
            try:
                total_subscriptions = db.query(Subscription).count()

                # Répartition par plan
                plan_counts = db.query(Subscription.plan, func.count(Subscription.id)).group_by(Subscription.plan).all()
                plans = dict(plan_counts)

                # Répartition par statut
                status_counts = db.query(Subscription.status, func.count(Subscription.id)).group_by(Subscription.status).all()
                statuses = dict(status_counts)

                # Abonnements premium = MRR proxy
                premium_count = plans.get("premium", 0)

                # Abonnements avec Stripe
                stripe_count = db.query(Subscription).filter(Subscription.stripe_customer_id.isnot(None)).count()

                # Abonnements récents (7 derniers jours)
                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                recent_subs = db.query(Subscription).filter(Subscription.created_at >= seven_days_ago).count()

                # Abonnements expirant dans les 30 prochains jours
                thirty_days = datetime.now(timezone.utc) + timedelta(days=30)
                expiring_soon = (
                    db.query(Subscription)
                    .filter(
                        Subscription.current_period_end.isnot(None),
                        Subscription.current_period_end <= thirty_days,
                        Subscription.current_period_end >= datetime.now(timezone.utc),
                        Subscription.status == "active",
                    )
                    .count()
                )

                # Taux de conversion (free → premium)
                total_with_plan = sum(plans.values()) if plans else 0
                conversion_rate = (premium_count / total_with_plan * 100) if total_with_plan > 0 else 0

                # Churn : annulés / total
                canceled_count = statuses.get("canceled", 0)
                churn_rate = (canceled_count / total_subscriptions * 100) if total_subscriptions > 0 else 0

                # Historique mensuel des changements (12 derniers mois)
                twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)
                monthly_data = (
                    db.query(
                        func.date_trunc("month", Subscription.created_at).label("month"),
                        Subscription.plan,
                        func.count(Subscription.id),
                    )
                    .filter(Subscription.created_at >= twelve_months_ago)
                    .group_by("month", Subscription.plan)
                    .order_by("month")
                    .all()
                )

                # Organiser l'historique mensuel
                monthly_history: Dict[str, Dict[str, int]] = {}
                for row_month, plan, count in monthly_data:
                    month_str = row_month.strftime("%Y-%m") if row_month else "unknown"
                    if month_str not in monthly_history:
                        monthly_history[month_str] = {"free": 0, "premium": 0}
                    monthly_history[month_str][plan] = count

                # Convertir en liste triée
                history_list = [{"month": month, **counts} for month, counts in sorted(monthly_history.items())]

                return {
                    "total_subscriptions": total_subscriptions,
                    "plans": plans,
                    "statuses": statuses,
                    "premium_count": premium_count,
                    "stripe_count": stripe_count,
                    "recent_subscriptions_7d": recent_subs,
                    "expiring_soon_30d": expiring_soon,
                    "conversion_rate": round(conversion_rate, 1),
                    "churn_rate": round(churn_rate, 1),
                    "monthly_history": history_list,
                }
            except Exception as e:
                logger.error("Erreur lors de la récupération des stats abonnements: %s", e)
                raise

    def update_subscription(self, subscription_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        """
        Met à jour un abonnement (plan, statut, etc.).

        Args:
            subscription_id: UUID de l'abonnement
            updates: Champs à mettre à jour

        Returns:
            Abonnement mis à jour

        Raises:
            ValueError: Si l'abonnement n'existe pas ou les valeurs sont invalides
        """
        with get_sync_session() as db:
            try:
                sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
                if not sub:
                    raise ValueError(f"Abonnement avec l'ID {subscription_id} non trouvé")

                user = db.query(User).filter(User.id == sub.user_id).first()

                # Valider et appliquer les changements
                if "plan" in updates:
                    new_plan = updates["plan"]
                    if new_plan not in self.VALID_PLANS:
                        raise ValueError(f"Plan invalide: {new_plan}. Plans valides: {', '.join(self.VALID_PLANS)}")
                    old_plan = sub.plan
                    sub.plan = new_plan
                    logger.info("Plan de l'abonnement %s changé: %s → %s", subscription_id, old_plan, new_plan)

                if "status" in updates:
                    new_status = updates["status"]
                    if new_status not in self.VALID_STATUSES:
                        raise ValueError(f"Statut invalide: {new_status}. Statuts valides: {', '.join(self.VALID_STATUSES)}")
                    old_status = sub.status
                    sub.status = new_status
                    logger.info("Statut de l'abonnement %s changé: %s → %s", subscription_id, old_status, new_status)

                if "current_period_end" in updates:
                    value = updates["current_period_end"]
                    if value is None:
                        sub.current_period_end = None
                    else:
                        try:
                            sub.current_period_end = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        except (ValueError, AttributeError) as e:
                            raise ValueError(f"Date de fin de période invalide: {value}") from e

                sub.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(sub)

                return self._serialize_subscription(sub, user)

            except ValueError:
                raise
            except Exception as e:
                db.rollback()
                logger.error("Erreur lors de la mise à jour de l'abonnement: %s", e)
                raise

    def get_plan_history(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Récupère l'historique des abonnements triés par date de mise à jour.

        Args:
            limit: Nombre maximum de résultats
            offset: Décalage pour la pagination

        Returns:
            Liste des derniers changements d'abonnement
        """
        with get_sync_session() as db:
            try:
                query = (
                    db.query(Subscription, User)
                    .join(User, User.id == Subscription.user_id)
                    .filter(Subscription.updated_at.isnot(None))
                    .order_by(Subscription.updated_at.desc())
                )

                total = query.count()
                rows = query.offset(offset).limit(limit).all()

                history = []
                for sub, user in rows:
                    history.append(
                        {
                            **self._serialize_subscription(sub, user),
                            "type": "update",
                        }
                    )

                from app.schemas.common import make_pagination_meta

                return {"history": history, **make_pagination_meta(total=total, limit=limit, offset=offset)}
            except Exception as e:
                logger.error("Erreur lors de la récupération de l'historique: %s", e)
                raise

    @staticmethod
    def _serialize_subscription(sub: Subscription, user: Optional[User] = None) -> Dict[str, Any]:
        """Sérialise un abonnement en dictionnaire."""
        return {
            "id": str(sub.id),
            "user_id": str(sub.user_id),
            "email": user.email if user else None,
            "plan": sub.plan,
            "status": sub.status,
            "stripe_customer_id": sub.stripe_customer_id,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "newsletter_enabled": sub.newsletter_enabled,
            "notifications_enabled": sub.new_features_notifications_enabled,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
            "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
        }
