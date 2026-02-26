"""Détection des versions TLS obsolètes (1.0, 1.1)."""

import socket
import ssl


def try_tls_version(host: str, port: int, timeout: float, min_ver: ssl.TLSVersion, max_ver: ssl.TLSVersion) -> bool:
    """Tente une connexion TLS avec les versions min/max spécifiées.

    Args:
        host: Nom d'hôte.
        port: Port (443).
        timeout: Timeout en secondes.
        min_ver: Version TLS minimale.
        max_ver: Version TLS maximale.

    Returns:
        bool: True si la connexion réussit.
    """
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = min_ver
        context.maximum_version = max_ver
        with socket.create_connection((host, port), timeout=timeout) as sock, context.wrap_socket(sock, server_hostname=host) as ssock:
            _ = ssock.version()
        return True
    except (ssl.SSLError, OSError):
        return False


def check_tls_versions_obsolete(host: str, port: int, timeout: float) -> tuple[list[str], list[str]]:
    """Détecte si le serveur accepte TLS 1.0 ou 1.1 (obsolètes).

    Args:
        host: Nom d'hôte.
        port: Port (ex. 443 ou 1010 pour badssl.com).
        timeout: Timeout en secondes.

    Returns:
        tuple[list[str], list[str]]: (versions_obsolete, findings).
    """
    obsolete: list[str] = []
    findings: list[str] = []

    if try_tls_version(host, port, timeout, ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1):
        obsolete.append("1.0")
    if try_tls_version(host, port, timeout, ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1):
        obsolete.append("1.1")

    if obsolete:
        findings.append(f"TLS {' et '.join(obsolete)} encore accepté(s). Versions obsolètes à désactiver.")

    return obsolete, findings
