"""Chargement de configuration pour Scan Service."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings, load_yaml

settings = create_simple_settings("scan-service", default_port=8012, caller_file=__file__)


@lru_cache(maxsize=1)
def _load_settings_yml() -> dict:
    """Charge config/settings.yml une fois (mis en cache).

    Returns:
        dict: Contenu complet du fichier YAML.
    """
    root = Path(__file__).resolve().parents[1]
    return load_yaml(root / "config" / "settings.yml")


@dataclass(frozen=True)
class SsrfSettings:
    """Configuration de la protection SSRF (hostnames, plages IP, timeout DNS)."""

    dns_timeout: float
    blocked_hostnames: frozenset[str]
    blocked_ipv4_networks: tuple[str, ...]
    blocked_ipv6_networks: tuple[str, ...]


# Valeurs par défaut SSRF si la section est absente du YAML.
_DEFAULT_SSRF_HOSTNAMES = ("localhost", "localhost.", "127.0.0.1", "::1", "[::1]", "0.0.0.0")
_DEFAULT_SSRF_IPV4 = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16", "127.0.0.0/8", "0.0.0.0/8")
_DEFAULT_SSRF_IPV6 = ("::1/128", "fe80::/10", "fc00::/7")


@lru_cache(maxsize=1)
def get_ssrf_settings() -> SsrfSettings:
    """Charge la section SSRF depuis config/settings.yml (mis en cache).

    Returns:
        SsrfSettings: hostnames et plages IP bloqués.
    """
    data = _load_settings_yml()
    ssrf = data.get("ssrf") or {}
    dns_timeout = float(ssrf.get("dns_timeout", 5.0))
    hostnames = ssrf.get("blocked_hostnames") or _DEFAULT_SSRF_HOSTNAMES
    ipv4 = ssrf.get("blocked_ipv4_networks") or _DEFAULT_SSRF_IPV4
    ipv6 = ssrf.get("blocked_ipv6_networks") or _DEFAULT_SSRF_IPV6
    return SsrfSettings(
        dns_timeout=dns_timeout,
        blocked_hostnames=frozenset(str(h) for h in hostnames),
        blocked_ipv4_networks=tuple(str(n) for n in ipv4),
        blocked_ipv6_networks=tuple(str(n) for n in ipv6),
    )


@dataclass(frozen=True)
class UrlValidationSettings:
    """Configuration de la validation d'URL (schémas, ports, longueur max)."""

    max_url_length: int
    allowed_schemes: tuple[str, ...]
    allowed_ports: tuple[int, ...]


_DEFAULT_URL_MAX_LENGTH = 2048
_DEFAULT_URL_SCHEMES = ("http", "https")
_DEFAULT_URL_PORTS = (80, 443)


@lru_cache(maxsize=1)
def get_url_validation_settings() -> UrlValidationSettings:
    """Charge la section url_validation depuis config/settings.yml (mis en cache).

    Returns:
        UrlValidationSettings: longueur max, schémas et ports autorisés.
    """
    data = _load_settings_yml()
    uv = data.get("url_validation") or {}
    max_len = int(uv.get("max_url_length", _DEFAULT_URL_MAX_LENGTH))
    schemes = uv.get("allowed_schemes") or _DEFAULT_URL_SCHEMES
    ports = uv.get("allowed_ports") or _DEFAULT_URL_PORTS
    return UrlValidationSettings(
        max_url_length=max_len,
        allowed_schemes=tuple(str(s) for s in schemes),
        allowed_ports=tuple(int(p) for p in ports),
    )


@dataclass(frozen=True)
class ScanTimeoutsSettings:
    """Timeouts pour le scan HTTP (roadmap §2.3)."""

    connection: float
    read: float
    scan_global: float


_DEFAULT_CONNECTION_TIMEOUT = 3.0
_DEFAULT_READ_TIMEOUT = 10.0
_DEFAULT_SCAN_GLOBAL_TIMEOUT = 60.0


@dataclass(frozen=True)
class SecurityHeaderConfig:
    """Configuration d'un en-tête de sécurité à vérifier."""

    name: str
    message_absent: str
    expected_value: str | None


