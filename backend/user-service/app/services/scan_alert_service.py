"""Service d'alertes pour les scans planifiés (régression score, finding critical).

Appelle l'admin-service pour l'envoi des emails et persiste l'historique.
"""

import os
import uuid
from typing import Any

import httpx
from common.logging_config import get_logger

from app.db import get_async_session
from app.services.scan_alert_repository import create_scan_alert_event

logger = get_logger(__name__)

ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL", "http://localhost:8010")
ADMIN_SERVICE_INTERNAL_API_KEY = os.getenv("ADMIN_SERVICE_INTERNAL_API_KEY")
SCAN_ALERT_REGRESSION_THRESHOLD = int(os.getenv("SCAN_ALERT_REGRESSION_THRESHOLD", "10"))
REQUEST_TIMEOUT = 10.0


def _has_critical_finding(findings: list[dict[str, Any]]) -> bool:
    """Vérifie si au moins un finding a la sévérité critical."""
    return any(str(f.get("severity", "")).lower() == "critical" for f in findings or [])


def _build_headers() -> dict:
    """Construit les headers pour l'appel admin-service."""
    headers = {}
    if ADMIN_SERVICE_INTERNAL_API_KEY:
        headers["X-Internal-Api-Key"] = ADMIN_SERVICE_INTERNAL_API_KEY
    return headers


def _build_regression_alert(data: dict, last_scan, url: str, threshold: int | None = None) -> dict | None:
    """Construit l'alerte de régression si le score a chuté au-delà du seuil.

    Args:
        threshold: Seuil personnalisé (pts). None = valeur par défaut serveur.
    """
    score_actuel = data.get("score")
    if score_actuel is None or not last_scan or last_scan.score is None:
        return None
    effective_threshold = threshold if threshold is not None else SCAN_ALERT_REGRESSION_THRESHOLD
    delta = last_scan.score - score_actuel
    if delta < effective_threshold:
        return None
    return {
        "subject": f"[SecureOps] Régression score sur {url[:50]}...",
        "message": f"Le score de sécurité est passé de {last_scan.score} à {score_actuel} (-{delta} points).",
        "severity": "critical" if delta >= 20 else "warning",
        "alert_type": "regression",
    }


def _build_critical_finding_alert(data: dict, url: str) -> dict | None:
    """Construit l'alerte finding critical si au moins un finding est critique."""
    findings = data.get("findings", [])
    if not _has_critical_finding(findings):
        return None
    critical_titles = [f.get("title", "Finding critique") for f in findings if str(f.get("severity", "")).lower() == "critical"]
    msg = "Finding(s) critique(s) détecté(s) : " + " ; ".join(critical_titles[:3])
    if len(critical_titles) > 3:
        msg += f" (+{len(critical_titles) - 3} autre(s))"
    return {
        "subject": f"[SecureOps] Finding critique sur {url[:50]}...",
        "message": msg,
        "severity": "critical",
        "alert_type": "critical_finding",
    }


async def _send_alert(alert: dict, user_email: str, url: str) -> bool:
    """Envoie une alerte à l'admin-service.

    Returns:
        bool: True si l'email a été envoyé avec succès (status 200).
    """
    try:
        payload = {
            "to_email": user_email.strip(),
            "url": url,
            "subject": alert["subject"],
            "message": alert["message"],
            "severity": alert["severity"],
            "alert_type": alert["alert_type"],
        }
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{ADMIN_SERVICE_URL.rstrip('/')}/api/internal/notifications/scan-alert",
                json=payload,
                headers=_build_headers(),
            )
        if resp.status_code != 200:
            logger.warning("Alert scan non envoyée: admin-service %s %s", resp.status_code, resp.text[:200])
            return False
        return True
    except Exception as e:
        logger.warning("Erreur envoi alerte scan: %s", e)
        return False


async def check_and_send_scan_alerts(
    user_id: uuid.UUID,
    user_email: str,
    url: str,
    data: dict,
    last_scan,
    scan_alerts_enabled: bool,
    scan_type: str = "frontend",
    scan_mode: str = "passive",
    scheduled_scan_id: uuid.UUID | None = None,
    alert_on_regression: bool = True,
    alert_on_critical_finding: bool = True,
    alert_score_threshold: int | None = None,
) -> None:
    """Vérifie les conditions d'alerte, envoie les emails et persiste l'historique.

    Args:
        user_id: UUID de l'utilisateur.
        user_email: Email du destinataire.
        url: URL scannée (normalisée).
        data: Réponse du scan-service (score, findings, etc.).
        last_scan: Dernier scan pour cette URL (ou None).
        scan_alerts_enabled: Si l'utilisateur a activé les alertes.
        scheduled_scan_id: UUID du scan planifié (optionnel).
        alert_on_regression: Déclencher une alerte sur régression de score.
        alert_on_critical_finding: Déclencher une alerte sur finding critique.
        alert_score_threshold: Seuil de chute de score (pts). None = valeur serveur.
    """
    if not scan_alerts_enabled or not user_email or not user_email.strip():
        return

    if not ADMIN_SERVICE_URL:
        logger.warning("ADMIN_SERVICE_URL non configuré. Alertes scan ignorées.")
        return

    alerts_to_send: list[dict[str, str]] = []
    if alert_on_regression:
        if reg := _build_regression_alert(data, last_scan, url, threshold=alert_score_threshold):
            alerts_to_send.append(reg)
    if alert_on_critical_finding:
        if crit := _build_critical_finding_alert(data, url):
            alerts_to_send.append(crit)

    for alert in alerts_to_send:
        email_sent = await _send_alert(alert, user_email, url)
        async with get_async_session() as session:
            await create_scan_alert_event(
                session=session,
                user_id=user_id,
                url=url,
                scan_type=scan_type,
                scan_mode=scan_mode,
                alert_type=alert["alert_type"],
                email_sent=email_sent,
                scheduled_scan_id=scheduled_scan_id,
            )
