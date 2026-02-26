"""Fingerprinting technologique léger (roadmap §3.7).

Lit les en-têtes Server, X-Powered-By, etc., applique des heuristiques simples
pour détecter serveur web, runtime et framework/CMS. Remonte une « stack info »
indicative sans sur-promettre.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


@dataclass
class TechFingerprintingCheckResult:
    """Résultat du fingerprinting technologique.

    Attributes:
        server (str | None): Valeur de l'en-tête Server.
        runtime (str | None): Valeur de X-Powered-By ou détection déduite.
        framework_cms (str | None): Framework/CMS probable (ex. WordPress, Drupal, Express).
        findings (tuple[str, ...]): Messages informatifs (niveau Info).
        fetch_ok (bool): True si la réponse a pu être analysée.
    """

    server: str | None
    runtime: str | None
    framework_cms: str | None
    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise pour l'événement SSE result."""
        return {
            "server": self.server,
            "runtime": self.runtime,
            "framework_cms": self.framework_cms,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


def _get_header(response: "httpx.Response", name: str) -> str | None:
    """Retourne la valeur d'un en-tête (insensible casse) ou None."""
    for k, v in response.headers.items():
        if k.lower() == name.lower():
            return v
    return None


def _detect_framework_cms(response: "httpx.Response") -> str | None:
    """Détecte framework ou CMS via heuristiques sur les en-têtes.

    Retourne un libellé indicatif (WordPress, Drupal, Express, etc.) ou None.
    """
    x_generator = _get_header(response, "X-Generator")
    x_drupal_cache = _get_header(response, "X-Drupal-Cache")
    x_powered_by = _get_header(response, "X-Powered-By") or ""

    if x_drupal_cache is not None:
        return "Drupal"
    if x_generator and "drupal" in x_generator.lower():
        return "Drupal"
    if x_generator and "wordpress" in x_generator.lower():
        return "WordPress"
    if "express" in x_powered_by.lower():
        return "Express"
    if "asp.net" in x_powered_by.lower():
        return "ASP.NET"
    if "php" in x_powered_by.lower():
        return "PHP"
    return None


def check_tech_fingerprinting_from_response(response: "httpx.Response | None") -> TechFingerprintingCheckResult:
    """Analyse les en-têtes pour un fingerprinting technologique léger.

    Lit Server, X-Powered-By, X-Generator, X-Drupal-Cache, etc. Applique des
    heuristiques simples. Formulations indicatives (« probable », « détecté »).

    Args:
        response: Réponse HTTP (ou None si le fetch a échoué).

    Returns:
        TechFingerprintingCheckResult: Stack info indicative.
    """
    if response is None:
        return TechFingerprintingCheckResult(
            server=None,
            runtime=None,
            framework_cms=None,
            findings=("Impossible d'analyser les en-têtes (connexion refusée ou timeout).",),
            fetch_ok=False,
        )

    server = _get_header(response, "Server")
    x_powered_by = _get_header(response, "X-Powered-By")
    framework_cms = _detect_framework_cms(response)

    findings: list[str] = []
    if server:
        findings.append(f"Serveur détecté : {server}")
    if x_powered_by:
        findings.append(f"Runtime : {x_powered_by} (X-Powered-By)")
    if framework_cms:
        findings.append(f"Framework/CMS probable : {framework_cms}")
    if not findings:
        findings.append("Stack : non identifiée (ou masquée)")

    return TechFingerprintingCheckResult(
        server=server,
        runtime=x_powered_by,
        framework_cms=framework_cms,
        findings=tuple(findings),
        fetch_ok=True,
    )