_DEFAULT_SECURITY_HEADERS: tuple[tuple[str, str, str | None], ...] = (
    ("Content-Security-Policy", "Content-Security-Policy absent : risque XSS accru.", None),
    ("Strict-Transport-Security", "Strict-Transport-Security absent : risque de downgrade HTTPS→HTTP.", None),
    ("X-Frame-Options", "X-Frame-Options absent : risque de clickjacking.", None),
    ("X-Content-Type-Options", "X-Content-Type-Options absent : risque de MIME sniffing.", "nosniff"),
    ("Referrer-Policy", "Referrer-Policy absent : risque de fuite d'URLs sensibles.", None),
    ("Permissions-Policy", "Permissions-Policy absent : APIs navigateur accessibles par défaut.", None),
)


@lru_cache(maxsize=1)
def get_security_headers_settings() -> tuple[SecurityHeaderConfig, ...]:
    """Charge la section security_headers depuis config/settings.yml (mis en cache).

    Returns:
        tuple[SecurityHeaderConfig, ...]: Liste des en-têtes à vérifier.
    """
    data = _load_settings_yml()
    sh = data.get("security_headers") or {}
    headers_raw = sh.get("headers") or []
    if not headers_raw:
        return tuple(SecurityHeaderConfig(h[0], h[1], h[2]) for h in _DEFAULT_SECURITY_HEADERS)
    result: list[SecurityHeaderConfig] = []
    for item in headers_raw:
        if isinstance(item, dict):
            name = str(item.get("name", ""))
            msg = str(item.get("message_absent", ""))
            exp = item.get("expected_value")
            exp_val = str(exp) if exp is not None else None
            result.append(SecurityHeaderConfig(name=name, message_absent=msg, expected_value=exp_val))
    return tuple(result)


@dataclass(frozen=True)
class ExposedFileConfig:
    """Configuration d'un chemin sensible à tester (roadmap §3.4)."""

    path: str
    severity: str
    message: str


_DEFAULT_EXPOSED_PATHS: tuple[tuple[str, str, str], ...] = (
    ("/.env", "critical", "Fichier .env exposé : credentials et secrets accessibles."),
    ("/.git/config", "critical", "Fichier .git/config exposé : dépôt Git accessible."),
    ("/backup.zip", "high", "Archive backup.zip exposée : sauvegarde accessible."),
    ("/phpinfo.php", "high", "phpinfo.php exposé : configuration PHP révélée."),
    ("/admin/", "medium", "Interface /admin/ exposée : à protéger par authentification."),
    ("/.DS_Store", "low", "Fichier .DS_Store exposé : structure des répertoires révélée."),
)


@lru_cache(maxsize=1)
def get_exposed_files_settings() -> tuple[ExposedFileConfig, ...]:
    """Charge la section exposed_files depuis config/settings.yml (mis en cache).

    Returns:
        tuple[ExposedFileConfig, ...]: Liste des chemins à tester.
    """
    data = _load_settings_yml()
    ef = data.get("exposed_files") or {}
    paths_raw = ef.get("paths") or []
    if not paths_raw:
        return tuple(ExposedFileConfig(p[0], p[1], p[2]) for p in _DEFAULT_EXPOSED_PATHS)
    result: list[ExposedFileConfig] = []
    for item in paths_raw:
        if isinstance(item, dict):
            path = str(item.get("path", ""))
            severity = str(item.get("severity", "medium"))
            message = str(item.get("message", ""))
            result.append(ExposedFileConfig(path=path, severity=severity, message=message))
    return tuple(result)


@lru_cache(maxsize=1)
def get_exposed_files_max_body() -> int:
    """Retourne la limite de lecture du corps (octets) pour la détection."""
    data = _load_settings_yml()
    ef = data.get("exposed_files") or {}
    return int(ef.get("max_body_bytes", 8192))


@dataclass(frozen=True)
class DirectoryListingConfig:
    """Configuration d'un répertoire à tester pour le listing (roadmap §3.5)."""

    path: str
    severity: str
    message: str


_DEFAULT_DIRECTORY_LISTING_PATHS: tuple[tuple[str, str, str], ...] = (
    ("/uploads/", "high", "Directory listing activé sur /uploads/ : fichiers utilisateurs énumérables."),
    ("/assets/", "medium", "Directory listing activé sur /assets/ : structure révélée."),
    ("/static/", "medium", "Directory listing activé sur /static/ : structure révélée."),
)


