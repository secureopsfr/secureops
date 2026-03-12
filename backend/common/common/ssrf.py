"""Protection SSRF : blocage localhost, IP privées.

Résolution DNS (A/AAAA) et refus si une IP résolue est dans une plage interdite.
En production (is_prod_env=True), localhost et les IP privées sont bloqués.
En non prod, localhost/127.0.0.1/::1 sont autorisés pour les tests locaux.
"""

import asyncio
import socket
from ipaddress import ip_address, ip_network

from common.config_base import SsrfSettings
from common.env_utils import is_prod_env
from common.url_helpers import extract_host_from_url, extract_port_from_url
from common.url_utils import URLValidationError


def _ipv4_networks_from_settings(settings: SsrfSettings) -> tuple:
    """Réseaux IPv4 interdits (précompilés depuis les settings)."""
    return tuple(ip_network(n) for n in settings.blocked_ipv4_networks)


def _ipv6_networks_from_settings(settings: SsrfSettings) -> tuple:
    """Réseaux IPv6 interdits (précompilés depuis les settings)."""
    return tuple(ip_network(n) for n in settings.blocked_ipv6_networks)


def is_hostname_blocked(hostname: str | None, settings: SsrfSettings) -> bool:
    """Indique si le hostname est dans la liste des hostnames interdits.

    En environnement non prod, localhost/127.0.0.1/::1 ne sont pas bloqués.

    Args:
        hostname: Host extrait de l'URL (peut être None).
        settings: Configuration SSRF.

    Returns:
        bool: True si le host est interdit.
    """
    if not hostname:
        return False
    normalized = hostname.lower().strip()
    if not is_prod_env() and normalized in {
        "localhost",
        "localhost.",
        "127.0.0.1",
        "::1",
        "[::1]",
    }:
        return False
    return normalized in settings.blocked_hostnames


def is_ip_blocked(ip_str: str, settings: SsrfSettings) -> bool:
    """Indique si l'IP (IPv4 ou IPv6) est dans une plage interdite.

    En environnement non prod, les IP loopback ne sont pas bloquées.

    Args:
        ip_str: Adresse IP en chaîne.
        settings: Configuration SSRF.

    Returns:
        bool: True si l'IP est bloquée.
    """
    try:
        addr = ip_address(ip_str)
    except ValueError:
        return True
    if not is_prod_env() and addr.is_loopback:
        return False
    ipv4_nets = _ipv4_networks_from_settings(settings)
    ipv6_nets = _ipv6_networks_from_settings(settings)
    if addr.version == 4:
        return any(addr in net for net in ipv4_nets)
    return any(addr in net for net in ipv6_nets)


def resolve_host(host: str, port: int | None) -> list[str]:
    """Résout le host en liste d'adresses IP (A + AAAA). Bloquant. Public pour tests."""
    port = port or 80
    try:
        results = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    ips: list[str] = []
    seen: set[str] = set()
    for _family, _type, _proto, _canon, sockaddr in results:
        ip = sockaddr[0]
        if ip not in seen:
            seen.add(ip)
            ips.append(ip)
    return ips


async def check_ssrf(url: str, settings: SsrfSettings, timeout: float | None = None) -> None:
    """Vérifie que l'URL ne cible pas localhost ni une IP privée.

    Résout le host via DNS et lève URLValidationError si une IP résolue
    est dans une plage interdite.

    Args:
        url: URL normalisée (après validate_and_normalize_url).
        settings: Configuration SSRF (dns_timeout, plages bloquées).
        timeout: Délai max pour la résolution DNS (défaut: settings.dns_timeout).

    Raises:
        URLValidationError: Si le host est interdit ou résout vers une IP bloquée.
    """
    t = timeout if timeout is not None else settings.dns_timeout
    host = extract_host_from_url(url).strip()
    if not host:
        raise URLValidationError("URL sans host.")
    if is_hostname_blocked(host, settings):
        raise URLValidationError(
            "Les adresses localhost / 127.0.0.1 / ::1 ne sont pas autorisées.",
        )

    port = extract_port_from_url(url)
    try:
        ips = await asyncio.wait_for(
            asyncio.to_thread(resolve_host, host, port),
            timeout=t,
        )
    except asyncio.TimeoutError:
        raise URLValidationError("Délai de résolution DNS dépassé.") from None
    if not ips:
        raise URLValidationError("Impossible de résoudre le nom d'hôte.")

    blocked = [ip for ip in ips if is_ip_blocked(ip, settings)]
    if blocked:
        raise URLValidationError(
            "L'URL pointe vers une adresse IP privée ou locale (interdit pour des raisons de sécurité).",
        )
