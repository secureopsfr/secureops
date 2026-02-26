"""Vérification robots.txt (roadmap §3.6).

Lit /robots.txt, extrait les directives Disallow et signale les routes
potentiellement sensibles (admin, api, backup, etc.).
"""

from dataclasses import dataclass

from app.config_loader import get_robots_txt_settings
from app.utils.http_fetch import get_with_client
from app.utils.url_helpers import build_url_with_path


@dataclass
class SensitiveRoute:
    """Route Disallow identifiée comme potentiellement sensible.

    Attributes:
        path (str): Chemin extrait de Disallow.
        pattern (str): Motif qui a déclenché la détection.
        severity (str): info, low, medium, high, critical.
    """

    path: str
    pattern: str
    severity: str


@dataclass
class RobotsTxtCheckResult:
    """Résultat de la vérification robots.txt.

    Attributes:
        disallow_paths (tuple[str, ...]): Chemins Disallow extraits.
        sensitive_routes (tuple[SensitiveRoute, ...]): Routes sensibles détectées.
        findings (tuple[str, ...]): Messages des findings.
        fetch_ok (bool): True si la requête a abouti.
    """

    disallow_paths: tuple[str, ...]
    sensitive_routes: tuple[SensitiveRoute, ...]
    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise pour l'événement SSE result."""
        sensitive_serialized = [{"path": r.path, "pattern": r.pattern, "severity": r.severity} for r in self.sensitive_routes]
        return {
            "disallow_paths": list(self.disallow_paths),
            "sensitive_routes": sensitive_serialized,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


def _extract_disallow_paths(content: str) -> list[str]:
    """Extrait les chemins des directives Disallow du contenu robots.txt.

    Ignore les commentaires (#), lignes vides. Normalise les chemins.

    Args:
        content: Contenu brut de robots.txt.

    Returns:
        list[str]: Liste des chemins Disallow uniques.
    """
    paths: list[str] = []
    seen: set[str] = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("disallow:"):
            path = line[9:].strip()
            if path and path != "/":
                if path not in seen:
                    seen.add(path)
                    paths.append(path)
    return paths


def _path_matches_sensitive(path: str, patterns: tuple[tuple[str, str], ...]) -> SensitiveRoute | None:
    """Vérifie si le chemin correspond à un motif sensible.

    Args:
        path: Chemin extrait (ex. /admin/).
        patterns: Tuple de (motif, severity). Motif = sous-chaîne à rechercher (insensible casse).

    Returns:
        SensitiveRoute si match, None sinon.
    """
    path_lower = path.lower()
    for pattern, severity in patterns:
        if pattern not in path_lower:
            continue
        # Exception : /api/public/ n'est pas considéré sensible (doc robots-txt.md)
        if pattern == "api" and "public" in path_lower:
            continue
        return SensitiveRoute(path=path, pattern=pattern, severity=severity)
    return None


async def run_robots_txt_checks(
    base_url: str,
    *,
    client,
) -> RobotsTxtCheckResult:
    """Lit robots.txt, extrait Disallow et signale les routes sensibles.

    Réutilise le client partagé pour une seule requête GET /robots.txt.

    Args:
        base_url: URL de base (ex. https://example.com/).
        client: Client httpx (issu de scan_client()).

    Returns:
        RobotsTxtCheckResult: Chemins extraits, routes sensibles et findings.
    """
    robots_url = build_url_with_path(base_url, "/robots.txt")
    response = await get_with_client(client, robots_url, follow_redirects=False)

    if response is None:
        return RobotsTxtCheckResult(
            disallow_paths=(),
            sensitive_routes=(),
            findings=("Impossible de récupérer robots.txt (connexion refusée ou timeout).",),
            fetch_ok=False,
        )

    if response.status_code != 200:
        return RobotsTxtCheckResult(
            disallow_paths=(),
            sensitive_routes=(),
            findings=(),
            fetch_ok=True,
        )

    content = response.text
    disallow_paths = _extract_disallow_paths(content)
    patterns = get_robots_txt_settings()

    sensitive: list[SensitiveRoute] = []
    findings: list[str] = []
    for path in disallow_paths:
        route = _path_matches_sensitive(path, patterns)
        if route is not None:
            sensitive.append(route)
            findings.append(f"Disallow: {path} (route potentiellement sensible : {route.pattern}). Vérifier la protection.")

    return RobotsTxtCheckResult(
        disallow_paths=tuple(disallow_paths),
        sensitive_routes=tuple(sensitive),
        findings=tuple(findings),
        fetch_ok=True,
    )
