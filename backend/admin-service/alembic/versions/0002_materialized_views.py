"""Ajout des vues matérialisées pour les agrégations analytics.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-17

Crée 5 vues matérialisées pour pré-calculer les KPIs analytics
et éviter les full-table scans à chaque requête du dashboard admin.
Les vues sont rafraîchies toutes les heures via un scheduler asyncio.
"""

from typing import Optional, Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Optional[str] = "0001"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    """Crée les vues matérialisées analytics."""
    # ── 1. Stats globales quotidiennes ──
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analytics_daily_stats AS
        SELECT
            DATE(created_at AT TIME ZONE 'UTC') AS stat_date,
            COUNT(*) FILTER (WHERE event_type = 'page_view') AS total_page_views,
            COUNT(DISTINCT session_id) FILTER (WHERE event_type = 'page_view') AS unique_sessions,
            COUNT(*) AS total_events
        FROM analytics_events
        GROUP BY DATE(created_at AT TIME ZONE 'UTC')
    """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_stats_date " "ON mv_analytics_daily_stats (stat_date)")

    # ── 2. Stats par page quotidiennes ──
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analytics_page_daily AS
        SELECT
            DATE(created_at AT TIME ZONE 'UTC') AS stat_date,
            page,
            COUNT(*) FILTER (WHERE event_type = 'page_view') AS views,
            COUNT(DISTINCT session_id) FILTER (WHERE event_type = 'page_view') AS unique_visitors,
            AVG(duration_ms) FILTER (WHERE event_type = 'page_exit') AS avg_duration_ms,
            COUNT(duration_ms) FILTER (WHERE event_type = 'page_exit') AS duration_count
        FROM analytics_events
        GROUP BY DATE(created_at AT TIME ZONE 'UTC'), page
    """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_page_daily_date_page " "ON mv_analytics_page_daily (stat_date, page)")

    # ── 3. Stats par referrer quotidiennes ──
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analytics_referrer_daily AS
        SELECT
            DATE(created_at AT TIME ZONE 'UTC') AS stat_date,
            COALESCE(referrer, 'direct') AS referrer_source,
            COUNT(*) AS visit_count,
            COUNT(DISTINCT session_id) AS unique_visitors
        FROM analytics_events
        WHERE event_type = 'page_view'
        GROUP BY DATE(created_at AT TIME ZONE 'UTC'), COALESCE(referrer, 'direct')
    """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_referrer_daily_date_ref " "ON mv_analytics_referrer_daily (stat_date, referrer_source)")

    # ── 4. Stats par appareil quotidiennes ──
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analytics_device_daily AS
        SELECT
            DATE(created_at AT TIME ZONE 'UTC') AS stat_date,
            COALESCE(device_type, 'unknown') AS device,
            COUNT(DISTINCT session_id) AS unique_sessions
        FROM analytics_events
        WHERE event_type = 'page_view'
        GROUP BY DATE(created_at AT TIME ZONE 'UTC'), COALESCE(device_type, 'unknown')
    """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_device_daily_date_dev " "ON mv_analytics_device_daily (stat_date, device)")

    # ── 5. Stats géographiques quotidiennes ──
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analytics_geo_daily AS
        SELECT
            DATE(created_at AT TIME ZONE 'UTC') AS stat_date,
            COALESCE(country, '??') AS country_code,
            COALESCE(region, 'Inconnu') AS region_name,
            COALESCE(city, 'Inconnue') AS city_name,
            COUNT(DISTINCT session_id) AS unique_sessions
        FROM analytics_events
        WHERE event_type = 'page_view'
        GROUP BY
            DATE(created_at AT TIME ZONE 'UTC'),
            COALESCE(country, '??'),
            COALESCE(region, 'Inconnu'),
            COALESCE(city, 'Inconnue')
    """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_geo_daily_date_geo " "ON mv_analytics_geo_daily (stat_date, country_code, region_name, city_name)"
    )

    # ── 6. Stats par session (pour bounce rate, durée, pages/session) ──
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analytics_session_stats AS
        SELECT
            session_id,
            DATE(MIN(created_at) AT TIME ZONE 'UTC') AS session_date,
            COUNT(*) FILTER (WHERE event_type = 'page_view') AS page_view_count,
            COUNT(DISTINCT page) FILTER (WHERE event_type = 'page_view') AS distinct_pages,
            SUM(duration_ms) FILTER (WHERE event_type = 'page_exit') AS total_duration_ms
        FROM analytics_events
        GROUP BY session_id
    """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_session_stats_sid " "ON mv_analytics_session_stats (session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_mv_session_stats_date " "ON mv_analytics_session_stats (session_date)")


def downgrade() -> None:
    """Supprime les vues matérialisées."""
    views = [
        "mv_analytics_session_stats",
        "mv_analytics_geo_daily",
        "mv_analytics_device_daily",
        "mv_analytics_referrer_daily",
        "mv_analytics_page_daily",
        "mv_analytics_daily_stats",
    ]
    for view in views:
        op.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view} CASCADE")
