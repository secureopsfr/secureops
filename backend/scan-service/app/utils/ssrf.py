"""Protection SSRF — délègue à common."""

from common.ssrf import check_ssrf as _check_ssrf
from common.ssrf import is_hostname_blocked as _is_hostname_blocked
from common.ssrf import is_ip_blocked as _is_ip_blocked
from common.ssrf import (
    resolve_host,
)

from app.config_loader import get_ssrf_settings

# Alias pour compatibilité tests (monkeypatch cible common.ssrf.resolve_host)
_resolve_host = resolve_host


def is_hostname_blocked(hostname: str | None) -> bool:
    """Indique si le hostname est bloqué (config scan-service)."""
    return _is_hostname_blocked(hostname, get_ssrf_settings())


def is_ip_blocked(ip_str: str) -> bool:
    """Indique si l'IP est bloquée (config scan-service)."""
    return _is_ip_blocked(ip_str, get_ssrf_settings())


async def check_ssrf(url: str, timeout: float | None = None) -> None:
    """Vérifie que l'URL ne cible pas localhost ni une IP privée."""
    settings = get_ssrf_settings()
    await _check_ssrf(url, settings, timeout=timeout)
