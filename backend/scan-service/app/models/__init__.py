"""Modèles partagés du scan-service."""

from app.models.check_result_base import CheckResultProtocol
from app.models.finding import Finding
from app.models.scan_result import ScanResult

__all__ = ["CheckResultProtocol", "Finding", "ScanResult"]
