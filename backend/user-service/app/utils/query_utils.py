"""Utilitaires pour les requêtes SQLAlchemy."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import ColumnElement
from sqlalchemy.sql import Select


def apply_url_filter(stmt: Select[Any], url_column: ColumnElement[str], url: Optional[str]) -> Select[Any]:
    """Ajoute un filtre par URL à une requête SELECT si url est fourni."""
    if url:
        return stmt.where(url_column == url)
    return stmt


def apply_scan_type_filter(
    stmt: Select[Any],
    scan_type_column: ColumnElement[str],
    scan_type: Optional[str],
) -> Select[Any]:
    """Ajoute un filtre par type de scan (frontend, backend, both) si fourni."""
    if scan_type and scan_type in ("frontend", "backend", "both", "custom"):
        return stmt.where(scan_type_column == scan_type)
    return stmt


def apply_scan_mode_filter(
    stmt: Select[Any],
    scan_mode_column: ColumnElement[str],
    scan_mode: Optional[str],
) -> Select[Any]:
    """Ajoute un filtre par mode de scan (passive, intrusive, destructive, custom)."""
    if scan_mode and scan_mode in ("passive", "intrusive", "destructive", "custom"):
        return stmt.where(scan_mode_column == scan_mode)
    return stmt


def apply_date_filter(
    stmt: Select[Any],
    date_column: ColumnElement[datetime],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> Select[Any]:
    """Ajoute un filtre par plage de dates si fourni."""
    if date_from is not None:
        stmt = stmt.where(date_column >= date_from)
    if date_to is not None:
        stmt = stmt.where(date_column <= date_to)
    return stmt
