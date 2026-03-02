"""Service de sauvegarde des scans dans l'historique (appel au user-service via gateway).

Appelé par le scan_stream à la fin d'un scan réussi, si un token Authorization
est présent. En cas d'échec, lève une exception pour que le stream émette save_failed.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
SAVE_TIMEOUT = 15.0


async def save_scan_to_history(
    payload: dict[str, Any],
    authorization: str,
) -> None:
    """Enregistre le résultat du scan dans l'historique via le gateway.

    Args:
        payload: Payload du résultat (url, timestamp, duration, score, findings).
        authorization: Header Authorization (Bearer <token>).

    Raises:
        Exception: Si la sauvegarde échoue (pour émettre save_failed).
    """
    url = f"{GATEWAY_URL.rstrip('/')}/user/api/scans/history"
    body = {
        "url": payload["url"],
        "status": "success",
        "score": payload["score"],
        "findings": payload["findings"],
        "timestamp": payload["timestamp"],
        "duration": payload["duration"],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization,
    }
    async with httpx.AsyncClient(timeout=SAVE_TIMEOUT) as client:
        resp = await client.post(url, json=body, headers=headers)
        if resp.status_code >= 400:
            msg = resp.text or f"HTTP {resp.status_code}"
            logger.warning("Sauvegarde scan échouée: %s", msg)
            raise RuntimeError(msg)
        logger.info("Scan sauvegardé dans l'historique: url=%s", payload["url"][:50])
