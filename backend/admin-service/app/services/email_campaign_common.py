"""Utilitaires communs pour les campagnes email (newsletter/notification)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from app.email_config import send_newsletter_email
from app.models.user import Subscription, User


def create_campaign_email(db, model_cls, email_data, success_message: str) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Crée un email de campagne (draft)."""
    campaign_email = model_cls(
        subject=email_data.subject,
        content=email_data.content,
        status="draft",
        template_name=getattr(email_data, "template_name", None) or "newsletter.html",
    )
    db.add(campaign_email)
    db.commit()
    db.refresh(campaign_email)
    return {"id": campaign_email.id, "subject": campaign_email.subject, "message": success_message}


def list_campaign_emails(db, model_cls, limit: int, offset: int) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Liste les emails de campagne avec pagination."""
    from app.schemas.common import make_pagination_meta

    query = db.query(model_cls)
    total = query.count()
    emails = query.order_by(model_cls.sent_at.desc()).offset(offset).limit(limit).all()

    data = [
        {
            "id": email.id,
            "subject": email.subject,
            "content": email.content,
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "recipients_count": email.recipients_count,
            "status": email.status,
            "scheduled_at": email.scheduled_at.isoformat() if email.scheduled_at else None,
            "is_scheduled": email.is_scheduled,
            "template_name": email.template_name or "newsletter.html",
        }
        for email in emails
    ]
    return {"data": data, **make_pagination_meta(total=total, limit=limit, offset=offset)}


async def send_campaign_email(  # type: ignore[no-untyped-def]
    db,
    model_cls,
    email_id: int,
    subscription_flag: str,
    no_subscribers_message: str,
    logger,
) -> dict[str, Any]:
    """Envoie une campagne email à des abonnés filtrés par flag subscription."""
    email = db.query(model_cls).filter(model_cls.id == email_id).first()
    if not email:
        raise ValueError(f"Email avec l'ID {email_id} non trouvé")

    flag_column = getattr(Subscription, subscription_flag)
    subscribers = (
        db.query(User).join(Subscription, User.id == Subscription.user_id).filter(flag_column.is_(True)).filter(User.email.isnot(None)).all()
    )

    if not subscribers:
        return {"message": no_subscribers_message, "recipients_count": 0}

    sent_count = 0
    failed_count = 0
    template = email.template_name or "newsletter.html"

    for user in subscribers:
        try:
            unsubscribe_token = secrets.token_urlsafe(32)
            await send_newsletter_email(
                to_email=user.email,
                subject=email.subject,
                content=email.content,
                unsubscribe_token=unsubscribe_token,
                template_name=template,
            )
            sent_count += 1
        except Exception as exc:  # pragma: no cover - dépend des providers email
            logger.warning("Erreur lors de l'envoi email campagne à %s: %s", user.email, exc)
            failed_count += 1

    if sent_count > 0:
        email.status = "sent"
        email.recipients_count = sent_count
        email.sent_at = datetime.now(timezone.utc)
    else:
        email.status = "failed"
        email.recipients_count = 0
    db.commit()

    return {"message": f"Email envoyé à {sent_count} abonnés, {failed_count} échecs", "recipients_count": sent_count}


def schedule_campaign_email(db, model_cls, email_id: int, scheduled_at: str) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Programme l'envoi d'un email de campagne."""
    email = db.query(model_cls).filter(model_cls.id == email_id).first()
    if not email:
        raise ValueError(f"Email avec l'ID {email_id} non trouvé")
    if email.status == "sent":
        raise ValueError("Cet email a déjà été envoyé")

    scheduled_datetime = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
    if scheduled_datetime <= datetime.now(timezone.utc):
        raise ValueError("La date d'envoi doit être dans le futur")

    email.scheduled_at = scheduled_datetime
    email.is_scheduled = True
    email.status = "scheduled"
    db.commit()

    return {
        "message": f"Email programmé pour le {scheduled_datetime.strftime('%d/%m/%Y à %H:%M')}",
        "email_id": email_id,
        "scheduled_at": scheduled_at,
        "is_scheduled": True,
    }


def update_campaign_email(db, model_cls, email_id: int, email_data, success_message: str) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Met à jour un email de campagne."""
    email = db.query(model_cls).filter(model_cls.id == email_id).first()
    if not email:
        raise ValueError(f"Email avec l'ID {email_id} non trouvé")
    if email.status == "sent":
        raise ValueError("Impossible de modifier un email déjà envoyé")

    email.subject = email_data.subject
    email.content = email_data.content
    if hasattr(email_data, "template_name") and email_data.template_name is not None:
        email.template_name = email_data.template_name

    db.commit()
    db.refresh(email)
    return {"id": email.id, "subject": email.subject, "message": success_message}