@lru_cache(maxsize=1)
def get_directory_listing_settings() -> tuple[DirectoryListingConfig, ...]:
    """Charge la section directory_listing depuis config/settings.yml (mis en cache).

    Returns:
        tuple[DirectoryListingConfig, ...]: Liste des répertoires à tester.
    """
    data = _load_settings_yml()
    dl = data.get("directory_listing") or {}
    paths_raw = dl.get("paths") or []
    if not paths_raw:
        return tuple(DirectoryListingConfig(p[0], p[1], p[2]) for p in _DEFAULT_DIRECTORY_LISTING_PATHS)
    result: list[DirectoryListingConfig] = []
    for item in paths_raw:
        if isinstance(item, dict):
            path = str(item.get("path", ""))
            severity = str(item.get("severity", "medium"))
            message = str(item.get("message", ""))
            result.append(DirectoryListingConfig(path=path, severity=severity, message=message))
    return tuple(result)


@lru_cache(maxsize=1)
def get_directory_listing_max_body() -> int:
    """Retourne la limite de lecture du corps (octets) pour la détection du listing."""
    data = _load_settings_yml()
    dl = data.get("directory_listing") or {}
    return int(dl.get("max_body_bytes", 8192))


_DEFAULT_ROBOTS_TXT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("admin", "high"),
    ("administrator", "high"),
    ("backend", "high"),
    ("manage", "high"),
    ("api", "medium"),
    ("config", "high"),
    ("backup", "high"),
    ("private", "high"),
    ("internal", "high"),
    ("secret", "high"),
    ("cgi-bin", "medium"),
    ("upload", "medium"),
    ("media", "medium"),
    ("tmp", "medium"),
    ("cache", "medium"),
    ("database", "high"),
    (".git", "critical"),
    (".env", "critical"),
    ("login", "medium"),
    ("auth", "medium"),
)


@lru_cache(maxsize=1)
def get_robots_txt_settings() -> tuple[tuple[str, str], ...]:
    """Charge la section robots_txt depuis config/settings.yml (mis en cache).

    Returns:
        tuple[tuple[str, str], ...]: Liste des (motif, severity) pour routes sensibles.
    """
    data = _load_settings_yml()
    rt = data.get("robots_txt") or {}
    patterns_raw = rt.get("patterns") or []
    if not patterns_raw:
        return _DEFAULT_ROBOTS_TXT_PATTERNS
    result: list[tuple[str, str]] = []
    for item in patterns_raw:
        if isinstance(item, dict):
            pattern = str(item.get("pattern", ""))
            severity = str(item.get("severity", "medium"))
            if pattern:
                result.append((pattern, severity))
    return tuple(result) if result else _DEFAULT_ROBOTS_TXT_PATTERNS


@lru_cache(maxsize=1)
def get_scan_timeouts() -> ScanTimeoutsSettings:
    """Charge la section timeouts depuis config/settings.yml (mis en cache).

    Returns:
        ScanTimeoutsSettings: timeouts connexion, lecture et global.
    """
    data = _load_settings_yml()
    t = data.get("timeouts") or {}
    return ScanTimeoutsSettings(
        connection=float(t.get("connection", _DEFAULT_CONNECTION_TIMEOUT)),
        read=float(t.get("read", _DEFAULT_READ_TIMEOUT)),
        scan_global=float(t.get("scan_global", _DEFAULT_SCAN_GLOBAL_TIMEOUT)),
    )


__all__ = [
    "settings",
    "AppSettings",
    "DirectoryListingConfig",
    "ExposedFileConfig",
    "get_robots_txt_settings",
    "GeneralSettings",
    "RoutersSettings",
    "SecurityHeaderConfig",
    "SsrfSettings",
    "get_directory_listing_max_body",
    "get_directory_listing_settings",
    "get_exposed_files_max_body",
    "get_exposed_files_settings",
    "get_security_headers_settings",
    "get_ssrf_settings",
    "UrlValidationSettings",
    "get_url_validation_settings",
    "ScanTimeoutsSettings",
    "get_scan_timeouts",
]
