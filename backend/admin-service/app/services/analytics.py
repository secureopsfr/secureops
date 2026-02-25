"""Services pour la gestion des événements analytics et leurs agrégations.

Pour les fenêtres temporelles larges (>= 1 jour) ou « toutes les données »,
les requêtes sont servies depuis des **vues matérialisées** pré-calculées
(rafraîchies toutes les heures). Pour les fenêtres courtes (< 1 jour),
la table brute ``analytics_events`` est interrogée directement afin de
conserver la fraîcheur temps réel.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_async_session
from app.models.analytics_event import AnalyticsEvent
from app.schemas.analytics import (
    AnalyticsEventCreate,
    DeviceBreakdown,
    DeviceBreakdownResponse,
    PageViewsSummaryResponse,
    PageViewSummary,
    ReferrersSummaryResponse,
    ReferrerSummary,
    TrafficTimeSeriesPoint,
    TrafficTimeSeriesResponse,
)
from app.services.materialized_views import (
    fetch_device_breakdown_from_mv,
    fetch_page_views_from_mv,
    fetch_referrers_from_mv,
    should_use_materialized_views,
)
from app.services.utils import auto_bucket_minutes

logger = logging.getLogger(__name__)


# ─────────────────────── Ingestion ───────────────────────


async def bulk_insert_events(events: List[AnalyticsEventCreate]) -> int:
    """Insère un batch d'événements analytics en base.

    Args:
        events: liste d'événements à persister.

    Returns:
        int: nombre d'événements insérés.

    Raises:
        SQLAlchemyError: si la persistance échoue.
    """
    async with get_async_session() as session:
        db_events = []
        for event in events:
            db_event = AnalyticsEvent(
                session_id=event.session_id,
                user_id_hash=event.user_id_hash,
                event_type=event.event_type,
                page=event.page,
                referrer=event.referrer,
                duration_ms=event.duration_ms,
                event_metadata=event.metadata,
                viewport=event.viewport,
                device_type=event.device_type,
                language=event.language,
                country=event.country,
                region=event.region,
                city=event.city,
                created_at=event.timestamp or datetime.now(timezone.utc),
            )
            db_events.append(db_event)
            session.add(db_event)

        try:
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise

        return len(db_events)


# ─────────────────────── Helpers ───────────────────────


def _cutoff(window_minutes: int | None) -> datetime | None:
    """Calcule la date de coupure pour la fenêtre temporelle.

    Args:
        window_minutes: fenêtre en minutes (None = toutes les données).

    Returns:
        datetime | None: date de coupure ou None.
    """
    if window_minutes is None:
        return None
    return datetime.now(timezone.utc) - timedelta(minutes=window_minutes)


# ─────────────────────── Consultation ───────────────────────


async def fetch_page_views_summary(window_minutes: int | None, limit: int) -> PageViewsSummaryResponse:  # noqa: C901
    """Récupère un résumé des vues par page avec métriques globales.

    Pour les fenêtres >= 1 jour ou toutes les données, utilise les vues
    matérialisées. Pour les fenêtres courtes, utilise la table brute.

    Args:
        window_minutes: fenêtre temporelle en minutes (None = toutes les données).
        limit: nombre maximal de pages à retourner.

    Returns:
        PageViewsSummaryResponse: métriques de vues par page + KPI globaux.
    """
    # ── Déléguer aux vues matérialisées si la fenêtre est large ──
    if should_use_materialized_views(window_minutes):
        try:
            mv_data = await fetch_page_views_from_mv(window_minutes, limit)
            return PageViewsSummaryResponse(
                pages=[
                    PageViewSummary(
                        page=p["page"],
                        views=p["views"],
                        unique_visitors=p["unique_visitors"],
                        avg_duration_ms=p["avg_duration_ms"],
                        bounce_count=p["bounce_count"],
                    )
                    for p in mv_data["pages"]
                ],
                total_views=mv_data["total_views"],
                total_unique_visitors=mv_data["total_unique_visitors"],
                avg_pages_per_session=mv_data["avg_pages_per_session"],
                avg_session_duration_ms=mv_data["avg_session_duration_ms"],
                bounce_rate=mv_data["bounce_rate"],
            )
        except Exception as exc:
            logger.warning("Fallback vers table brute (vue matérialisée indisponible): %s", exc)

    cutoff_dt = _cutoff(window_minutes)

    async with get_async_session() as session:
        # ── Sous-requête : sessions avec 1 seule page vue (pour le bounce) ──
        bounce_sub = select(
            AnalyticsEvent.session_id,
            func.count(func.distinct(AnalyticsEvent.page)).label("distinct_pages"),
        ).where(AnalyticsEvent.event_type == "page_view")
        if cutoff_dt is not None:
            bounce_sub = bounce_sub.where(AnalyticsEvent.created_at >= cutoff_dt)
        bounce_sub = bounce_sub.group_by(AnalyticsEvent.session_id).subquery()

        # ── Sous-requête : durée moyenne par page (depuis page_exit) ──
        duration_sub = select(
            AnalyticsEvent.page.label("page"),
            func.avg(AnalyticsEvent.duration_ms).label("avg_dur"),
        ).where(AnalyticsEvent.event_type == "page_exit")
        if cutoff_dt is not None:
            duration_sub = duration_sub.where(AnalyticsEvent.created_at >= cutoff_dt)
        duration_sub = duration_sub.group_by(AnalyticsEvent.page).subquery()

        # ── Requête principale : vues par page ──
        pages_stmt = select(
            AnalyticsEvent.page.label("page"),
            func.count().label("views"),
            func.count(func.distinct(AnalyticsEvent.session_id)).label("unique_visitors"),
        ).where(AnalyticsEvent.event_type == "page_view")
        if cutoff_dt is not None:
            pages_stmt = pages_stmt.where(AnalyticsEvent.created_at >= cutoff_dt)

        pages_stmt = pages_stmt.group_by(AnalyticsEvent.page).order_by(func.count().desc()).limit(limit)

        pages_result = await session.execute(pages_stmt)
        page_summaries: List[PageViewSummary] = []

        for row in pages_result.mappings():
            page = row["page"]
            # Chercher la durée moyenne pour cette page
            dur_stmt = select(duration_sub.c.avg_dur).where(duration_sub.c.page == page)
            dur_result = await session.execute(dur_stmt)
            avg_dur = dur_result.scalar()

            # Compter les bounces pour cette page (sessions entrées par cette page et avec 1 seule page)
            # Simplifié : nombre de sessions mono-page qui ont vu cette page
            bounce_stmt = (
                select(func.count())
                .select_from(bounce_sub)
                .where(bounce_sub.c.distinct_pages == 1)
                .where(
                    bounce_sub.c.session_id.in_(
                        select(AnalyticsEvent.session_id).where(AnalyticsEvent.event_type == "page_view").where(AnalyticsEvent.page == page)
                    )
                )
            )
            bounce_result = await session.execute(bounce_stmt)
            bounce_count = bounce_result.scalar() or 0

            page_summaries.append(
                PageViewSummary(
                    page=page,
                    views=int(row["views"]),
                    unique_visitors=int(row["unique_visitors"]),
                    avg_duration_ms=float(avg_dur) if avg_dur is not None else None,
                    bounce_count=int(bounce_count),
                )
            )

        # ── KPI globaux ──
        global_stmt = select(
            func.count().label("total_views"),
            func.count(func.distinct(AnalyticsEvent.session_id)).label("total_unique"),
        ).where(AnalyticsEvent.event_type == "page_view")
        if cutoff_dt is not None:
            global_stmt = global_stmt.where(AnalyticsEvent.created_at >= cutoff_dt)
        global_result = await session.execute(global_stmt)
        global_row = global_result.mappings().first()
        total_views = int(global_row["total_views"]) if global_row else 0
        total_unique = int(global_row["total_unique"]) if global_row else 0

        # Pages par session
        pps_stmt = select(func.avg(bounce_sub.c.distinct_pages)).select_from(bounce_sub)
        pps_result = await session.execute(pps_stmt)
        avg_pages_per_session = pps_result.scalar()

        # Durée moyenne de session (somme des durées page_exit par session, puis moyenne)
        session_dur_sub = select(
            AnalyticsEvent.session_id,
            func.sum(AnalyticsEvent.duration_ms).label("session_dur"),
        ).where(AnalyticsEvent.event_type == "page_exit")
        if cutoff_dt is not None:
            session_dur_sub = session_dur_sub.where(AnalyticsEvent.created_at >= cutoff_dt)
        session_dur_sub = session_dur_sub.group_by(AnalyticsEvent.session_id).subquery()

        avg_sess_dur_stmt = select(func.avg(session_dur_sub.c.session_dur))
        avg_sess_dur_result = await session.execute(avg_sess_dur_stmt)
        avg_session_duration = avg_sess_dur_result.scalar()

        # Taux de rebond global
        total_sessions_stmt = select(func.count(func.distinct(AnalyticsEvent.session_id))).where(AnalyticsEvent.event_type == "page_view")
        if cutoff_dt is not None:
            total_sessions_stmt = total_sessions_stmt.where(AnalyticsEvent.created_at >= cutoff_dt)
        total_sessions_result = await session.execute(total_sessions_stmt)
        total_sessions = total_sessions_result.scalar() or 0

        bounce_total_stmt = select(func.count()).select_from(bounce_sub).where(bounce_sub.c.distinct_pages == 1)
        bounce_total_result = await session.execute(bounce_total_stmt)
        total_bounces = bounce_total_result.scalar() or 0

        bounce_rate = total_bounces / total_sessions if total_sessions > 0 else None

        return PageViewsSummaryResponse(
            pages=page_summaries,
            total_views=total_views,
            total_unique_visitors=total_unique,
            avg_pages_per_session=float(avg_pages_per_session) if avg_pages_per_session is not None else None,
            avg_session_duration_ms=float(avg_session_duration) if avg_session_duration is not None else None,
            bounce_rate=bounce_rate,
        )


async def fetch_referrers_summary(window_minutes: int | None, limit: int) -> ReferrersSummaryResponse:
    """Récupère le top des referrers.

    Pour les fenêtres >= 1 jour ou toutes les données, utilise les vues
    matérialisées. Pour les fenêtres courtes, utilise la table brute.

    Args:
        window_minutes: fenêtre temporelle en minutes.
        limit: nombre maximal de referrers à retourner.

    Returns:
        ReferrersSummaryResponse: liste des top referrers.
    """
    # ── Déléguer aux vues matérialisées si la fenêtre est large ──
    if should_use_materialized_views(window_minutes):
        try:
            mv_data = await fetch_referrers_from_mv(window_minutes, limit)
            return ReferrersSummaryResponse(
                referrers=[
                    ReferrerSummary(
                        referrer=r["referrer"],
                        count=r["count"],
                        unique_visitors=r["unique_visitors"],
                    )
                    for r in mv_data
                ]
            )
        except Exception as exc:
            logger.warning("Fallback vers table brute (vue matérialisée indisponible): %s", exc)

    cutoff_dt = _cutoff(window_minutes)

    async with get_async_session() as session:
        # Nettoyer les referrers vides
        referrer_expr = func.coalesce(AnalyticsEvent.referrer, "direct").label("referrer_source")

        stmt = select(
            referrer_expr,
            func.count().label("count"),
            func.count(func.distinct(AnalyticsEvent.session_id)).label("unique_visitors"),
        ).where(AnalyticsEvent.event_type == "page_view")
        if cutoff_dt is not None:
            stmt = stmt.where(AnalyticsEvent.created_at >= cutoff_dt)

        stmt = stmt.group_by(referrer_expr).order_by(func.count().desc()).limit(limit)

        result = await session.execute(stmt)
        referrers: List[ReferrerSummary] = []
        for row in result.mappings():
            referrers.append(
                ReferrerSummary(
                    referrer=row["referrer_source"],
                    count=int(row["count"]),
                    unique_visitors=int(row["unique_visitors"]),
                )
            )

        return ReferrersSummaryResponse(referrers=referrers)


async def fetch_traffic_timeseries(
    window_minutes: int,
    bucket_minutes: int | None,
) -> TrafficTimeSeriesResponse:
    """Récupère une série temporelle de trafic (vues + visiteurs uniques par bucket).

    Args:
        window_minutes: fenêtre temporelle en minutes.
        bucket_minutes: taille du bucket en minutes (auto si None).

    Returns:
        TrafficTimeSeriesResponse: série temporelle ordonnée chronologiquement.
    """
    effective_bucket = bucket_minutes if bucket_minutes else auto_bucket_minutes(window_minutes)
    bucket_seconds = effective_bucket * 60
    cutoff_dt = _cutoff(window_minutes)

    async with get_async_session() as session:
        epoch_expr = func.extract("epoch", AnalyticsEvent.created_at)
        bucket_start = func.floor(epoch_expr / bucket_seconds) * bucket_seconds
        bucket_ts = func.to_timestamp(bucket_start).label("bucket_ts")

        stmt = (
            select(
                bucket_ts,
                func.count().label("views"),
                func.count(func.distinct(AnalyticsEvent.session_id)).label("unique_visitors"),
            )
            .where(AnalyticsEvent.event_type == "page_view")
            .group_by(bucket_ts)
            .order_by(bucket_ts.asc())
        )

        if cutoff_dt is not None:
            stmt = stmt.where(AnalyticsEvent.created_at >= cutoff_dt)

        result = await session.execute(stmt)
        points: List[TrafficTimeSeriesPoint] = []
        for row in result.mappings():
            points.append(
                TrafficTimeSeriesPoint(
                    timestamp=row["bucket_ts"],
                    views=int(row["views"]),
                    unique_visitors=int(row["unique_visitors"]),
                )
            )

        return TrafficTimeSeriesResponse(
            bucket_minutes=effective_bucket,
            points=points,
        )


async def fetch_device_breakdown(window_minutes: int | None) -> DeviceBreakdownResponse:
    """Récupère la répartition des sessions par type d'appareil.

    Pour les fenêtres >= 1 jour ou toutes les données, utilise les vues
    matérialisées. Pour les fenêtres courtes, utilise la table brute.

    Args:
        window_minutes: fenêtre temporelle en minutes (None = toutes les données).

    Returns:
        DeviceBreakdownResponse: répartition par type d'appareil.
    """
    # ── Déléguer aux vues matérialisées si la fenêtre est large ──
    if should_use_materialized_views(window_minutes):
        try:
            mv_data = await fetch_device_breakdown_from_mv(window_minutes)
            return DeviceBreakdownResponse(
                devices=[
                    DeviceBreakdown(
                        device_type=d["device_type"],
                        count=d["count"],
                        percentage=d["percentage"],
                    )
                    for d in mv_data
                ]
            )
        except Exception as exc:
            logger.warning("Fallback vers table brute (vue matérialisée indisponible): %s", exc)

    cutoff_dt = _cutoff(window_minutes)

    async with get_async_session() as session:
        device_expr = func.coalesce(AnalyticsEvent.device_type, "unknown").label("device")

        stmt = select(
            device_expr,
            func.count(func.distinct(AnalyticsEvent.session_id)).label("count"),
        ).where(AnalyticsEvent.event_type == "page_view")
        if cutoff_dt is not None:
            stmt = stmt.where(AnalyticsEvent.created_at >= cutoff_dt)

        stmt = stmt.group_by(device_expr).order_by(func.count(func.distinct(AnalyticsEvent.session_id)).desc())

        result = await session.execute(stmt)
        rows = list(result.mappings())

        total = sum(int(row["count"]) for row in rows)
        devices: List[DeviceBreakdown] = []
        for row in rows:
            count = int(row["count"])
            devices.append(
                DeviceBreakdown(
                    device_type=row["device"],
                    count=count,
                    percentage=round((count / total) * 100, 1) if total > 0 else 0,
                )
            )

        return DeviceBreakdownResponse(devices=devices)
