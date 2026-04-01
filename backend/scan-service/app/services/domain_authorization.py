"""Contrôle domaine vérifié (DNS) pour les scans non passifs via user-service."""

from __future__ import annotations

import logging
import os
from typing import Optional

import httpx
from common.url_helpers import registered_domain_from_url
from fastapi import HTTPException

logger = logging.getLogger(__name__)

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8011").rstrip("/")
USER_SERVICE_INTERNAL_API_KEY = os.getenv("USER_SERVICE_INTERNAL_API_KEY")
ASSERT_TIMEOUT_S = float(os.getenv("USER_SERVICE_ASSERT_TIMEOUT_S", "10"))


def authorization_check_enabled() -> bool:
    """Return True if authorization check is enabled."""
    return os.getenv("AUTHORIZATION_CHECK_ENABLED", "").lower() in ("1", "true", "yes")


async def ensure_domain_authorized_for_non_passive_scan(
    *,
    cognito_sub: Optional[str],
    normalized_url: str,
    scan_mode: str,
) -> None:
    """Lève HTTPException 403 si le mode non passif exige un domaine vérifié et que ce n'est pas le cas."""
    if scan_mode == "passive" or not authorization_check_enabled():
        return
    if not cognito_sub:
        raise HTTPException(
            status_code=403,
            detail={"code": "domain_verification_required", "message": "Authentification requise avec compte pour ce mode de scan."},
        )
    if not USER_SERVICE_INTERNAL_API_KEY:
        logger.error("AUTHORIZATION_CHECK_ENABLED sans USER_SERVICE_INTERNAL_API_KEY — refus du scan.")
        raise HTTPException(status_code=503, detail="domain_verification_unavailable")

    domain = registered_domain_from_url(normalized_url).lower()
    url = f"{USER_SERVICE_URL}/api/internal/domain-verifications/assert"
    headers = {"Content-Type": "application/json", "X-Internal-Api-Key": USER_SERVICE_INTERNAL_API_KEY}
    payload = {"cognito_sub": cognito_sub, "domain": domain}
    try:
        async with httpx.AsyncClient(timeout=ASSERT_TIMEOUT_S) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as e:
        logger.warning("assert domain: user-service unreachable: %s", e)
        raise HTTPException(status_code=503, detail="domain_verification_unavailable") from e

    if resp.status_code != 200:
        logger.debug("assert domain unexpected status %s: %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=503, detail="domain_verification_unavailable")

    data = resp.json()
    if data.get("allowed") is True:
        return
    reason = data.get("reason") or "domain_not_verified"
    raise HTTPException(
        status_code=403,
        detail={
            "code": reason if reason in ("domain_not_verified", "domain_owned_by_another_user") else "domain_not_verified",
            "message": "Domaine non vérifié ou non autorisé pour ce compte.",
            "domain": domain,
        },
    )
