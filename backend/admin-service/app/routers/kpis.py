"""Router pour l'ingestion et la consultation des métriques de performance."""

from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from app.config_loader import settings
from app.schemas.kpis import (
    PerformanceMetricCreate,
    PerformanceMetricResponse,
    PerformanceSummaryResponse,
    ServiceSummaryResponse,
    TimeSeriesResponse,
)
from app.services.kpis import fetch_performance_summary, fetch_service_summary, fetch_timeseries, record_performance_metric

logger = logging.getLogger(__name__)

config = settings()
router_config = config.routers.kpis
router = APIRouter(prefix=router_config.prefix, tags=router_config.tags)
METRICS_API_KEY = config.metrics.api_key

window_minutes_config = config.metrics.queries.window_minutes
limit_config = config.metrics.queries.limit

WINDOW_MINUTES_QUERY = Query(
    default=None,
    ge=window_minutes_config.ge if window_minutes_config.ge is not None else None,
    le=window_minutes_config.le if window_minutes_config.le is not None else None,
    description=window_minutes_config.description,
)
LIMIT_QUERY = Query(
    limit_config.default,
    ge=limit_config.ge,
    le=limit_config.le,
    description=limit_config.description,
)


HEADER_X_ADMIN_METRICS_KEY = Header(default=None, alias="X-Admin-Metrics-Key")


def verify_metrics_api_key(x_admin_metrics_key: str | None = HEADER_X_ADMIN_METRICS_KEY) -> None:
    """Vérifie la clé API transmise par le gateway.

    Args:
        x_admin_metrics_key (str | None): clé transmise dans le header.

    Raises:
        HTTPException: si la clé attendue est définie et ne correspond pas.
    """
    # Si aucune clé n'est configurée, autoriser sans vérification (pour le développement)
    if not METRICS_API_KEY or METRICS_API_KEY.strip() == "":
        logger.debug("Aucune clé API configurée, autorisation sans vérification")
        return
    # Si une clé est configurée, vérifier qu'elle correspond
    if x_admin_metrics_key != METRICS_API_KEY:
        logger.warning("Clé API métriques invalide")
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Clé API métriques invalide")


DEPENDS_VERIFY_METRICS_API_KEY = Depends(verify_metrics_api_key)  # module-level to éviter B008


@router.post("/performance", response_model=PerformanceMetricResponse, status_code=HTTPStatus.CREATED)
async def ingest_performance_metric(payload: PerformanceMetricCreate, _: None = DEPENDS_VERIFY_METRICS_API_KEY) -> PerformanceMetricResponse:
    """Ingère une métrique envoyée par l'API Gateway."""
    try:
        http_request = await record_performance_metric(payload)
        return PerformanceMetricResponse(success=True, metric_id=str(http_request.id), created_at=http_request.created_at)
    except SQLAlchemyError as exc:
        logger.error("Erreur SQL lors de l'enregistrement de la métrique: %s", exc)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Erreur d'enregistrement de la métrique") from exc


@router.get("/performance/summary", response_model=PerformanceSummaryResponse)
async def get_performance_summary(
    window_minutes: int | None = WINDOW_MINUTES_QUERY,
    limit: int = LIMIT_QUERY,
) -> PerformanceSummaryResponse:
    """Retourne des statistiques agrégées pour les métriques collectées.

    Args:
        request: requête HTTP.
        window_minutes: fenêtre temporelle en minutes (optionnel, si None calcule sur toutes les données).
        limit: nombre maximal d'entrées agrégées à retourner.

    Returns:
        PerformanceSummaryResponse: réponse contenant les métriques agrégées.
    """
    metrics = await fetch_performance_summary(window_minutes=window_minutes, limit=limit)
    return PerformanceSummaryResponse(metrics=metrics)


@router.get("/performance/services", response_model=ServiceSummaryResponse)
async def get_service_performance_summary(
    window_minutes: int | None = WINDOW_MINUTES_QUERY,
    limit: int = LIMIT_QUERY,
) -> ServiceSummaryResponse:
    """Retourne des statistiques agrégées par service backend.

    Args:
        request (Request): requête HTTP courante.
        window_minutes (int | None): fenêtre temporelle en minutes (None pour toutes les données).
        limit (int): nombre maximal d'entrées agrégées à retourner.

    Returns:
        ServiceSummaryResponse: réponse contenant les métriques agrégées par service.
    """
    metrics = await fetch_service_summary(window_minutes=window_minutes, limit=limit)
    return ServiceSummaryResponse(metrics=metrics)


@router.get("/performance/timeseries", response_model=TimeSeriesResponse)
async def get_performance_timeseries(
    route: str | None = Query(default=None, description="Route à filtrer (optionnel, si absent agrège toutes les routes)"),  # noqa: B008
    service_prefix: str | None = Query(default=None, description="Service backend à filtrer (optionnel)"),  # noqa: B008
    window_minutes: int = Query(default=10080, ge=1, description="Fenêtre temporelle en minutes (défaut 7 jours)"),  # noqa: B008
    bucket_minutes: int | None = Query(default=None, ge=1, description="Taille du bucket en minutes (auto si absent)"),  # noqa: B008
) -> TimeSeriesResponse:
    """Retourne une série temporelle (count + avgMs par bucket) pour tracer un graphe d'évolution.

    Args:
        route (str | None): route à filtrer. Si None, toutes les routes sont agrégées.
        service_prefix (str | None): service backend à filtrer. Si None, tous les services sont agrégés.
        window_minutes (int): fenêtre temporelle en minutes.
        bucket_minutes (int | None): taille du bucket en minutes. Calculé automatiquement si absent.

    Returns:
        TimeSeriesResponse: série temporelle ordonnée chronologiquement.
    """
    points, effective_bucket = await fetch_timeseries(
        route=route,
        window_minutes=window_minutes,
        bucket_minutes=bucket_minutes,
        service_prefix=service_prefix,
    )
    return TimeSeriesResponse(
        route=route,
        bucket_minutes=effective_bucket,
        points=points,
    )
