"""Normalisation des résultats PathCheck (exposed_files, directory_listing) en list[Finding].

Le get_exposed_files_severity_upgrade() est appelé une seule fois avant la boucle
pour éviter des lectures de config répétées par finding.
"""

from collections.abc import Callable

from app.catalogue.owasp import get_owasp_categories
from app.catalogue.recommendations import get_recommendation, get_references
from app.config_loader import get_exposed_files_severity_upgrade
from app.models.finding import Finding
from app.services.passive.both.path_checks.core import PathCheckResult, PathFinding


def _finding(slug: str, category: str, title: str, severity: str, evidence: str) -> Finding:
    sev = severity.lower() if severity else "medium"
    return Finding(
        id=slug,
        category=category,
        title=title,
        severity=sev,
        evidence=evidence,
        recommendation=get_recommendation(slug),
        references=get_references(slug),
        owasp_categories=get_owasp_categories(slug),
    )


def _path_to_slug(path: str, category: str) -> str:
    p = path.rstrip("/").lower().replace(".", "-").replace("/", "-").strip("-") or "root"
    return f"{category}-{p}"


def _path_severity(path: str, config_severity: str, severity_upgrades: list[str]) -> str:
    """Applique upgrade : chemins dans severity_upgrade (settings.yml) = critical.

    severity_upgrades est passé en paramètre pour éviter un appel config par finding.
    """
    path_norm = path.rstrip("/") or "/"
    for up in severity_upgrades:
        up_norm = up.rstrip("/") or "/"
        if path_norm == up_norm or path_norm.endswith("/" + up_norm.lstrip("/")):
            return "critical"
    return config_severity.lower()


def _normalize_path_check_result(
    result: PathCheckResult,
    category: str,
    title_fn: Callable[[PathFinding], str],
    severity_fn: Callable[[PathFinding], str],
) -> list[Finding]:
    findings: list[Finding] = []
    for pf in result.exposed:
        slug = _path_to_slug(pf.path, category)
        title = title_fn(pf)
        severity = severity_fn(pf)
        findings.append(_finding(slug, category, title, severity, pf.message))
    return findings


def normalize_exposed_files(result: PathCheckResult) -> list[Finding]:
    """Convertit PathCheckResult (exposed_files) en list[Finding]."""
    severity_upgrades = get_exposed_files_severity_upgrade()
    return _normalize_path_check_result(
        result,
        "exposed_files",
        title_fn=lambda pf: f"Fichier exposé : {pf.path}",
        severity_fn=lambda pf: _path_severity(pf.path, pf.severity, severity_upgrades),
    )


def normalize_directory_listing(result: PathCheckResult) -> list[Finding]:
    """Convertit PathCheckResult (directory_listing) en list[Finding].

    Gère exposed (listing 200) et exposed_403 (chemins sensibles retournant 403).
    """
    findings = _normalize_path_check_result(
        result,
        "directory_listing",
        title_fn=lambda pf: f"Directory listing : {pf.path}",
        severity_fn=lambda pf: pf.severity.lower(),
    )
    for pf in result.exposed_403:
        findings.append(
            _finding(
                "directory_listing-sensitive-403",
                "directory_listing",
                f"Répertoire sensible révélé : {pf.path}",
                pf.severity.lower(),
                pf.message,
            )
        )
    return findings
