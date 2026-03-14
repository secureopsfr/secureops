"""Fake custom security checks used to simulate a richer pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding


@dataclass(frozen=True)
class CustomCheckResult:
    """Result of one custom fake check execution."""

    check_name: str
    findings: tuple[Finding, ...]


def _seed(url: str, salt: int) -> int:
    return (sum(ord(ch) for ch in url) + salt) % 9


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


def run_custom_strategy_probe(url: str) -> CustomCheckResult:
    """Simulate strategy consistency checks for custom mode."""
    findings: list[Finding] = []
    if _seed(url, 17) in {2, 6}:
        findings.append(
            _finding(
                slug="custom-strategy-drift-suspected",
                category="custom_strategy",
                title="Custom strategy drift suspected",
                severity="medium",
                evidence="The simulated custom scenario indicates inconsistent guard conditions between runs.",
            )
        )
    return CustomCheckResult(check_name="custom_strategy", findings=tuple(findings))


def run_custom_guardrails_probe(url: str) -> CustomCheckResult:
    """Simulate guardrail checks for custom mode."""
    findings: list[Finding] = []
    if _seed(url, 29) in {1, 5}:
        findings.append(
            _finding(
                slug="custom-guardrails-weak-suspected",
                category="custom_guardrails",
                title="Custom execution guardrails seem weak",
                severity="high",
                evidence="A simulated custom operation appears to run without strict blast-radius constraints.",
            )
        )
    return CustomCheckResult(check_name="custom_guardrails", findings=tuple(findings))


CUSTOM_STEPS = (
    ("custom_strategy", run_custom_strategy_probe),
    ("custom_guardrails", run_custom_guardrails_probe),
)
