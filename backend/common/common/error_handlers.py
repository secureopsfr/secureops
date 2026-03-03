"""Gestion centralisée des erreurs HTTP — module commun.

Ce module fournit des handlers d'exception uniformes pour tous les services
FastAPI du projet. Il suffit d'appeler ``register_exception_handlers(app)``
dans le ``main.py`` de chaque service.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _build_error_payload(
    request: Request,
    message: str,
    details: Optional[Any],
    status_code: int,
) -> Dict[str, Any]:
    """Construit un payload JSON standard pour les erreurs HTTP.

    Args:
        request: requête FastAPI ayant provoqué l'erreur.
        message: message d'erreur principal destiné au client.
        details: informations additionnelles ou erreurs de validation.
        status_code: code de statut HTTP associé à l'erreur.

    Returns:
        Dict[str, Any]: payload JSON structuré.
    """
    payload: Dict[str, Any] = {
        "success": False,
        "error": message,
        "detail": message,  # Alias pour compatibilité frontend (err.detail)
        "status_code": status_code,
        "path": request.url.path,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    if details not in (None, ""):
        payload["details"] = details

    return payload


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Gère les HTTPException standard en appliquant un format unique."""
    logger.warning(
        "HTTPException interceptée",
        extra={"path": request.url.path, "status_code": exc.status_code, "detail": exc.detail},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_payload(request, str(exc.detail or "Erreur HTTP"), exc.detail, exc.status_code),
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Formate les erreurs de validation FastAPI."""
    # Nettoyer les erreurs pour rendre les objets ValueError JSON-serialisables
    cleaned_errors = []
    for error in exc.errors():
        cleaned_error = error.copy()
        if "ctx" in cleaned_error and "error" in cleaned_error["ctx"]:
            error_obj = cleaned_error["ctx"]["error"]
            if isinstance(error_obj, Exception):
                cleaned_error["ctx"]["error"] = str(error_obj)
        cleaned_errors.append(cleaned_error)

    logger.warning(
        "Erreur de validation interceptée",
        extra={"path": request.url.path, "errors": cleaned_errors},
    )
    return JSONResponse(
        status_code=422,
        content=_build_error_payload(request, "Erreur de validation des paramètres", cleaned_errors, 422),
    )


async def _generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Capture toute autre exception non gérée."""
    logger.error(
        "Exception non gérée interceptée",
        extra={"path": request.url.path},
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content=_build_error_payload(request, "Erreur interne du serveur", str(exc), 500),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Enregistre les handlers globaux sur l'application FastAPI.

    Args:
        app: application sur laquelle ajouter les handlers.
    """
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _generic_exception_handler)
