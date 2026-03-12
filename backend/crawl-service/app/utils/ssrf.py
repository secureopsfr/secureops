"""Protection SSRF — délègue à common."""

from common.ssrf import check_ssrf as _check_ssrf
from common.ssrf import is_hostname_blocked as _is_hostname_blocked

from app.config_loader import get_ssrf_settings


def is_hostname_blocked(hostname: str | None) -> bool:
    """Indique si le hostname est bloqué (config crawl-service)."""
    return _is_hostname_blocked(hostname, get_ssrf_settings())


async def check_ssrf(url: str, timeout: float | None = None) -> None:
    """Vérifie que l'URL ne cible pas localhost ni une IP privée."""
    settings = get_ssrf_settings()
    await _check_ssrf(url, settings, timeout=timeout)
