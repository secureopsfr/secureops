"""Fake destructive security checks used to simulate a richer pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding


@dataclass(frozen=True)
class DestructiveCheckResult:
    """Result of one destructive fake check execution."""

    check_name: str
    findings: tuple[Finding, ...]


def _seed(url: str, salt: int) -> int:
    return (sum(ord(ch) for ch in url) + salt) % 11


def _finding(
    *,
    slug: str,
    category: str,
    title: str,
    severity: str,
    evidence: str,
) -> Finding:
    return Finding(
        id=slug,
        category=category,
        title=title,
        severity=severity,
        evidence=evidence,
        recommendation=get_recommendation(slug),
        references=get_references(slug),
    )


def run_destructive_prechecks_probe(url: str) -> DestructiveCheckResult:
    """Simulate prechecks before destructive operations."""
    findings: list[Finding] = []
    if _seed(url, 31) in {0, 4}:
        findings.append(
            _finding(
                slug="destructive-prechecks-gaps-suspected",
                category="destructive_prechecks",
                title="Destructive prechecks appear incomplete",
                severity="high",
                evidence="A simulated destructive plan appears to proceed without all expected preconditions.",
            )
        )
    return DestructiveCheckResult(check_name="destructive_prechecks", findings=tuple(findings))


def run_destructive_safety_probe(url: str) -> DestructiveCheckResult:
    """Simulate safety controls for destructive mode."""
    findings: list[Finding] = []
    if _seed(url, 43) in {3, 8}:
        findings.append(
            _finding(
                slug="destructive-safety-controls-weak-suspected",
                category="destructive_safety",
                title="Destructive safety controls may be insufficient",
                severity="critical",
                evidence="A simulated destructive execution indicates weak emergency-stop or rollback controls.",
            )
        )
    return DestructiveCheckResult(check_name="destructive_safety", findings=tuple(findings))


DESTRUCTIVE_STEPS = (
    ("destructive_prechecks", run_destructive_prechecks_probe),
    ("destructive_safety", run_destructive_safety_probe),
)
