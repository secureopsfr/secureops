"""Router pour l'ingestion et la consultation des événements analytics (tracking site)."""

from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.analytics import (
    AnalyticsIngestRequest,
    AnalyticsIngestResponse,
    DeviceBreakdownResponse,
    PageViewsSummaryResponse,
    ReferrersSummaryResponse,
    TrafficTimeSeriesResponse,
)
from app.services.analytics import (
    bulk_insert_events,
    fetch_device_breakdown,
    fetch_page_views_summary,
    fetch_referrers_summary,
    fetch_traffic_timeseries,
)
from app.services.materialized_views import get_last_refresh_info, refresh_materialized_views

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Variables module-level pour éviter B008 (appels de fonctions dans les arguments par défaut)
WINDOW_MINUTES_QUERY = Query(default=None, ge=1, description="Fenêtre temporelle en minutes")
LIMIT_PAGES_QUERY = Query(default=50, ge=1, le=200, description="Nombre maximal de pages à retourner")
LIMIT_REFERRERS_QUERY = Query(default=20, ge=1, le=100, description="Nombre maximal de referrers")
WINDOW_MINUTES_7D_QUERY = Query(default=10080, ge=1, description="Fenêtre temporelle en minutes (défaut 7 jours)")
BUCKET_MINUTES_QUERY = Query(default=None, ge=1, description="Taille du bucket en minutes (auto si absent)")


# ─────────────────────── Ingestion (public) ───────────────────────


@router.post("/ingest", response_model=AnalyticsIngestResponse, status_code=HTTPStatus.CREATED)
async def ingest_analytics(payload: AnalyticsIngestRequest) -> AnalyticsIngestResponse:
    """Ingère un batch d'événements analytics envoyés par le frontend.

    Cet endpoint est public (pas d'auth requise) car il reçoit les événements
    de tous les visiteurs, y compris anonymes. La protection se fait par :
    - Validation stricte du payload (max 50 événements, tailles max, types autorisés)
    - Rate limiting au niveau du reverse proxy / gateway

    Args:
        payload: batch d'événements analytics.

    Returns:
        AnalyticsIngestResponse: confirmation avec le nombre d'événements enregistrés.
    """
    # Validation des types d'événements autorisés
    allowed_types = {"page_view", "page_exit", "session_start", "click", "scroll_depth"}
    for event in payload.events:
        if event.event_type not in allowed_types:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Type d'événement non autorisé: {event.event_type}. " f"Types autorisés: {', '.join(sorted(allowed_types))}",
            )

    try:
        count = await bulk_insert_events(payload.events)
        return AnalyticsIngestResponse(success=True, count=count)
    except SQLAlchemyError as exc:
        logger.error("Erreur SQL lors de l'ingestion analytics: %s", exc)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Erreur d'enregistrement des événements analytics",
        ) from exc


# ─────────────────────── Consultation (admin auth via gateway) ───────────────────────


@router.get("/pages", response_model=PageViewsSummaryResponse)
async def get_page_views_summary(
    window_minutes: int | None = WINDOW_MINUTES_QUERY,
    limit: int = LIMIT_PAGES_QUERY,
) -> PageViewsSummaryResponse:
    """Retourne les métriques de vues par page + KPI globaux.

    Args:
        window_minutes: fenêtre temporelle (None = toutes les données).
        limit: nombre maximal de pages.

    Returns:
        PageViewsSummaryResponse: métriques par page et KPIs globaux.
    """
    return await fetch_page_views_summary(window_minutes=window_minutes, limit=limit)


@router.get("/referrers", response_model=ReferrersSummaryResponse)
async def get_referrers_summary(
    window_minutes: int | None = WINDOW_MINUTES_QUERY,
    limit: int = LIMIT_REFERRERS_QUERY,
) -> ReferrersSummaryResponse:
    """Retourne le top des referrers (d'où viennent les visiteurs).

    Args:
        window_minutes: fenêtre temporelle (None = toutes les données).
        limit: nombre maximal de referrers.

    Returns:
        ReferrersSummaryResponse: liste des top referrers.
    """
    return await fetch_referrers_summary(window_minutes=window_minutes, limit=limit)


@router.get("/traffic/timeseries", response_model=TrafficTimeSeriesResponse)
async def get_traffic_timeseries(
    window_minutes: int = WINDOW_MINUTES_7D_QUERY,
    bucket_minutes: int | None = BUCKET_MINUTES_QUERY,
) -> TrafficTimeSeriesResponse:
    """Retourne une série temporelle du trafic (vues + visiteurs uniques par bucket).

    Args:
        window_minutes: fenêtre temporelle en minutes.
        bucket_minutes: taille du bucket (auto si None).

    Returns:
        TrafficTimeSeriesResponse: série temporelle ordonnée.
    """
    return await fetch_traffic_timeseries(window_minutes=window_minutes, bucket_minutes=bucket_minutes)


@router.get("/devices", response_model=DeviceBreakdownResponse)
async def get_device_breakdown(
    window_minutes: int | None = WINDOW_MINUTES_QUERY,
) -> DeviceBreakdownResponse:
    """Retourne la répartition des sessions par type d'appareil.

    Args:
        window_minutes: fenêtre temporelle (None = toutes les données).

    Returns:
        DeviceBreakdownResponse: répartition desktop / mobile / tablet.
    """
    return await fetch_device_breakdown(window_minutes=window_minutes)


# ─────────────────────── Vues matérialisées (admin) ───────────────────────


@router.post("/materialized-views/refresh")
async def refresh_views() -> dict:
    """Rafraîchit manuellement toutes les vues matérialisées analytics.

    Cet endpoint permet de forcer un rafraîchissement sans attendre le
    scheduler automatique (qui tourne toutes les heures).

    Returns:
        dict: résultat du rafraîchissement avec durée et statut par vue.
    """
    try:
        result = await refresh_materialized_views()
        return {"success": True, **result}
    except Exception as exc:
        logger.error("Erreur lors du rafraîchissement manuel des vues: %s", exc)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erreur de rafraîchissement: {exc}",
        ) from exc


@router.get("/materialized-views/status")
async def views_status() -> dict:
    """Retourne le statut des vues matérialisées (nombre de lignes par vue).

    Returns:
        dict: informations sur chaque vue matérialisée.
    """
    try:
        info = await get_last_refresh_info()
        return {"success": True, "views": info}
    except Exception as exc:
        logger.error("Erreur lors de la récupération du statut des vues: %s", exc)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erreur de récupération du statut: {exc}",
        ) from exc
