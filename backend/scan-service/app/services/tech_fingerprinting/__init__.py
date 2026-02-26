"""Vérifications tech fingerprinting (roadmap §3.7)."""

from app.services.tech_fingerprinting.checks import (
    TechFingerprintingCheckResult,
    check_tech_fingerprinting_from_response,
)

__all__ = ["TechFingerprintingCheckResult", "check_tech_fingerprinting_from_response"]
