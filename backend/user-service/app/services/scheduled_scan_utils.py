"""Utilitaires pour le calcul des dates d'exécution des scans planifiés."""

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil.relativedelta import relativedelta


def _get_ref_in_tz(from_dt: datetime, tz_name: Optional[str]) -> datetime:
    """Convertit from_dt en datetime dans le fuseau de l'utilisateur (ou UTC si null)."""
    if from_dt.tzinfo is None:
        from_dt = from_dt.replace(tzinfo=timezone.utc)
    if tz_name and tz_name != "UTC":
        try:
            tz = ZoneInfo(tz_name)
            return from_dt.astimezone(tz)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Fuseau horaire invalide: {tz_name}") from exc
    return from_dt


def _to_utc(local_dt: datetime, tz_name: Optional[str]) -> datetime:
    """Convertit un datetime local (dans tz_name) en UTC."""
    if tz_name and tz_name != "UTC":
        try:
            tz = ZoneInfo(tz_name)
            if local_dt.tzinfo is None:
                local_dt = local_dt.replace(tzinfo=tz)
            return local_dt.astimezone(timezone.utc)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Fuseau horaire invalide: {tz_name}") from exc
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=timezone.utc)
    return local_dt


def _compute_next_run_daily(ref_local: datetime, schedule_hour: int, schedule_minute: int, tz_name: Optional[str]) -> datetime:
    """Prochaine exécution pour fréquence quotidienne."""
    next_run = ref_local.replace(hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)
    if next_run <= ref_local:
        next_run += relativedelta(days=1)
    return _to_utc(next_run, tz_name)


def _compute_next_run_weekly(
    ref_local: datetime,
    schedule_hour: int,
    schedule_minute: int,
    schedule_day_of_week: Optional[int],
    tz_name: Optional[str],
) -> datetime:
    """Prochaine exécution pour fréquence hebdomadaire."""
    dow = schedule_day_of_week if schedule_day_of_week is not None else ref_local.weekday()
    next_run = ref_local.replace(hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)
    days_ahead = (dow - ref_local.weekday() + 7) % 7
    if days_ahead == 0 and next_run <= ref_local:
        days_ahead = 7
    next_run += relativedelta(days=days_ahead)
    return _to_utc(next_run, tz_name)


def _compute_next_run_monthly(
    ref_local: datetime,
    schedule_hour: int,
    schedule_minute: int,
    schedule_day_of_month: Optional[int],
    tz_name: Optional[str],
) -> datetime:
    """Prochaine exécution pour fréquence mensuelle."""
    dom = schedule_day_of_month if schedule_day_of_month is not None else ref_local.day
    dom = min(max(dom, 1), 28)
    next_run = ref_local.replace(day=1, hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)
    next_run += relativedelta(months=1)
    try:
        next_run = next_run.replace(day=dom)
    except ValueError:
        next_run = next_run.replace(day=28)
    if next_run <= ref_local:
        next_run += relativedelta(months=1)
        try:
            next_run = next_run.replace(day=dom)
        except ValueError:
            next_run = next_run.replace(day=28)
    return _to_utc(next_run, tz_name)


def compute_next_run(
    from_dt: datetime,
    frequency: str,
    schedule_hour: int = 2,
    schedule_minute: int = 0,
    schedule_day_of_week: Optional[int] = None,
    schedule_day_of_month: Optional[int] = None,
    timezone_name: Optional[str] = None,
) -> datetime:
    """Calcule la prochaine date d'exécution selon la fréquence et les paramètres.

    schedule_hour et schedule_minute sont interprétés dans le fuseau de l'utilisateur
    (timezone_name, ex. Europe/Paris). Si timezone_name est null, on utilise UTC.

    Args:
        from_dt: Date/heure de référence (généralement maintenant ou last run, en UTC).
        frequency: daily, weekly ou monthly.
        schedule_hour: Heure d'exécution (0-23) dans le fuseau utilisateur.
        schedule_minute: Minute d'exécution (0-59).
        schedule_day_of_week: Jour de la semaine pour weekly (0=lundi, 6=dimanche).
        schedule_day_of_month: Jour du mois pour monthly (1-31).
        timezone_name: Fuseau utilisateur (ex. Europe/Paris). Si null, UTC.

    Returns:
        datetime: Prochaine date d'exécution (timezone-aware UTC).
    """
    if from_dt.tzinfo is None:
        from_dt = from_dt.replace(tzinfo=timezone.utc)
    ref_local = _get_ref_in_tz(from_dt, timezone_name)

    if frequency == "weekly":
        return _compute_next_run_weekly(ref_local, schedule_hour, schedule_minute, schedule_day_of_week, timezone_name)
    if frequency == "monthly":
        return _compute_next_run_monthly(ref_local, schedule_hour, schedule_minute, schedule_day_of_month, timezone_name)
    return _compute_next_run_daily(ref_local, schedule_hour, schedule_minute, timezone_name)


def compute_initial_next_run(
    frequency: str,
    schedule_hour: int = 2,
    schedule_minute: int = 0,
    schedule_day_of_week: Optional[int] = None,
    schedule_day_of_month: Optional[int] = None,
    timezone_name: Optional[str] = None,
) -> datetime:
    """Calcule la première date d'exécution pour un nouveau scan planifié.

    Args:
        frequency: daily, weekly ou monthly.
        schedule_hour: Heure d'exécution (dans le fuseau utilisateur).
        schedule_minute: Minute d'exécution.
        schedule_day_of_week: Jour de la semaine (weekly).
        schedule_day_of_month: Jour du mois (monthly).
        timezone_name: Fuseau utilisateur (ex. Europe/Paris). Si null, UTC.

    Returns:
        datetime: Première date d'exécution (UTC).
    """
    now = datetime.now(timezone.utc)
    return compute_next_run(
        from_dt=now,
        frequency=frequency,
        schedule_hour=schedule_hour,
        schedule_minute=schedule_minute,
        schedule_day_of_week=schedule_day_of_week,
        schedule_day_of_month=schedule_day_of_month,
        timezone_name=timezone_name,
    )
