"""Destructive scan pipeline (fake implementation for V1)."""

from app.services.destructive.multi_scan_orchestrator import run_multi_scan
from app.services.destructive.scan_runner import run_scan_to_result

__all__ = ["run_scan_to_result", "run_multi_scan"]
