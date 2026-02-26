"""Fixtures partagées pour les tests du scan-service."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


def parse_sse_events(response) -> list[tuple[str, dict]]:
    """Parse le corps SSE en liste de (event, data).

    Args:
        response: Réponse HTTP avec body text (stream SSE).

    Returns:
        list[tuple[str, dict]]: Liste de (event_type, data_dict).
    """
    events = []
    for block in response.text.strip().split("\n\n"):
        if not block:
            continue
        event, data = "message", {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                event = line[7:].strip()
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        events.append((event, data))
    return events


@pytest.fixture()
def client() -> TestClient:
    """Client de test FastAPI pour les routes."""
    return TestClient(app)
