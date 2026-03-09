"""Utilitaires pour les requêtes SQLAlchemy."""

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
    """Ajoute un filtre par type de scan (frontend, backend, custom) si fourni."""
    if scan_type and scan_type in ("frontend", "backend", "custom"):
        return stmt.where(scan_type_column == scan_type)
    return stmt
