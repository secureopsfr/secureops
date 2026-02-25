"""Chargement de configuration pour Scan Service."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings, load_yaml

settings = create_simple_settings("scan-service", default_port=8012, caller_file=__file__)


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
    root = Path(__file__).resolve().parents[1]
    data = load_yaml(root / "config" / "settings.yml")
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
    root = Path(__file__).resolve().parents[1]
    data = load_yaml(root / "config" / "settings.yml")
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


@lru_cache(maxsize=1)
def get_scan_timeouts() -> ScanTimeoutsSettings:
    """Charge la section timeouts depuis config/settings.yml (mis en cache).

    Returns:
        ScanTimeoutsSettings: timeouts connexion, lecture et global.
    """
    root = Path(__file__).resolve().parents[1]
    data = load_yaml(root / "config" / "settings.yml")
    t = data.get("timeouts") or {}
    return ScanTimeoutsSettings(
        connection=float(t.get("connection", _DEFAULT_CONNECTION_TIMEOUT)),
        read=float(t.get("read", _DEFAULT_READ_TIMEOUT)),
        scan_global=float(t.get("scan_global", _DEFAULT_SCAN_GLOBAL_TIMEOUT)),
    )


__all__ = [
    "settings",
    "AppSettings",
    "GeneralSettings",
    "RoutersSettings",
    "SsrfSettings",
    "get_ssrf_settings",
    "UrlValidationSettings",
    "get_url_validation_settings",
    "ScanTimeoutsSettings",
    "get_scan_timeouts",
]
