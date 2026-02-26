"""Chargement de configuration pour Scan Service."""

import re
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
    """Configuration d'un en-tête de sécurité à vérifier.

    Attributes:
        name (str): Nom de l'en-tête HTTP.
        message_absent (str): Message si l'en-tête est absent.
        expected_value (str | None): Valeur attendue (ex. nosniff) ou None.
        slug (str): Slug pour le finding (ex. headers-csp-absent). Dérivé du nom si absent en YAML.
    """

    name: str
    message_absent: str
    expected_value: str | None
    slug: str


# Slug connu pour chaque en-tête par défaut (utilisé quand YAML n'a pas de slug).
_KNOWN_HEADER_SLUGS: dict[str, str] = {
    "Content-Security-Policy": "headers-csp-absent",
    "Strict-Transport-Security": "headers-hsts-absent",
    "X-Frame-Options": "headers-xfo-absent",
    "X-Content-Type-Options": "headers-xcto-absent",
    "Referrer-Policy": "headers-referrer-absent",
    "Permissions-Policy": "headers-permissions-absent",
}


def _derive_header_slug(name: str) -> str:
    """Dérive un slug à partir du nom d'en-tête (pour headers ajoutés en YAML sans slug).

    Utilise _KNOWN_HEADER_SLUGS si le nom est connu, sinon slugify le nom.

    Args:
        name: Nom de l'en-tête (ex. Content-Security-Policy).

    Returns:
        str: Slug (ex. headers-csp-absent ou headers-content-security-policy-absent).
    """
    if name in _KNOWN_HEADER_SLUGS:
        return _KNOWN_HEADER_SLUGS[name]
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"headers-{normalized}-absent" if normalized else "headers-unknown-absent"


