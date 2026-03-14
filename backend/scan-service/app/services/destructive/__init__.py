"""Destructive scan pipeline (fake implementation for V1)."""

from app.services.destructive.multi_scan_orchestrator import run_multi_scan
from app.services.destructive.scan_stream import scan_stream_generator

__all__ = ["scan_stream_generator", "run_multi_scan"]
