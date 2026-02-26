"""Exécution du scan : étapes métier (TLS, etc.). Utilise get_scan_timeouts pour le client HTTP."""

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import httpx

from app.config_loader import get_scan_timeouts


@dataclass
class TlsCheckResult:
    """Résultat des vérifications TLS/HTTPS.

    Attributes:
        https_enabled (bool): True si le site répond en HTTPS.
        findings (tuple[str, ...]): Liste des findings (ex. "HTTPS non activé").
    """

    https_enabled: bool
    findings: tuple[str, ...]


def _build_https_url(url: str) -> str:
    """Construit l'URL HTTPS à tester à partir de l'URL fournie.

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL https://host/ (port 443 implicite).
    """
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc.split(":")[0]
    return urlunparse(("https", host, "/", "", "", ""))


async def run_tls_checks(url: str) -> TlsCheckResult:
    """Vérifications TLS/HTTPS (roadmap §3.1).

    Vérification 1 : HTTPS activé ? Une requête GET vers https://<host>/ doit aboutir
    (même si le certificat est invalide ou auto-signé). Si connexion refusée ou timeout,
    HTTPS n'est pas proposé.

    Args:
        url: URL normalisée à scanner (sera utilisée pour extraire le host).

    Returns:
        TlsCheckResult: https_enabled et liste des findings.
    """
    timeouts = get_scan_timeouts()
    https_url = _build_https_url(url)
    findings: list[str] = []

    try:
        async with httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(
                timeouts.connection,
                read=timeouts.read,
            ),
        ) as client:
            response = await client.get(https_url)
            # Toute réponse (200, 301, 404, etc.) indique que HTTPS répond
            _ = response.status_code
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        findings.append("HTTPS non activé (connexion refusée ou timeout). Risque d'interception.")
        return TlsCheckResult(https_enabled=False, findings=tuple(findings))
    except Exception as e:
        findings.append(f"HTTPS non activé : {e!s}")
        return TlsCheckResult(https_enabled=False, findings=tuple(findings))

    return TlsCheckResult(https_enabled=True, findings=tuple(findings))
