"""Service d'agrégation des scans pour KPIs et graphique d'évolution."""

import logging
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import Scan
from app.models.scheduled_scan import ScheduledScan
from app.services.scan_repository import count_user_scans
from app.utils.query_utils import apply_date_filter, apply_scan_type_filter, apply_url_filter

logger = logging.getLogger(__name__)


def _parse_optional_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse une chaîne ISO en datetime timezone-aware."""
    if not value or not value.strip():
        return None
    try:
        s = value.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _count_critical_findings(findings: list[dict[str, Any]]) -> int:
    """Compte les findings avec severity critical."""
    if not findings:
        return 0
    return sum(1 for f in findings if str(f.get("severity", "")).lower() == "critical")


def _count_all_findings(findings: list[dict[str, Any]]) -> int:
    """Compte le nombre total de findings."""
    return len(findings) if findings else 0


async def get_scan_overview(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: Optional[str] = None,
    scan_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> dict[str, Any]:
    """Calcule les KPIs et les données du graphique pour la vue d'ensemble scanner.

    Tous les calculs respectent les filtres (url, scan_type, date_from, date_to).

    Returns:
        dict avec:
        - kpis: scans_in_period, total_scans, avg_score, critical_findings_count,
                active_scheduled_count, last_scan_at
        - chart_data: liste de { ts, scans, score, anomalies } par jour
    """
    base_stmt = select(Scan).where(Scan.user_id == user_id)
    base_stmt = apply_url_filter(base_stmt, Scan.url, url)
    base_stmt = apply_scan_type_filter(base_stmt, Scan.scan_type, scan_type)
    stmt_filtered = apply_date_filter(base_stmt, Scan.timestamp, date_from, date_to)

    total_scans = await count_user_scans(session, user_id, url=url, scan_type=scan_type, date_from=None, date_to=None)
    scans_in_period = await count_user_scans(session, user_id, url=url, scan_type=scan_type, date_from=date_from, date_to=date_to)

    filtered_scans_stmt = stmt_filtered.order_by(Scan.created_at.desc()).limit(5000)
    result_filtered = await session.execute(filtered_scans_stmt)
    scans_filtered = list(result_filtered.scalars().all())

    scores = [s.score for s in scans_filtered if s.score is not None]
    avg_score = round(sum(scores) / len(scores)) if scores else None

    critical_count = 0
    for s in scans_filtered:
        findings = s.findings_json or []
        critical_count += _count_critical_findings(findings)

    last_scan_at = None
    if scans_filtered:
        last_scan_at = scans_filtered[0].timestamp

    active_scheduled = await _count_enabled_scheduled_scans(session, user_id, url=url, scan_type=scan_type)

    chart_data = _build_chart_data(scans_filtered, date_from, date_to)

    return {
        "kpis": {
            "scans_in_period": scans_in_period,
            "total_scans": total_scans,
            "avg_score": avg_score,
            "critical_findings_count": critical_count,
            "active_scheduled_count": active_scheduled,
            "last_scan_at": last_scan_at.isoformat() if last_scan_at else None,
        },
        "chart_data": chart_data,
    }


async def _count_enabled_scheduled_scans(
    session: AsyncSession,
    user_id: uuid.UUID,
    url: Optional[str] = None,
    scan_type: Optional[str] = None,
) -> int:
    """Compte les scans planifiés actifs (enabled=True)."""
    stmt = select(func.count(ScheduledScan.id)).where(ScheduledScan.user_id == user_id, ScheduledScan.enabled == True)  # noqa: E712
    stmt = apply_url_filter(stmt, ScheduledScan.url, url)
    stmt = apply_scan_type_filter(stmt, ScheduledScan.scan_type, scan_type)
    result = await session.execute(stmt)
    return result.scalar() or 0


def _build_chart_data(
    scans: list,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> list[dict[str, Any]]:
    """Agrège les scans par jour pour le graphique."""
    by_day: dict[str, list] = defaultdict(list)
    for s in scans:
        ts = s.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        day_key = ts.strftime("%Y-%m-%d")
        by_day[day_key].append(s)

    if not by_day:
        return []

    if not date_from or not date_to:
        keys = sorted(by_day.keys())
        date_from = datetime.fromisoformat(keys[0] + "T00:00:00").replace(tzinfo=UTC)
        date_to = datetime.fromisoformat(keys[-1] + "T23:59:59").replace(tzinfo=UTC)

    points = []
    current = date_from.date()
    end_date = date_to.date()
    while current <= end_date:
        day_key = current.isoformat()
        day_scans = by_day.get(day_key, [])
        scans_count = len(day_scans)
        scores = [s.score for s in day_scans if s.score is not None]
        avg = round(sum(scores) / len(scores)) if scores else 0
        anomalies = sum(_count_all_findings(s.findings_json or []) for s in day_scans)

        ts_label = current.strftime("%d/%m")
        points.append(
            {
                "ts": ts_label,
                "scans": scans_count,
                "score": avg,
                "anomalies": anomalies,
            }
        )
        current += timedelta(days=1)

    return points