_DEFAULT_SECURITY_HEADERS: tuple[tuple[str, str, str | None, str], ...] = (
    ("Content-Security-Policy", "Content-Security-Policy absent : risque XSS accru.", None, "headers-csp-absent"),
    ("Strict-Transport-Security", "Strict-Transport-Security absent : risque de downgrade HTTPS→HTTP.", None, "headers-hsts-absent"),
    ("X-Frame-Options", "X-Frame-Options absent : risque de clickjacking.", None, "headers-xfo-absent"),
    ("X-Content-Type-Options", "X-Content-Type-Options absent : risque de MIME sniffing.", "nosniff", "headers-xcto-absent"),
    ("Referrer-Policy", "Referrer-Policy absent : risque de fuite d'URLs sensibles.", None, "headers-referrer-absent"),
    ("Permissions-Policy", "Permissions-Policy absent : APIs navigateur accessibles par défaut.", None, "headers-permissions-absent"),
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
        return tuple(SecurityHeaderConfig(h[0], h[1], h[2], h[3]) for h in _DEFAULT_SECURITY_HEADERS)
    result: list[SecurityHeaderConfig] = []
    for item in headers_raw:
        if isinstance(item, dict):
            name = str(item.get("name", ""))
            msg = str(item.get("message_absent", ""))
            exp = item.get("expected_value")
            exp_val = str(exp) if exp is not None else None
            slug = str(item.get("slug", "")) if item.get("slug") else _derive_header_slug(name)
            result.append(SecurityHeaderConfig(name=name, message_absent=msg, expected_value=exp_val, slug=slug))
    return tuple(result)


@dataclass(frozen=True)
class PathCheckConfig:
    """Configuration commune pour une vérification par chemin (path, severity, message).

    Utilisé par exposed_files et directory_listing (roadmap §3.4, §3.5).

    Attributes:
        path (str): Chemin à tester (ex. /.env, /uploads/).
        severity (str): Niveau de sévérité (critical, high, medium, low).
        message (str): Message du finding.
    """

    path: str
    severity: str
    message: str


def _get_path_check_settings(section: str, defaults: tuple[tuple[str, str, str], ...]) -> tuple[PathCheckConfig, ...]:
    """Charge une section YAML de type path check (paths avec path, severity, message).

    Args:
        section: Clé de section (ex. "exposed_files", "directory_listing").
        defaults: Liste de tuples (path, severity, message) si paths vide ou absent.

    Returns:
        tuple[PathCheckConfig, ...]: Liste des configs pour cette section.
    """
    data = _load_settings_yml()
    block = data.get(section) or {}
    paths_raw = block.get("paths") or []
    if not paths_raw:
        return tuple(PathCheckConfig(p[0], p[1], p[2]) for p in defaults)
    result: list[PathCheckConfig] = []
    for item in paths_raw:
        if isinstance(item, dict):
            path = str(item.get("path", ""))
            severity = str(item.get("severity", "medium"))
            message = str(item.get("message", ""))
            result.append(PathCheckConfig(path=path, severity=severity, message=message))
    return tuple(result)


def _get_path_check_max_body(section: str, default: int) -> int:
    """Retourne la limite de lecture du corps (octets) pour une section path check.

    Args:
        section: Clé de section (ex. "exposed_files", "directory_listing").
        default: Valeur par défaut si max_body_bytes absent.

    Returns:
        int: Limite en octets.
    """
    data = _load_settings_yml()
    block = data.get(section) or {}
    return int(block.get("max_body_bytes", default))


_DEFAULT_EXPOSED_PATHS: tuple[tuple[str, str, str], ...] = (
    ("/.env", "critical", "Fichier .env exposé : credentials et secrets accessibles."),
    ("/.git/config", "critical", "Fichier .git/config exposé : dépôt Git accessible."),
    ("/backup.zip", "high", "Archive backup.zip exposée : sauvegarde accessible."),
    ("/phpinfo.php", "high", "phpinfo.php exposé : configuration PHP révélée."),
    ("/admin/", "medium", "Interface /admin/ exposée : à protéger par authentification."),
    ("/.DS_Store", "low", "Fichier .DS_Store exposé : structure des répertoires révélée."),
)


_DEFAULT_DIRECTORY_LISTING_PATHS: tuple[tuple[str, str, str], ...] = (
    ("/uploads/", "high", "Directory listing activé sur /uploads/ : fichiers utilisateurs énumérables."),
    ("/assets/", "medium", "Directory listing activé sur /assets/ : structure révélée."),
    ("/static/", "medium", "Directory listing activé sur /static/ : structure révélée."),
)

# Alias pour rétrocompatibilité et sémantique par domaine.
ExposedFileConfig = PathCheckConfig
DirectoryListingConfig = PathCheckConfig


@lru_cache(maxsize=1)
def get_exposed_files_settings() -> tuple[PathCheckConfig, ...]:
    """Charge la section exposed_files depuis config/settings.yml (mis en cache).

    Returns:
        tuple[PathCheckConfig, ...]: Liste des chemins à tester.
    """
    return _get_path_check_settings("exposed_files", _DEFAULT_EXPOSED_PATHS)


@lru_cache(maxsize=1)
def get_exposed_files_max_body() -> int:
    """Retourne la limite de lecture du corps (octets) pour la détection."""
    return _get_path_check_max_body("exposed_files", 8192)


@lru_cache(maxsize=1)
def get_directory_listing_settings() -> tuple[PathCheckConfig, ...]:
    """Charge la section directory_listing depuis config/settings.yml (mis en cache).

    Returns:
        tuple[PathCheckConfig, ...]: Liste des répertoires à tester.
    """
    return _get_path_check_settings("directory_listing", _DEFAULT_DIRECTORY_LISTING_PATHS)


@lru_cache(maxsize=1)
def get_directory_listing_max_body() -> int:
    """Retourne la limite de lecture du corps (octets) pour la détection du listing."""
    return _get_path_check_max_body("directory_listing", 8192)


# Defaults utilisés quand robots_txt.patterns est vide. YAML fait foi pour les surcharges.
_DEFAULT_ROBOTS_TXT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("admin", "high"),
    ("administrator", "high"),
    ("backend", "high"),
    ("manage", "high"),
    ("api", "medium"),
    ("config", "high"),
    ("configs", "high"),
    ("configuration", "high"),
    ("backup", "high"),
    ("backups", "high"),
    ("dump", "high"),
    ("private", "high"),
    ("internal", "high"),
    ("secret", "high"),
    ("cgi-bin", "medium"),
    ("/bin/", "medium"),
    ("upload", "medium"),
    ("uploads", "medium"),
    ("media", "medium"),
    ("files", "medium"),
    ("tmp", "medium"),
    ("temp", "medium"),
    ("cache", "medium"),
    ("/db/", "high"),
    ("database", "high"),
    ("sql", "high"),
    (".git", "critical"),
    (".env", "critical"),
    ("login", "medium"),
    ("auth", "medium"),
    ("signin", "medium"),
)


