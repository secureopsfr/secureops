"""Smoke tests sur la présence/structure des migrations Alembic."""

from pathlib import Path


def test_alembic_files_exist() -> None:
    """Vérifie que la structure Alembic admin-service existe."""
    root = Path(__file__).resolve().parents[1]
    assert (root / "alembic.ini").exists()
    assert (root / "alembic" / "env.py").exists()
    assert (root / "alembic" / "versions").exists()


def test_alembic_has_revision_files() -> None:
    """Vérifie qu'au moins une migration est présente."""
    root = Path(__file__).resolve().parents[1]
    version_files = list((root / "alembic" / "versions").glob("*.py"))
    assert len(version_files) > 0
