"""Scheduler des scans planifiés : réveille et exécute les scans dus."""

import asyncio
import os
from datetime import UTC, datetime

import httpx
from common.logging_config import get_logger

from app.db import get_async_session
from app.services.scan_repository import create_scan
from app.services.scheduled_scan_repository import get_scans_due_for_execution, update_next_run_at
from app.services.scheduled_scan_utils import compute_next_run
from app.services.subscription_repository import get_subscription_by_user_id
from app.utils.url_utils import URLValidationError, normalize_scan_url

logger = get_logger(__name__)

SCAN_SERVICE_URL = os.getenv("SCAN_SERVICE_URL", "http://localhost:8012")
SCAN_SERVICE_INTERNAL_API_KEY = os.getenv("SCAN_SERVICE_INTERNAL_API_KEY")  # Optionnel, pour sécuriser l'endpoint interne
SCHEDULER_INTERVAL = int(os.getenv("SCHEDULED_SCAN_INTERVAL_SECONDS", "300"))  # 5 minutes par défaut
SCHEDULER_INITIAL_DELAY = int(os.getenv("SCHEDULED_SCAN_INITIAL_DELAY_SECONDS", "60"))  # Délai au démarrage
SCAN_TIMEOUT = 120.0  # Timeout pour un scan (peut être long)


def _build_internal_headers() -> dict:
    """Construit les headers pour l'appel au scan-service (clé API si définie).

    Returns:
        dict: Headers à envoyer (X-Internal-Api-Key si configuré).
    """
    headers = {}
    if SCAN_SERVICE_INTERNAL_API_KEY:
        headers["X-Internal-Api-Key"] = SCAN_SERVICE_INTERNAL_API_KEY
    return headers


async def _call_scan_service(url: str) -> dict:
    """Appelle le scan-service et retourne la réponse JSON.

    Args:
        url: URL à scanner.

    Returns:
        dict: Réponse JSON du scan-service (ou dict vide si non-JSON).
    """
    headers = _build_internal_headers()
    async with httpx.AsyncClient(timeout=SCAN_TIMEOUT) as client:
        resp = await client.post(
            f"{SCAN_SERVICE_URL.rstrip('/')}/api/internal/scan/run",
            json={"url": url},
            headers=headers,
        )
    if resp.headers.get("content-type", "").startswith("application/json"):
        return resp.json()
    return {}


async def _persist_result_and_schedule_next(scan, data: dict, now: datetime) -> None:
    """Sauvegarde le scan dans l'historique (si retention != none) et met à jour next_run_at.

    Args:
        scan: Entité ScheduledScan.
        data: Réponse du scan-service (url, score, findings, etc.).
        now: Date/heure courante pour compute_next_run.
    """
    async with get_async_session() as session:
        subscription = await get_subscription_by_user_id(session, scan.user_id)
        retention = (subscription.history_retention if subscription else None) or "30"
        if retention != "none":
            await create_scan(
                session=session,
                user_id=scan.user_id,
                url=data["url"],
                status=data.get("status", "success"),
                score=data.get("score"),
                findings=data.get("findings", []),
                timestamp=data.get("timestamp", now.isoformat()),
                duration=data.get("duration", 0.0),
            )

    next_run = compute_next_run(
        from_dt=now,
        frequency=scan.frequency,
        schedule_hour=scan.schedule_hour,
        schedule_minute=scan.schedule_minute,
        schedule_day_of_week=scan.schedule_day_of_week,
        schedule_day_of_month=scan.schedule_day_of_month,
        timezone_name=getattr(scan, "timezone", None),
    )
    async with get_async_session() as session:
        await update_next_run_at(session, scan.id, next_run)


async def run_due_scheduled_scans() -> tuple[int, int]:
    """Exécute les scans planifiés dus et met à jour next_run_at en cas de succès.

    En cas d'échec du scan (site down, timeout), next_run_at n'est PAS mis à jour
    pour permettre un retry au prochain passage du scheduler.

    Returns:
        tuple[int, int]: (nombre de scans dus, nombre exécutés avec succès).
    """
    now = datetime.now(UTC)
    success_count = 0

    async with get_async_session() as session:
        due_scans = await get_scans_due_for_execution(session, before=now)

    logger.info("Scheduler: %d scan(s) planifié(s) dus", len(due_scans))

    for scan in due_scans:
        try:
            try:
                url_to_scan = normalize_scan_url(scan.url)
            except URLValidationError as e:
                logger.warning(
                    "Scan planifié ignoré (URL invalide): id=%s url=%s message=%s",
                    scan.id,
                    scan.url[:50] if scan.url else "",
                    e,
                )
                continue

            data = await _call_scan_service(url_to_scan)

            if data.get("status") == "error":
                logger.warning(
                    "Scan planifié échoué (retry au prochain passage): id=%s url=%s message=%s",
                    scan.id,
                    scan.url[:50],
                    data.get("message", "unknown"),
                )
                continue

            if "score" in data and "findings" in data:
                await _persist_result_and_schedule_next(scan, data, now)
                success_count += 1
                logger.info("Scan planifié exécuté: id=%s url=%s score=%s", scan.id, scan.url[:50], data.get("score"))
            else:
                logger.warning("Réponse scan-service invalide (pas de score): id=%s", scan.id)

        except httpx.TimeoutException as e:
            logger.warning("Timeout lors du scan planifié (retry): id=%s url=%s %s", scan.id, scan.url[:50], e)
        except Exception as e:
            logger.exception("Erreur lors de l'exécution du scan planifié: id=%s %s", scan.id, e)

    return len(due_scans), success_count


async def scheduled_scan_loop() -> None:
    """Boucle de fond : exécute les scans dus toutes les SCHEDULER_INTERVAL secondes."""
    logger.info("Scheduler: tâche démarrée, attente de %s s avant premier cycle", SCHEDULER_INITIAL_DELAY)
    await asyncio.sleep(SCHEDULER_INITIAL_DELAY)

    while True:
        try:
            due_count, success_count = await run_due_scheduled_scans()
            if success_count > 0:
                logger.info("Scheduler: %d scan(s) planifié(s) exécuté(s) avec succès", success_count)
        except Exception as exc:
            logger.error("Erreur dans le scheduler des scans planifiés: %s", exc, exc_info=True)
        await asyncio.sleep(SCHEDULER_INTERVAL)
