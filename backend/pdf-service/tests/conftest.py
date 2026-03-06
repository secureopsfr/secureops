"""Fixtures partagées pour les tests du pdf-service."""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _ensure_database_url() -> None:
    """Assure que DATABASE_URL est défini pour le chargement de la config (non utilisée par le service)."""
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5432/template_db"


@pytest.fixture()
def client() -> TestClient:
    """Client de test FastAPI pour les routes."""
    return TestClient(app)
