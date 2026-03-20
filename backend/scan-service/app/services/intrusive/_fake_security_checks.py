"""Fake intrusive security probes used to bootstrap the pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from app.catalogue.recommendations import get_recommendation, get_references
from app.models.finding import Finding


@dataclass(frozen=True)
class IntrusiveCheckResult:
    """Result of one intrusive probe execution."""

    check_name: str
    findings: tuple[Finding, ...]


def _seed(url: str, salt: int) -> int:
    return (sum(ord(ch) for ch in url) + salt) % 7


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


def run_reflected_xss_probe(url: str) -> IntrusiveCheckResult:
    """Simulate a reflected XSS probe and return potential findings."""
    findings: list[Finding] = []
    if _seed(url, 11) in {1, 4}:
        findings.append(
            _finding(
                slug="intrusive-reflected-xss-suspected",
                category="intrusive_reflected_xss",
                title="Reflected payload observed in response",
                severity="high",
                evidence="A controlled payload marker appeared in the reflected output.",
            )
        )
    return IntrusiveCheckResult(check_name="intrusive_reflected_xss", findings=tuple(findings))


def run_sql_injection_probe(url: str) -> IntrusiveCheckResult:
    """Simulate a SQL injection probe and return potential findings."""
    findings: list[Finding] = []
    if _seed(url, 23) in {0, 3}:
        findings.append(
            _finding(
                slug="intrusive-sqli-suspected",
                category="intrusive_sql_injection",
                title="Potential SQL injection behavior",
                severity="critical",
                evidence="Response timing or error pattern changed after SQL meta-character payload.",
            )
        )
    return IntrusiveCheckResult(check_name="intrusive_sql_injection", findings=tuple(findings))


def run_authz_bypass_probe(url: str) -> IntrusiveCheckResult:
    """Simulate an authorization bypass probe and return potential findings."""
    findings: list[Finding] = []
    if _seed(url, 37) in {2, 5}:
        findings.append(
            _finding(
                slug="intrusive-authz-bypass-suspected",
                category="intrusive_authz_bypass",
                title="Authorization bypass behavior suspected",
                severity="medium",
                evidence="A protected path returned an unexpected success status to crafted request.",
            )
        )
    return IntrusiveCheckResult(check_name="intrusive_authz_bypass", findings=tuple(findings))


INTRUSIVE_STEPS = (
    ("intrusive_reflected_xss", run_reflected_xss_probe),
    ("intrusive_sql_injection", run_sql_injection_probe),
    ("intrusive_authz_bypass", run_authz_bypass_probe),
)
