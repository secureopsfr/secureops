"""Tests unitaires des helpers de métriques proxy."""

from app.services.proxy.metrics import build_endpoint, extract_route


def test_build_endpoint_joins_prefix_and_path() -> None:
    """Doit construire endpoint avec prefix + path."""
    assert build_endpoint("scan", "/api/scan") == "/scan/api/scan"


def test_extract_route_stops_on_numeric_segment() -> None:
    """Doit supprimer les segments dynamiques numériques."""
    assert extract_route("/scan/api/results/12345") == "/scan/api/results"


def test_extract_route_stops_on_uuid_segment() -> None:
    """Doit supprimer les UUID en fin de route."""
    endpoint = "/user/api/scans/550e8400-e29b-41d4-a716-446655440000"
    assert extract_route(endpoint) == "/user/api/scans"
