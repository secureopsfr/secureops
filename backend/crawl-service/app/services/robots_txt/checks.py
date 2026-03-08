"""Vérification robots.txt (roadmap §3.6, §5.1.6).

Lit /robots.txt, extrait les directives Disallow, Allow, Sitemap, Crawl-delay
et signale les routes potentiellement sensibles (admin, api, backup, etc.).
"""

from dataclasses import dataclass

from app.config_loader import get_robots_txt_settings
from app.constants import MSG_ROBOTS_TXT_UNAVAILABLE
from app.utils.http_fetch import get_with_client
from app.utils.url_helpers import build_url_with_path


@dataclass
class SensitiveRoute:
    """Route Disallow identifiée comme potentiellement sensible."""

    path: str
    pattern: str
    severity: str


@dataclass
class RobotsTxtCheckResult:
    """Résultat de la vérification robots.txt."""

    disallow_paths: tuple[str, ...]
    allow_paths: tuple[str, ...]
    sensitive_routes: tuple[SensitiveRoute, ...]
    findings: tuple[str, ...]
    fetch_ok: bool
    found: bool
    crawl_delay: int | None
    sitemap_urls: tuple[str, ...]

    def to_dict(self) -> dict:
        """Sérialise pour l'événement SSE result."""
        sensitive_serialized = [{"path": r.path, "pattern": r.pattern, "severity": r.severity} for r in self.sensitive_routes]
        return {
            "disallow_paths": list(self.disallow_paths),
            "allow_paths": list(self.allow_paths),
            "sensitive_routes": sensitive_serialized,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
            "crawl_delay": self.crawl_delay,
            "sitemap_urls": list(self.sitemap_urls),
        }


def _extract_disallow_paths(content: str) -> list[str]:
    """Extrait les chemins des directives Disallow du contenu robots.txt."""
    paths: list[str] = []
    seen: set[str] = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("disallow:"):
            path = line[9:].strip()
            if path and path != "/" and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _extract_allow_paths(content: str) -> list[str]:
    """Extrait les chemins des directives Allow du contenu robots.txt."""
    paths: list[str] = []
    seen: set[str] = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("allow:"):
            path = line[6:].strip()
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _extract_sitemap_urls(content: str) -> list[str]:
    """Extrait les URLs des directives Sitemap: du contenu robots.txt."""
    urls: list[str] = []
    seen: set[str] = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("sitemap:"):
            url = line[8:].strip()
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def _extract_crawl_delay(content: str) -> int | None:
    """Extrait la valeur Crawl-delay (non standard) du contenu robots.txt."""
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("crawl-delay:"):
            try:
                val = int(line[12:].strip().split()[0])
                return val if val >= 0 else None
            except (ValueError, IndexError):
                return None
    return None


def _path_matches_sensitive(path: str, patterns: tuple[tuple[str, str], ...]) -> SensitiveRoute | None:
    """Vérifie si le chemin correspond à un motif sensible."""
    path_lower = path.lower()
    for pattern, severity in patterns:
        if pattern not in path_lower or (pattern == "api" and "public" in path_lower):
            continue
        return SensitiveRoute(path=path, pattern=pattern, severity=severity)
    return None


async def run_robots_txt_checks(
    base_url: str,
    *,
    client,
) -> RobotsTxtCheckResult:
    """Lit robots.txt, extrait Disallow et signale les routes sensibles.

    Args:
        base_url: URL de base (ex. https://example.com/).
        client: Client httpx (issu de scan_client()).

    Returns:
        RobotsTxtCheckResult: Chemins extraits, routes sensibles et findings.
    """
    robots_url = build_url_with_path(base_url, "/robots.txt")
    response = await get_with_client(client, robots_url, follow_redirects=True)

    if response is None:
        return RobotsTxtCheckResult(
            disallow_paths=(),
            allow_paths=(),
            sensitive_routes=(),
            findings=(MSG_ROBOTS_TXT_UNAVAILABLE,),
            fetch_ok=False,
            found=False,
            crawl_delay=None,
            sitemap_urls=(),
        )

    if response.status_code != 200:
        return RobotsTxtCheckResult(
            disallow_paths=(),
            allow_paths=(),
            sensitive_routes=(),
            findings=(),
            fetch_ok=True,
            found=False,
            crawl_delay=None,
            sitemap_urls=(),
        )

    content = response.text
    disallow_paths = _extract_disallow_paths(content)
    allow_paths = _extract_allow_paths(content)
    sitemap_urls = _extract_sitemap_urls(content)
    crawl_delay = _extract_crawl_delay(content)
    patterns = get_robots_txt_settings()

    sensitive: list[SensitiveRoute] = []
    findings: list[str] = []
    for path in disallow_paths:
        route = _path_matches_sensitive(path, patterns)
        if route is not None:
            sensitive.append(route)
            findings.append(f"Disallow: {path} (route potentiellement sensible : {route.pattern}). Vérifier la protection.")

    if crawl_delay is not None:
        findings.append(f"Crawl-delay: {crawl_delay}s (directive non standard, certains moteurs l'ignorent).")

    return RobotsTxtCheckResult(
        disallow_paths=tuple(disallow_paths),
        allow_paths=tuple(allow_paths),
        sensitive_routes=tuple(sensitive),
        findings=tuple(findings),
        fetch_ok=True,
        found=True,
        crawl_delay=crawl_delay,
        sitemap_urls=tuple(sitemap_urls),
    )
