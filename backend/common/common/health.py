"""Factory pour les routes de santé — module commun.

Fournit ``create_health_router(service_name, prefix, tags)`` permettant
à chaque service de créer son endpoint ``/health`` en une seule ligne.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter


def create_health_router(
    service_name: str,
    prefix: str = "/api",
    tags: list[str] | None = None,
) -> APIRouter:
    """Crée un router APIRouter avec un endpoint ``GET /health``.

    Args:
        service_name: nom du service à inclure dans la réponse.
        prefix: préfixe URL du router (``/api`` par défaut).
        tags: tags OpenAPI du router (``["health"]`` par défaut).

    Returns:
        APIRouter: router configuré avec l'endpoint health.
    """
    if tags is None:
        tags = ["health"]

    router = APIRouter(prefix=prefix, tags=tags)

    @router.get("/health")
    async def health() -> dict[str, str]:
        """Health check du service."""
        return {
            "status": "ok",
            "service": service_name,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    return router
