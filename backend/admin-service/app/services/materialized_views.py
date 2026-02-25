"""Service de gestion des vues matérialisées analytics.

Ce module fournit :
- Le rafraîchissement concurrent des vues matérialisées (REFRESH CONCURRENTLY).
- Des fonctions de lecture optimisées qui agrègent les données pré-calculées
  à la place des full-table scans sur ``analytics_events``.
- Un seuil configurable : les vues sont utilisées quand la fenêtre temporelle
  est >= 1 jour (1440 minutes) ou « toutes les données » (None).
  Pour les fenêtres courtes (< 1 jour) le code existant sur la table brute
  est conservé afin de garder la fraîcheur temps réel.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.db import get_async_session

logger = logging.getLogger(__name__)

# Seuil en minutes au-delà duquel on utilise les vues matérialisées.
# En dessous, la table brute est interrogée directement (données temps réel).
MV_WINDOW_THRESHOLD_MINUTES = 1440  # 1 jour


# ─────────────────────── Noms des vues ───────────────────────

MATERIALIZED_VIEWS = [
    "mv_analytics_daily_stats",
    "mv_analytics_page_daily",
    "mv_analytics_referrer_daily",
    "mv_analytics_device_daily",
    "mv_analytics_session_stats",
]


# ─────────────────────── Refresh ───────────────────────


async def refresh_materialized_views() -> Dict[str, Any]:
    """Rafraîchit toutes les vues matérialisées de façon concurrente.

    Le mot-clé CONCURRENTLY permet de rafraîchir sans verrouiller les
    lectures. Nécessite un UNIQUE INDEX sur chaque vue (déjà créé dans
    la migration 0002).

    Returns:
        Dict contenant le statut du rafraîchissement et la durée en ms.
    """
    start = datetime.now(timezone.utc)
    results: Dict[str, str] = {}

    async with get_async_session() as session:
        for view_name in MATERIALIZED_VIEWS:
            try:
                await session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
                await session.commit()
                results[view_name] = "ok"
                logger.debug("Vue %s rafraîchie avec succès", view_name)
            except Exception as exc:
                await session.rollback()
                results[view_name] = f"error: {exc}"
                logger.warning("Erreur lors du rafraîchissement de %s: %s", view_name, exc)

    elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    logger.info(
        "Rafraîchissement des vues matérialisées terminé en %.0f ms — %s",
        elapsed_ms,
        results,
    )
    return {"refreshed": results, "duration_ms": round(elapsed_ms)}


async def get_last_refresh_info() -> Dict[str, Any]:
    """Retourne des informations sur les vues matérialisées.

    Returns:
        Dict contenant les vues et leur nombre de lignes.
    """
    info: Dict[str, Any] = {}
    async with get_async_session() as session:
        for view_name in MATERIALIZED_VIEWS:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {view_name}"))  # noqa: S608
                row_count = result.scalar() or 0
                info[view_name] = {"rows": row_count}
            except Exception:
                info[view_name] = {"rows": 0, "error": "vue inexistante ou vide"}
    return info


# ─────────────────────── Helpers ───────────────────────


def should_use_materialized_views(window_minutes: int | None) -> bool:
    """Détermine si on doit utiliser les vues matérialisées.

    Args:
        window_minutes: fenêtre temporelle en minutes (None = toutes les données).

    Returns:
        True si les vues matérialisées doivent être utilisées.
    """
    if window_minutes is None:
        return True
    return window_minutes >= MV_WINDOW_THRESHOLD_MINUTES


def _cutoff_date(window_minutes: int | None) -> Optional[date]:
    """Calcule la date de coupure pour filtrer les vues matérialisées.

    Args:
        window_minutes: fenêtre temporelle en minutes.

    Returns:
        date ou None (toutes les données).
    """
    if window_minutes is None:
        return None
    return (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).date()


# ─────────────────────── Lecture depuis les vues ───────────────────────


async def fetch_page_views_from_mv(window_minutes: int | None, limit: int) -> Dict[str, Any]:
    """Récupère les stats de pages depuis les vues matérialisées.

    Agrège les données pré-calculées par jour, ce qui est beaucoup plus
    rapide que de scanner la table brute ``analytics_events``.

    Note : ``unique_visitors`` est une approximation (somme des uniques
    quotidiens), ce qui est acceptable pour le dashboard admin.

    Args:
        window_minutes: fenêtre temporelle en minutes (None = tout).
        limit: nombre maximal de pages à retourner.

    Returns:
        Dict compatible avec le format PageViewsSummaryResponse.
    """
    cutoff = _cutoff_date(window_minutes)

    async with get_async_session() as session:
        # ── Per-page stats ──
        page_query = """
            SELECT
                page,
                SUM(views)::BIGINT AS views,
                SUM(unique_visitors)::BIGINT AS unique_visitors,
                CASE
                    WHEN SUM(duration_count) > 0
                    THEN SUM(avg_duration_ms * duration_count) / SUM(duration_count)
                    ELSE NULL
                END AS avg_duration_ms
            FROM mv_analytics_page_daily
            WHERE views > 0
        """
        params: Dict[str, Any] = {}
        if cutoff is not None:
            page_query += " AND stat_date >= :cutoff"
            params["cutoff"] = cutoff
        page_query += " GROUP BY page ORDER BY SUM(views) DESC LIMIT :limit"
        params["limit"] = limit

        page_result = await session.execute(text(page_query), params)
        page_rows = list(page_result.mappings())

        # ── Bounce counts par page (sessions mono-page) ──
        bounce_query = """
            SELECT
                ae.page,
                COUNT(DISTINCT s.session_id)::BIGINT AS bounce_count
            FROM mv_analytics_session_stats s
            JOIN analytics_events ae ON ae.session_id = s.session_id AND ae.event_type = 'page_view'
            WHERE s.distinct_pages = 1
        """
        bounce_params: Dict[str, Any] = {}
        if cutoff is not None:
            bounce_query += " AND s.session_date >= :cutoff"
            bounce_params["cutoff"] = cutoff
        bounce_query += " GROUP BY ae.page"

        bounce_result = await session.execute(text(bounce_query), bounce_params)
        bounce_map = {row["page"]: int(row["bounce_count"]) for row in bounce_result.mappings()}

        pages: List[Dict[str, Any]] = []
        for row in page_rows:
            pages.append(
                {
                    "page": row["page"],
                    "views": int(row["views"]),
                    "unique_visitors": int(row["unique_visitors"]),
                    "avg_duration_ms": float(row["avg_duration_ms"]) if row["avg_duration_ms"] is not None else None,
                    "bounce_count": bounce_map.get(row["page"], 0),
                }
            )

        # ── Global KPIs depuis mv_analytics_daily_stats ──
        global_query = """
            SELECT
                COALESCE(SUM(total_page_views), 0)::BIGINT AS total_views,
                COALESCE(SUM(unique_sessions), 0)::BIGINT AS total_unique
            FROM mv_analytics_daily_stats
        """
        global_params: Dict[str, Any] = {}
        if cutoff is not None:
            global_query += " WHERE stat_date >= :cutoff"
            global_params["cutoff"] = cutoff

        global_result = await session.execute(text(global_query), global_params)
        global_row = global_result.mappings().first()
        total_views = int(global_row["total_views"]) if global_row else 0
        total_unique = int(global_row["total_unique"]) if global_row else 0

        # ── Session-level KPIs depuis mv_analytics_session_stats ──
        session_query = """
            SELECT
                AVG(distinct_pages) AS avg_pages,
                AVG(total_duration_ms) FILTER (WHERE total_duration_ms IS NOT NULL) AS avg_session_dur,
                COUNT(*) FILTER (WHERE page_view_count > 0) AS total_sessions,
                COUNT(*) FILTER (WHERE distinct_pages = 1 AND page_view_count > 0) AS total_bounces
            FROM mv_analytics_session_stats
        """
        session_params: Dict[str, Any] = {}
        if cutoff is not None:
            session_query += " WHERE session_date >= :cutoff"
            session_params["cutoff"] = cutoff

        session_result = await session.execute(text(session_query), session_params)
        session_row = session_result.mappings().first()

        avg_pages = float(session_row["avg_pages"]) if session_row and session_row["avg_pages"] else None
        avg_session_dur = float(session_row["avg_session_dur"]) if session_row and session_row["avg_session_dur"] else None
        total_sessions = int(session_row["total_sessions"]) if session_row else 0
        total_bounces = int(session_row["total_bounces"]) if session_row else 0
        bounce_rate = total_bounces / total_sessions if total_sessions > 0 else None

        return {
            "pages": pages,
            "total_views": total_views,
            "total_unique_visitors": total_unique,
            "avg_pages_per_session": avg_pages,
            "avg_session_duration_ms": avg_session_dur,
            "bounce_rate": bounce_rate,
        }


async def fetch_referrers_from_mv(window_minutes: int | None, limit: int) -> List[Dict[str, Any]]:
    """Récupère les referrers depuis la vue matérialisée.

    Args:
        window_minutes: fenêtre temporelle en minutes (None = tout).
        limit: nombre maximal de referrers.

    Returns:
        Liste de dicts {referrer, count, unique_visitors}.
    """
    cutoff = _cutoff_date(window_minutes)

    query = """
        SELECT
            referrer_source AS referrer,
            SUM(visit_count)::BIGINT AS count,
            SUM(unique_visitors)::BIGINT AS unique_visitors
        FROM mv_analytics_referrer_daily
    """
    params: Dict[str, Any] = {}
    if cutoff is not None:
        query += " WHERE stat_date >= :cutoff"
        params["cutoff"] = cutoff
    query += " GROUP BY referrer_source ORDER BY SUM(visit_count) DESC LIMIT :limit"
    params["limit"] = limit

    async with get_async_session() as session:
        result = await session.execute(text(query), params)
        return [
            {
                "referrer": row["referrer"],
                "count": int(row["count"]),
                "unique_visitors": int(row["unique_visitors"]),
            }
            for row in result.mappings()
        ]


async def fetch_device_breakdown_from_mv(
    window_minutes: int | None,
) -> List[Dict[str, Any]]:
    """Récupère la répartition par appareil depuis la vue matérialisée.

    Args:
        window_minutes: fenêtre temporelle en minutes (None = tout).

    Returns:
        Liste de dicts {device_type, count, percentage}.
    """
    cutoff = _cutoff_date(window_minutes)

    query = """
        SELECT
            device AS device_type,
            SUM(unique_sessions)::BIGINT AS count
        FROM mv_analytics_device_daily
    """
    params: Dict[str, Any] = {}
    if cutoff is not None:
        query += " WHERE stat_date >= :cutoff"
        params["cutoff"] = cutoff
    query += " GROUP BY device ORDER BY SUM(unique_sessions) DESC"

    async with get_async_session() as session:
        result = await session.execute(text(query), params)
        rows = list(result.mappings())

    total = sum(int(r["count"]) for r in rows)
    return [
        {
            "device_type": row["device_type"],
            "count": int(row["count"]),
            "percentage": round((int(row["count"]) / total) * 100, 1) if total > 0 else 0,
        }
        for row in rows
    ]
