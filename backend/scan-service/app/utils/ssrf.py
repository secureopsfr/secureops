"""Protection SSRF : blocage localhost, IP privées et redirections (roadmap §2.2).

Résolution DNS (A/AAAA) et refus si une IP résolue est dans une plage interdite.
Configuration chargée depuis config/settings.yml (section ssrf).

En production (`IS_PROD=true`), localhost et les IP privées sont bloqués.
En environnement non prod (`IS_PROD=false`), localhost/127.0.0.1/::1 sont
autorisés pour tester un serveur local (ex. bad_cache_server sur 127.0.0.1:8001).
"""

import asyncio
import os
import socket
from functools import lru_cache
from ipaddress import ip_address, ip_network

from app.config_loader import get_ssrf_settings
from app.utils.url_helpers import extract_host_from_url, extract_port_from_url
from app.utils.url_validator import URLValidationError


@lru_cache(maxsize=1)
def _ipv4_networks() -> tuple:
    """Réseaux IPv4 interdits (précompilés depuis les settings)."""
    return tuple(ip_network(n) for n in get_ssrf_settings().blocked_ipv4_networks)


@lru_cache(maxsize=1)
def _ipv6_networks() -> tuple:
    """Réseaux IPv6 interdits (précompilés depuis les settings)."""
    return tuple(ip_network(n) for n in get_ssrf_settings().blocked_ipv6_networks)


def _is_prod_env() -> bool:
    """Indique si l'environnement est en mode production.

    La variable d'environnement IS_PROD est considérée vraie si elle vaut
    "1", "true" ou "yes" (insensible à la casse). Si elle est absente,
    le comportement par défaut est conservateur (prod).
    """
    value = os.getenv("IS_PROD", "true").lower().strip()
    return value in ("1", "true", "yes")


def is_hostname_blocked(hostname: str | None) -> bool:
    """Indique si le hostname est dans la liste des hostnames interdits (localhost, etc.).

    En environnement non prod (`IS_PROD=false`), localhost/127.0.0.1/::1 ne sont
    pas bloqués pour permettre les tests locaux.

    Args:
        hostname: Host extrait de l'URL (peut être None).

    Returns:
        bool: True si le host est interdit.
    """
    if not hostname:
        return False
    normalized = hostname.lower().strip()
    if not _is_prod_env() and normalized in {
        "localhost",
        "localhost.",
        "127.0.0.1",
        "::1",
        "[::1]",
    }:
        return False
    return normalized in get_ssrf_settings().blocked_hostnames


def is_ip_blocked(ip_str: str) -> bool:
    """Indique si l'IP (IPv4 ou IPv6) est dans une plage interdite.

    En environnement non prod (`IS_PROD=false`), les IP loopback (127.x, ::1)
    ne sont pas bloquées pour les tests locaux. Les autres IP privées restent
    interdites.

    Args:
        ip_str: Adresse IP en chaîne.

    Returns:
        bool: True si l'IP est bloquée (privée, loopback, link-local).
    """
    try:
        addr = ip_address(ip_str)
    except ValueError:
        return True
    if not _is_prod_env() and addr.is_loopback:
        return False
    if addr.version == 4:
        return any(addr in net for net in _ipv4_networks())
    return any(addr in net for net in _ipv6_networks())


def _resolve_host(host: str, port: int | None) -> list[str]:
    """Résout le host en liste d'adresses IP (A + AAAA). Bloquant.

    Args:
        host: Nom d'hôte ou IP.
        port: Port (utilisé pour getaddrinfo, 80 par défaut).

    Returns:
        list[str]: Liste d'adresses IP uniques.
    """
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


async def check_ssrf(url: str, timeout: float = 5.0) -> None:
    """Vérifie que l'URL ne cible pas localhost ni une IP privée (protection SSRF).

    Résout le host via DNS (A/AAAA) et lève URLValidationError si une IP résolue
    est dans une plage interdite. Utilise un timeout pour la résolution.

    Args:
        url: URL normalisée (après validate_and_normalize_url).
        timeout: Délai max pour la résolution DNS en secondes.

    Raises:
        URLValidationError: Si le host est interdit ou résout vers une IP bloquée.
    """
    host = extract_host_from_url(url).strip()
    if not host:
        raise URLValidationError("URL sans host.")
    if is_hostname_blocked(host):
        raise URLValidationError(
            "Les adresses localhost / 127.0.0.1 / ::1 ne sont pas autorisées.",
        )

    port = extract_port_from_url(url)
    try:
        ips = await asyncio.wait_for(
            asyncio.to_thread(_resolve_host, host, port),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise URLValidationError("Délai de résolution DNS dépassé.") from None
    if not ips:
        raise URLValidationError("Impossible de résoudre le nom d'hôte.")

    blocked = [ip for ip in ips if is_ip_blocked(ip)]
    if blocked:
        raise URLValidationError(
            "L'URL pointe vers une adresse IP privée ou locale (interdit pour des raisons de sécurité).",
        )