@lru_cache(maxsize=1)
def get_robots_txt_settings() -> tuple[tuple[str, str], ...]:
    """Charge la section robots_txt depuis config/settings.yml (mis en cache).

    Si patterns est vide ou absent, utilise _DEFAULT_ROBOTS_TXT_PATTERNS. Le YAML fait foi
    pour les surcharges ; les defaults sont dans le code.

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


@dataclass(frozen=True)
class ScoringSettings:
    """Configuration du scoring : pondération par catégorie et pénalités par sévérité."""

    category_weights: dict[str, int]
    severity_penalties: dict[str, int]


_DEFAULT_CATEGORY_WEIGHTS: dict[str, int] = {
    "tls": 25,
    "headers": 25,
    "cookies": 20,
    "exposed_files": 10,
    "directory_listing": 10,
    "robots_txt": 5,
    "tech_fingerprinting": 5,
}
_DEFAULT_SEVERITY_PENALTIES: dict[str, int] = {
    "critical": 100,
    "high": 50,
    "medium": 25,
    "low": 10,
    "info": 0,
}
_DEFAULT_SEVERITY_UPGRADE_PATHS: tuple[str, ...] = ("/.git/config", "/.env")


@lru_cache(maxsize=1)
def get_scoring_settings() -> ScoringSettings:
    """Charge la section scoring depuis config/settings.yml (mis en cache).

    Returns:
        ScoringSettings: Pondération par catégorie et pénalités par sévérité.
    """
    data = _load_settings_yml()
    s = data.get("scoring") or {}
    cw = s.get("category_weights") or _DEFAULT_CATEGORY_WEIGHTS
    sp = s.get("severity_penalties") or _DEFAULT_SEVERITY_PENALTIES
    return ScoringSettings(
        category_weights=dict((k, int(v)) for k, v in cw.items()),
        severity_penalties=dict((k, int(v)) for k, v in sp.items()),
    )


@lru_cache(maxsize=1)
def get_exposed_files_severity_upgrade() -> tuple[str, ...]:
    """Charge les chemins à upgrader en critical (exposed_files.severity_upgrade).

    Returns:
        tuple[str, ...]: Chemins forcés en critical (ex. /.git/config, /.env).
    """
    data = _load_settings_yml()
    ef = data.get("exposed_files") or {}
    paths = ef.get("severity_upgrade") or list(_DEFAULT_SEVERITY_UPGRADE_PATHS)
    return tuple(str(p) for p in paths)


__all__ = [
    "AppSettings",
    "DirectoryListingConfig",
    "ExposedFileConfig",
    "GeneralSettings",
    "PathCheckConfig",
    "RoutersSettings",
    "ScanTimeoutsSettings",
    "ScoringSettings",
    "SecurityHeaderConfig",
    "SsrfSettings",
    "UrlValidationSettings",
    "get_directory_listing_max_body",
    "get_directory_listing_settings",
    "get_exposed_files_max_body",
    "get_exposed_files_settings",
    "get_exposed_files_severity_upgrade",
    "get_robots_txt_settings",
    "get_scoring_settings",
    "get_scan_timeouts",
    "get_security_headers_settings",
    "get_ssrf_settings",
    "get_url_validation_settings",
    "settings",
]
