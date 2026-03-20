"""Client HTTP pour la vérification du quota journalier via le user-service."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import httpx

from ..config_loader import get_services_config

logger = logging.getLogger(__name__)

QUOTA_TIMEOUT = 3.0
DAILY_QUOTA_LIMIT: int = int(os.getenv("DAILY_QUOTA_LIMIT", "50"))


@lru_cache
def _get_user_service_url() -> str | None:
    """Retourne l'URL du user-service depuis la config gateway."""
    services = get_services_config()
    user_svc = next((s for s in services if s["prefix"] == "user"), None)
    if not user_svc:
        return None
    return str(user_svc["url"])


def _next_midnight_utc_iso() -> str:
    d = datetime.now(UTC).date()
    return (datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(days=1)).isoformat()


async def check_and_increment_quota(
    cognito_sub: str,
    *,
    limit: int = DAILY_QUOTA_LIMIT,
) -> tuple[bool, int, str]:
    """Appelle user-service pour vérifier et incrémenter le quota journalier.

    En cas d'indisponibilité du service (timeout, erreur réseau), la requête
    est autorisée par défaut (fail-open) pour ne pas bloquer les utilisateurs
    lors d'une panne du user-service.

    Returns:
        (allowed, remaining, reset_at_iso)
    """
    user_service_url = _get_user_service_url()
    if not user_service_url:
        logger.warning("User-service non configuré — quota non vérifié, passage autorisé")
        return True, limit, _next_midnight_utc_iso()

    url = f"{user_service_url.rstrip('/')}/api/internal/quota/check-and-increment"
    internal_key = os.getenv("USER_SERVICE_INTERNAL_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if internal_key:
        headers["X-Internal-Api-Key"] = internal_key

    try:
        async with httpx.AsyncClient(timeout=QUOTA_TIMEOUT) as client:
            resp = await client.post(
                url,
                json={"cognito_sub": cognito_sub, "limit": limit},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["allowed"], data["remaining"], data.get("reset_at", _next_midnight_utc_iso())
            detail = (resp.text or "")[:200]
            logger.warning(
                "Quota check: user-service HTTP %s — quota non incrémenté (fail-open). "
                "Aligner USER_SERVICE_INTERNAL_API_KEY sur gateway et user-service. Réponse: %s",
                resp.status_code,
                detail,
            )
            return True, limit, _next_midnight_utc_iso()
    except httpx.TimeoutException:
        logger.warning("Quota check timeout — passage autorisé (fail-open)")
        return True, limit, _next_midnight_utc_iso()
    except Exception as exc:
        logger.warning("Quota check erreur: %s — passage autorisé (fail-open)", exc)
        return True, limit, _next_midnight_utc_iso()
