"""Configuration SSRF (roadmap §2.2)."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class SsrfSettings:
    """Configuration de la protection SSRF (hostnames, plages IP, timeout DNS)."""

    dns_timeout: float
    blocked_hostnames: frozenset[str]
    blocked_ipv4_networks: tuple[str, ...]
    blocked_ipv6_networks: tuple[str, ...]


_DEFAULT_HOSTNAMES = ("localhost", "localhost.", "127.0.0.1", "::1", "[::1]", "0.0.0.0")
_DEFAULT_IPV4 = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16", "127.0.0.0/8", "0.0.0.0/8")
_DEFAULT_IPV6 = ("::1/128", "fe80::/10", "fc00::/7")


@lru_cache(maxsize=1)
def get_ssrf_settings() -> SsrfSettings:
    """Charge la section SSRF depuis config/settings.yml."""
    data = _load_settings_yml()
    ssrf = data.get("ssrf") or {}
    dns_timeout = float(ssrf.get("dns_timeout", 5.0))
    hostnames = ssrf.get("blocked_hostnames") or _DEFAULT_HOSTNAMES
    ipv4 = ssrf.get("blocked_ipv4_networks") or _DEFAULT_IPV4
    ipv6 = ssrf.get("blocked_ipv6_networks") or _DEFAULT_IPV6
    return SsrfSettings(
        dns_timeout=dns_timeout,
        blocked_hostnames=frozenset(str(h) for h in hostnames),
        blocked_ipv4_networks=tuple(str(n) for n in ipv4),
        blocked_ipv6_networks=tuple(str(n) for n in ipv6),
    )
