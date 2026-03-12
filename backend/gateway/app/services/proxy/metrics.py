"""Module de gestion des métriques de performance pour le proxy.

Contient les fonctions d'envoi et de planification des métriques de performance.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone

import httpx
from fastapi import Request

from .pseudonymizer import pseudonymize_ip_address, pseudonymize_user_id

logger = logging.getLogger(__name__)
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def extract_route(endpoint: str) -> str:
    """Extrait la route de base à partir de l'endpoint, sans les paramètres ni les valeurs numériques.

    Args:
        endpoint (str): Chemin complet de l'endpoint (ex: "/scan/api/results/123")

    Returns:
        str: Route de base sans paramètres (ex: "/scan/api/results")
    """
    if not endpoint:
        return endpoint

    parts = endpoint.strip("/").split("/")
    route_parts = []

    for part in parts:
        # Si le segment est vide, continuer
        if not part:
            continue

        # Si le segment contient {, c'est un pattern de route template, arrêter ici
        if "{" in part:
            break

        # Si le segment est purement numérique (float ou int), arrêter ici
        try:
            float(part)
            break
        except ValueError:
            pass

        # Si le segment ressemble à un UUID (format standard), arrêter ici
        if UUID_PATTERN.match(part):
            break

        # Sinon, ajouter le segment à la route
        route_parts.append(part)

    return "/" + "/".join(route_parts) if route_parts else endpoint


def build_endpoint(prefix: str, path: str) -> str:
    """Construit le chemin complet de l'endpoint.

    Args:
        prefix (str): Préfixe du service (ex: "scan")
        path (str): Chemin de la requête (ex: "/api/scan")

    Returns:
        str: Chemin complet (ex: "/scan/api/scan")
    """
    cleaned_path = path.lstrip("/")
    if cleaned_path:
        return f"/{prefix}/{cleaned_path}"
    return f"/{prefix}"


async def send_performance_metric(data: dict, admin_metrics_url: str, admin_metrics_api_key: str) -> None:
    """Envoie la métrique vers le service admin sans bloquer la requête utilisateur.

    Args:
        data (dict): Données de la métrique à envoyer
        admin_metrics_url (str): URL du service admin pour les métriques
        admin_metrics_api_key (str): Clé API pour les métriques
    """
    if not admin_metrics_url:
        return

    headers = {"Content-Type": "application/json"}
    if admin_metrics_api_key:
        headers["X-Admin-Metrics-Key"] = admin_metrics_api_key

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(admin_metrics_url, json=data, headers=headers)
    except Exception as exc:  # pragma: no cover - log uniquement en debug
        logger.debug("Échec d'envoi de la métrique: %s", exc)


def schedule_metric(
    prefix: str,
    path: str,
    request: Request,
    status_code: int,
    duration_ms: float,
    admin_metrics_url: str | None,
    admin_metrics_api_key: str,
    request_size_bytes: int | None = None,
    response_size_bytes: int | None = None,
) -> None:
    """Planifie l'envoi d'une métrique de performance.

    Args:
        prefix (str): Préfixe du service (pour les métriques)
        path (str): Chemin de la requête
        request (Request): Requête HTTP
        status_code (int): Code de statut HTTP
        duration_ms (float): Durée de la requête en millisecondes
        admin_metrics_url (str | None): URL du service admin pour les métriques
        admin_metrics_api_key (str): Clé API pour les métriques
        request_size_bytes (int | None): Taille de la requête en octets (optionnel)
        response_size_bytes (int | None): Taille de la réponse en octets (optionnel)
    """
    if admin_metrics_url is None:
        return

    # Calcul HMAC pseudonymisé si disponible
    user = getattr(request.state, "user", None)
    user_id_hash = None
    if user:
        user_id = user.get("sub") or user.get("username")
        if user_id:
            user_id_hash = pseudonymize_user_id(str(user_id))
            logger.debug("User ID hash calculé pour endpoint %s: %s...", build_endpoint(prefix, path), user_id_hash[:16] if user_id_hash else None)
        else:
            logger.debug("Pas de sub ou username dans user pour endpoint %s", build_endpoint(prefix, path))
    else:
        logger.debug("Pas de request.state.user pour endpoint %s", build_endpoint(prefix, path))

    # Hashage de l'adresse IP pour RGPD
    client_ip = request.client.host if request.client else None
    client_ip_hash = pseudonymize_ip_address(client_ip) if client_ip else None

    endpoint_full = build_endpoint(prefix, path)
    route = extract_route(endpoint_full)

    payload = {
        "service_prefix": prefix,
        "endpoint": endpoint_full,
        "route": route,
        "method": request.method,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "success": 200 <= status_code < 400,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "client_ip_hash": client_ip_hash,  # IP hashée pour RGPD
        "request_params": dict(request.query_params.multi_items()) if request.query_params else None,
        "userIdHash": user_id_hash,
        "request_size_bytes": request_size_bytes,
        "response_size_bytes": response_size_bytes,
    }

    asyncio.create_task(send_performance_metric(payload, admin_metrics_url, admin_metrics_api_key))
