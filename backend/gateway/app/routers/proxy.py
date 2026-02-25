"""Module de proxy pour l'API Gateway.

Enregistre les routes de proxy vers les services backend.
"""

import os

from fastapi import FastAPI

from ..config_loader import get_services_config
from ..services.proxy.handlers import make_handler


def register_proxy_routes(app: FastAPI) -> None:
    """
    Enregistre les routes de proxy vers les services backend.

    Args:
        app (FastAPI): Application FastAPI
    """
    SERVICES = get_services_config()
    ADMIN_SERVICE_URL = {svc["prefix"]: svc["url"] for svc in SERVICES}.get("admin")
    ADMIN_METRICS_URL = f"{ADMIN_SERVICE_URL.rstrip('/')}/api/metrics/performance" if ADMIN_SERVICE_URL else None  # noqa: Q000
    ADMIN_METRICS_API_KEY = os.getenv("ADMIN_METRICS_API_KEY", "")

    for svc in SERVICES:
        prefix, url = svc["prefix"], svc["url"]
        endpoint = make_handler(url, prefix, ADMIN_METRICS_URL, ADMIN_METRICS_API_KEY)
        app.add_api_route(
            f"/{prefix}/{{path:path}}",  # noqa: E231
            endpoint=endpoint,
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        )

    # Route spécifique pour /api/contact qui route vers l'admin-service
    # Cette route permet d'exposer le formulaire de contact publiquement
    if ADMIN_SERVICE_URL:
        from fastapi import Request

        # Créer le handler pour l'admin-service
        admin_handler = make_handler(ADMIN_SERVICE_URL, "admin", ADMIN_METRICS_URL, ADMIN_METRICS_API_KEY)

        async def contact_handler(request: Request):
            """Handler pour router /api/contact vers /admin/api/contact."""
            new_path = "api/contact"
            return await admin_handler(new_path, request)

        app.add_api_route(
            "/api/contact",
            endpoint=contact_handler,
            methods=["POST"],
        )
