"""Services pour la gestion des métriques de performance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import List

from sqlalchemy import Integer, case, cast, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_async_session
from app.models.http_request import HttpRequest
from app.schemas.kpis import PerformanceMetricCreate, PerformanceMetricSummary, ServiceMetricSummary, TimeSeriesPoint
from app.services.utils import auto_bucket_minutes


async def record_performance_metric(payload: PerformanceMetricCreate) -> HttpRequest:
    """Enregistre une métrique de performance en base.

    Args:
        payload (PerformanceMetricCreate): données de la métrique à persister.

    Returns:
        HttpRequest: objet persistant fraîchement créé.

    Raises:
        SQLAlchemyError: si la persistance échoue.
    """
    # Calcul des tailles en Ko (division par 1024)
    request_size_kb = payload.request_size_bytes / 1024.0 if payload.request_size_bytes is not None else None
    response_size_kb = payload.response_size_bytes / 1024.0 if payload.response_size_bytes is not None else None

    async with get_async_session() as session:
        metric = HttpRequest(
            service_prefix=payload.service_prefix,
            endpoint=payload.endpoint,
            route=payload.route,
            method=payload.method,
            status_code=payload.status_code,
            duration_ms=payload.duration_ms,
            success=payload.success,
            created_at=payload.observed_at or datetime.now(UTC),
            client_ip_hash=payload.client_ip_hash,
            request_params=payload.request_params,
            user_id_hash=payload.user_id_hash,
            request_size_bytes=payload.request_size_bytes,
            response_size_bytes=payload.response_size_bytes,
            request_size_kb=request_size_kb,
            response_size_kb=response_size_kb,
        )
        session.add(metric)
        try:
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        await session.refresh(metric)
        return metric


async def fetch_performance_summary(window_minutes: int | None, limit: int) -> List[PerformanceMetricSummary]:
    """Récupère un résumé statistique des métriques.

    Args:
        window_minutes (int | None): fenêtre temporelle à considérer (en minutes). Si None, calcule sur toutes les données.
        limit (int): nombre maximal d'entrées agrégées à retourner.

    Returns:
        List[PerformanceMetricSummary]: liste de métriques agrégées.
    """
    async with get_async_session() as session:
        # Utiliser COALESCE pour gérer les cas où route est NULL (données anciennes)
        route_expr = func.coalesce(HttpRequest.route, HttpRequest.endpoint).label("route")
        stmt = (
            select(
                route_expr,
                func.count().label("count"),
                func.sum(cast(HttpRequest.success, Integer)).label("success_count"),
                func.sum(case((HttpRequest.status_code.between(400, 499), 1), else_=0)).label("count_4xx"),
                func.sum(case((HttpRequest.status_code.between(500, 599), 1), else_=0)).label("count_5xx"),
                func.sum(case((HttpRequest.status_code == 504, 1), else_=0)).label("count_timeout"),
                func.avg(HttpRequest.duration_ms).label("avg_ms"),
                func.percentile_cont(0.05).within_group(HttpRequest.duration_ms).label("p5_ms"),
                func.percentile_cont(0.5).within_group(HttpRequest.duration_ms).label("median_ms"),
                func.min(HttpRequest.duration_ms).label("min_ms"),
                func.max(HttpRequest.duration_ms).label("max_ms"),
                func.var_pop(HttpRequest.duration_ms).label("variance_ms2"),
                func.stddev_pop(HttpRequest.duration_ms).label("std_ms"),
                func.percentile_cont(0.95).within_group(HttpRequest.duration_ms).label("p95_ms"),
                func.avg(HttpRequest.request_size_kb).label("avg_request_size_kb"),
                func.percentile_cont(0.05).within_group(HttpRequest.request_size_kb).label("p5_request_size_kb"),
                func.percentile_cont(0.5).within_group(HttpRequest.request_size_kb).label("median_request_size_kb"),
                func.percentile_cont(0.95).within_group(HttpRequest.request_size_kb).label("p95_request_size_kb"),
                func.min(HttpRequest.request_size_kb).label("min_request_size_kb"),
                func.max(HttpRequest.request_size_kb).label("max_request_size_kb"),
                func.var_pop(HttpRequest.request_size_kb).label("variance_request_size_kb"),
                func.stddev_pop(HttpRequest.request_size_kb).label("std_request_size_kb"),
                func.avg(HttpRequest.response_size_kb).label("avg_response_size_kb"),
                func.percentile_cont(0.05).within_group(HttpRequest.response_size_kb).label("p5_response_size_kb"),
                func.percentile_cont(0.5).within_group(HttpRequest.response_size_kb).label("median_response_size_kb"),
                func.percentile_cont(0.95).within_group(HttpRequest.response_size_kb).label("p95_response_size_kb"),
                func.min(HttpRequest.response_size_kb).label("min_response_size_kb"),
                func.max(HttpRequest.response_size_kb).label("max_response_size_kb"),
                func.var_pop(HttpRequest.response_size_kb).label("variance_response_size_kb"),
                func.stddev_pop(HttpRequest.response_size_kb).label("std_response_size_kb"),
            )
            .group_by(route_expr)
            .order_by(route_expr.asc())
            .limit(limit)
        )

        # Appliquer le filtre par date uniquement si window_minutes est fourni
        if window_minutes is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            stmt = stmt.where(HttpRequest.created_at >= cutoff)

        result = await session.execute(stmt)
        summaries: List[PerformanceMetricSummary] = []
        for row in result.mappings():
            count = int(row.get("count", 0))
            success_total = float(row.get("success_count") or 0.0)
            success_rate = success_total / count if count else 0.0
            count_4xx = float(row.get("count_4xx") or 0.0)
            count_5xx = float(row.get("count_5xx") or 0.0)
            count_timeout = float(row.get("count_timeout") or 0.0)
            client_error_rate = count_4xx / count if count else 0.0
            server_error_rate = count_5xx / count if count else 0.0
            timeout_rate = count_timeout / count if count else 0.0

            def _to_float(value):
                return float(value) if value is not None else None

            summaries.append(
                PerformanceMetricSummary(
                    route=row["route"],
                    count=count,
                    success_rate=success_rate,
                    client_error_rate=client_error_rate,
                    server_error_rate=server_error_rate,
                    timeout_rate=timeout_rate,
                    avg_ms=_to_float(row.get("avg_ms")),
                    p5_ms=_to_float(row.get("p5_ms")),
                    median_ms=_to_float(row.get("median_ms")),
                    p95_ms=_to_float(row.get("p95_ms")),
                    min_ms=_to_float(row.get("min_ms")),
                    max_ms=_to_float(row.get("max_ms")),
                    variance_ms2=_to_float(row.get("variance_ms2")),
                    std_ms=_to_float(row.get("std_ms")),
                    avg_request_size_kb=_to_float(row.get("avg_request_size_kb")),
                    p5_request_size_kb=_to_float(row.get("p5_request_size_kb")),
                    median_request_size_kb=_to_float(row.get("median_request_size_kb")),
                    p95_request_size_kb=_to_float(row.get("p95_request_size_kb")),
                    min_request_size_kb=_to_float(row.get("min_request_size_kb")),
                    max_request_size_kb=_to_float(row.get("max_request_size_kb")),
                    variance_request_size_kb=_to_float(row.get("variance_request_size_kb")),
                    std_request_size_kb=_to_float(row.get("std_request_size_kb")),
                    avg_response_size_kb=_to_float(row.get("avg_response_size_kb")),
                    p5_response_size_kb=_to_float(row.get("p5_response_size_kb")),
                    median_response_size_kb=_to_float(row.get("median_response_size_kb")),
                    p95_response_size_kb=_to_float(row.get("p95_response_size_kb")),
                    min_response_size_kb=_to_float(row.get("min_response_size_kb")),
                    max_response_size_kb=_to_float(row.get("max_response_size_kb")),
                    variance_response_size_kb=_to_float(row.get("variance_response_size_kb")),
                    std_response_size_kb=_to_float(row.get("std_response_size_kb")),
                )
            )

        return summaries


async def fetch_service_summary(window_minutes: int | None, limit: int) -> List[ServiceMetricSummary]:
    """Récupère un résumé statistique agrégé par service backend.

    Args:
        window_minutes (int | None): fenêtre temporelle à considérer en minutes. Si None, toutes les données sont agrégées.
        limit (int): nombre maximal d'enregistrements à retourner.

    Returns:
        List[ServiceMetricSummary]: collection des métriques agrégées par service backend.
    """
    async with get_async_session() as session:
        stmt = (
            select(
                HttpRequest.service_prefix.label("service_prefix"),
                func.count().label("count"),
                func.sum(cast(HttpRequest.success, Integer)).label("success_count"),
                func.sum(case((HttpRequest.status_code.between(400, 499), 1), else_=0)).label("count_4xx"),
                func.sum(case((HttpRequest.status_code.between(500, 599), 1), else_=0)).label("count_5xx"),
                func.sum(case((HttpRequest.status_code == 504, 1), else_=0)).label("count_timeout"),
                func.avg(HttpRequest.duration_ms).label("avg_ms"),
                func.percentile_cont(0.05).within_group(HttpRequest.duration_ms).label("p5_ms"),
                func.percentile_cont(0.5).within_group(HttpRequest.duration_ms).label("median_ms"),
                func.min(HttpRequest.duration_ms).label("min_ms"),
                func.max(HttpRequest.duration_ms).label("max_ms"),
                func.var_pop(HttpRequest.duration_ms).label("variance_ms2"),
                func.stddev_pop(HttpRequest.duration_ms).label("std_ms"),
                func.percentile_cont(0.95).within_group(HttpRequest.duration_ms).label("p95_ms"),
                func.avg(HttpRequest.request_size_kb).label("avg_request_size_kb"),
                func.percentile_cont(0.05).within_group(HttpRequest.request_size_kb).label("p5_request_size_kb"),
                func.percentile_cont(0.5).within_group(HttpRequest.request_size_kb).label("median_request_size_kb"),
                func.percentile_cont(0.95).within_group(HttpRequest.request_size_kb).label("p95_request_size_kb"),
                func.min(HttpRequest.request_size_kb).label("min_request_size_kb"),
                func.max(HttpRequest.request_size_kb).label("max_request_size_kb"),
                func.var_pop(HttpRequest.request_size_kb).label("variance_request_size_kb"),
                func.stddev_pop(HttpRequest.request_size_kb).label("std_request_size_kb"),
                func.avg(HttpRequest.response_size_kb).label("avg_response_size_kb"),
                func.percentile_cont(0.05).within_group(HttpRequest.response_size_kb).label("p5_response_size_kb"),
                func.percentile_cont(0.5).within_group(HttpRequest.response_size_kb).label("median_response_size_kb"),
                func.percentile_cont(0.95).within_group(HttpRequest.response_size_kb).label("p95_response_size_kb"),
                func.min(HttpRequest.response_size_kb).label("min_response_size_kb"),
                func.max(HttpRequest.response_size_kb).label("max_response_size_kb"),
                func.var_pop(HttpRequest.response_size_kb).label("variance_response_size_kb"),
                func.stddev_pop(HttpRequest.response_size_kb).label("std_response_size_kb"),
            )
            .group_by(HttpRequest.service_prefix)
            .order_by(HttpRequest.service_prefix.asc())
            .limit(limit)
        )

        if window_minutes is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            stmt = stmt.where(HttpRequest.created_at >= cutoff)

        result = await session.execute(stmt)

        summaries: List[ServiceMetricSummary] = []
        for row in result.mappings():
            count = int(row.get("count", 0))
            success_total = float(row.get("success_count") or 0.0)
            success_rate = success_total / count if count else 0.0
            count_4xx = float(row.get("count_4xx") or 0.0)
            count_5xx = float(row.get("count_5xx") or 0.0)
            count_timeout = float(row.get("count_timeout") or 0.0)
            client_error_rate = count_4xx / count if count else 0.0
            server_error_rate = count_5xx / count if count else 0.0
            timeout_rate = count_timeout / count if count else 0.0

            def _to_float(value):
                return float(value) if value is not None else None

            summaries.append(
                ServiceMetricSummary(
                    service_prefix=row.get("service_prefix", "inconnu"),
                    count=count,
                    success_rate=success_rate,
                    client_error_rate=client_error_rate,
                    server_error_rate=server_error_rate,
                    timeout_rate=timeout_rate,
                    avg_ms=_to_float(row.get("avg_ms")),
                    p5_ms=_to_float(row.get("p5_ms")),
                    median_ms=_to_float(row.get("median_ms")),
                    p95_ms=_to_float(row.get("p95_ms")),
                    min_ms=_to_float(row.get("min_ms")),
                    max_ms=_to_float(row.get("max_ms")),
                    variance_ms2=_to_float(row.get("variance_ms2")),
                    std_ms=_to_float(row.get("std_ms")),
                    avg_request_size_kb=_to_float(row.get("avg_request_size_kb")),
                    p5_request_size_kb=_to_float(row.get("p5_request_size_kb")),
                    median_request_size_kb=_to_float(row.get("median_request_size_kb")),
                    p95_request_size_kb=_to_float(row.get("p95_request_size_kb")),
                    min_request_size_kb=_to_float(row.get("min_request_size_kb")),
                    max_request_size_kb=_to_float(row.get("max_request_size_kb")),
                    variance_request_size_kb=_to_float(row.get("variance_request_size_kb")),
                    std_request_size_kb=_to_float(row.get("std_request_size_kb")),
                    avg_response_size_kb=_to_float(row.get("avg_response_size_kb")),
                    p5_response_size_kb=_to_float(row.get("p5_response_size_kb")),
                    median_response_size_kb=_to_float(row.get("median_response_size_kb")),
                    p95_response_size_kb=_to_float(row.get("p95_response_size_kb")),
                    min_response_size_kb=_to_float(row.get("min_response_size_kb")),
                    max_response_size_kb=_to_float(row.get("max_response_size_kb")),
                    variance_response_size_kb=_to_float(row.get("variance_response_size_kb")),
                    std_response_size_kb=_to_float(row.get("std_response_size_kb")),
                )
            )

        return summaries


async def fetch_timeseries(
    route: str | None,
    window_minutes: int,
    bucket_minutes: int | None,
    service_prefix: str | None = None,
) -> tuple[List[TimeSeriesPoint], int]:
    """Récupère une série temporelle de métriques (count + avg_ms par bucket).

    Args:
        route (str | None): route à filtrer (None pour toutes les routes).
        window_minutes (int): fenêtre temporelle en minutes.
        bucket_minutes (int | None): taille du bucket en minutes (auto si None).
        service_prefix (str | None): préfixe du service backend à filtrer (optionnel).

    Returns:
        tuple[List[TimeSeriesPoint], int]: liste de points et taille effective du bucket.
    """
    effective_bucket = bucket_minutes if bucket_minutes else auto_bucket_minutes(window_minutes)
    bucket_seconds = effective_bucket * 60

    async with get_async_session() as session:
        # Construire l'expression de bucket via FLOOR pour forcer la division entière.
        # Note : en SQLAlchemy 2.0, l'opérateur `/` (truediv) produit une division
        # flottante (type Numeric), donc `BIGINT / int` ne fait PAS de division entière.
        # On utilise floor(epoch / bucket) * bucket pour contourner ce comportement.
        epoch_expr = func.extract("epoch", HttpRequest.created_at)
        bucket_start = func.floor(epoch_expr / bucket_seconds) * bucket_seconds
        bucket_ts = func.to_timestamp(bucket_start).label("bucket_ts")

        stmt = (
            select(
                bucket_ts,
                func.count().label("count"),
                func.avg(HttpRequest.duration_ms).label("avg_ms"),
            )
            .group_by(bucket_ts)
            .order_by(bucket_ts.asc())
        )

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        stmt = stmt.where(HttpRequest.created_at >= cutoff)

        if route:
            route_expr = func.coalesce(HttpRequest.route, HttpRequest.endpoint)
            stmt = stmt.where(route_expr == route)

        if service_prefix:
            stmt = stmt.where(HttpRequest.service_prefix == service_prefix)

        result = await session.execute(stmt)

        points: List[TimeSeriesPoint] = []
        for row in result.mappings():
            ts = row["bucket_ts"]
            points.append(
                TimeSeriesPoint(
                    timestamp=ts,
                    count=int(row["count"]),
                    avg_ms=float(row["avg_ms"]) if row["avg_ms"] is not None else None,
                )
            )

        return points, effective_bucket
