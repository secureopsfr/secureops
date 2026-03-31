"""Service de sauvegarde des scans dans l'historique (appel au user-service via gateway).

Appelé par le scan_stream à la fin d'un scan réussi, si un token Authorization
est présent. En cas d'échec, lève une exception pour que le stream émette save_failed.
"""

import logging
import os
from typing import Any

import httpx

from app.config_loader import get_external_services_settings

logger = logging.getLogger(__name__)

_EXTERNAL = get_external_services_settings()
GATEWAY_URL = os.getenv("GATEWAY_URL", _EXTERNAL.gateway_url)
SAVE_TIMEOUT = _EXTERNAL.save_timeout


async def save_multi_scan_to_history(
    payload: dict[str, Any],
    authorization: str,
) -> str | None:
    """Enregistre le résultat d'un scan multi-URL dans l'historique.

    Le payload est sauvegardé sous forme d'une seule entrée avec
    result_mode="multi". Les champs principaux (url=base_url, score=score_global)
    sont alignés sur le format attendu par user-service pour la liste d'historique.

    Args:
        payload: Résultat MultiScanResult.to_dict() (result_mode, base_url, page_results…).
        authorization: Header Authorization (Bearer <token>).

    Returns:
        str | None: ID du scan créé, ou None si la réponse n'en contient pas.

    Raises:
        Exception: Si la sauvegarde échoue.
    """
    url = f"{GATEWAY_URL.rstrip('/')}/user/api/scans/history"
    body = {
        "url": payload.get("base_url", ""),
        "scan_type": payload.get("scan_type", "frontend"),
        "scan_mode": payload.get("scan_mode", "passive"),
        "status": "success",
        "score": payload.get("score_global", 0),
        "findings": [],
        "timestamp": payload.get("timestamp", ""),
        "duration": payload.get("duration", 0.0),
        "result_mode": "multi",
        "page_results": payload.get("page_results", []),
        "urls": payload.get("urls", []),
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization,
    }
    async with httpx.AsyncClient(timeout=SAVE_TIMEOUT) as client:
        resp = await client.post(url, json=body, headers=headers)
        if resp.status_code >= 400:
            msg = resp.text or f"HTTP {resp.status_code}"
            logger.warning("Sauvegarde multi-scan échouée: %s", msg)
            raise RuntimeError(msg)
        logger.info(
            "Multi-scan sauvegardé dans l'historique: base_url=%s pages=%d",
            payload.get("base_url", "")[:50],
            len(payload.get("page_results", [])),
        )
        data = resp.json()
        return data.get("id") if isinstance(data, dict) else None


async def save_scan_to_history(
    payload: dict[str, Any],
    authorization: str,
) -> str | None:
    """Enregistre le résultat du scan dans l'historique via le gateway.

    Args:
        payload: Payload du résultat (url, timestamp, duration, score, findings).
        authorization: Header Authorization (Bearer <token>).

    Returns:
        str | None: ID du scan créé, ou None si la réponse n'en contient pas.

    Raises:
        Exception: Si la sauvegarde échoue (pour émettre save_failed).
    """
    url = f"{GATEWAY_URL.rstrip('/')}/user/api/scans/history"
    body: dict[str, Any] = {
        "url": payload["url"],
        "scan_type": payload.get("scan_type", "frontend"),
        "scan_mode": payload.get("scan_mode", "passive"),
        "status": "success",
        "score": payload["score"],
        "findings": payload["findings"],
        "timestamp": payload["timestamp"],
        "duration": payload["duration"],
    }
    if payload.get("result_mode") and payload["result_mode"] != "single":
        body["result_mode"] = payload["result_mode"]
    if "category_summaries" in payload and payload["category_summaries"]:
        body["category_summaries"] = payload["category_summaries"]
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
        data = resp.json()
        return data.get("id") if isinstance(data, dict) else None
