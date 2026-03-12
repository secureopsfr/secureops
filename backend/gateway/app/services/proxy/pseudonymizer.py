"""Pseudonymisation des données personnelles pour les métriques.

Ce module fournit des fonctions pour pseudonymiser les données personnelles
via HMAC-SHA256 afin de respecter le RGPD lors de la collecte de métriques.
"""

import hashlib
import hmac
import ipaddress
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def _pseudonymize_data(data: str, data_type: str = "data") -> Optional[str]:
    """Pseudonymise une donnée via HMAC-SHA256.

    Args:
        data (str): donnée brute à pseudonymiser.
        data_type (str): type de donnée pour les logs (optionnel).

    Returns:
        Optional[str]: hash hexadécimal pseudonymisé, ou None si le secret n'est pas configuré.
    """
    secret = os.getenv("ADMIN_METRICS_USER_HASH_SECRET")
    if not secret:
        logger.debug("ADMIN_METRICS_USER_HASH_SECRET non défini, pas de pseudonymisation pour %s", data_type)
        return None
    secret_bytes = secret.encode()
    hash_result = hmac.new(secret_bytes, data.encode(), hashlib.sha256).hexdigest()
    logger.debug("Pseudonymisation réussie pour %s: ***... -> %s...", data_type, hash_result[:16])
    return hash_result


def pseudonymize_user_id(user_id: str) -> Optional[str]:
    """Pseudonymise un identifiant utilisateur via HMAC-SHA256.

    Args:
        user_id (str): identifiant utilisateur brut (sub ou username).

    Returns:
        Optional[str]: hash hexadécimal pseudonymisé, ou None si le secret n'est pas configuré.
    """
    return _pseudonymize_data(user_id, "user_id")


def _truncate_ip_address(ip_address: str) -> str:
    """Tronque une adresse IP pour réduire la précision et respecter le RGPD.

    Args:
        ip_address (str): adresse IP brute (IPv4 ou IPv6).

    Returns:
        str: adresse IP tronquée (IPv4: dernier octet mis à 0, IPv6: 64 premiers bits).
    """
    try:
        parsed = ipaddress.ip_address(ip_address)
    except ValueError:
        # Format non reconnu, retourner tel quel
        return ip_address

    if isinstance(parsed, ipaddress.IPv4Address):
        # IPv4: tronquer le dernier octet (192.168.1.100 -> 192.168.1.0)
        network = ipaddress.ip_network(f"{parsed}/24", strict=False)
        return str(network.network_address)

    # IPv6: garder les 64 premiers bits et mettre le reste à zero
    network = ipaddress.ip_network(f"{parsed}/64", strict=False)
    return str(network.network_address)


def pseudonymize_ip_address(ip_address: str) -> Optional[str]:
    """Pseudonymise une adresse IP via HMAC-SHA256 après troncature.

    La troncature réduit la précision de localisation pour mieux respecter le RGPD :
    - IPv4 : le dernier octet est mis à 0 (192.168.1.100 -> 192.168.1.0)
    - IPv6 : les 64 derniers bits sont mis à 0

    Args:
        ip_address (str): adresse IP brute (IPv4 ou IPv6).

    Returns:
        Optional[str]: hash hexadécimal pseudonymisé, ou None si le secret n'est pas configuré.
    """
    truncated_ip = _truncate_ip_address(ip_address)
    return _pseudonymize_data(truncated_ip, "ip_address")
