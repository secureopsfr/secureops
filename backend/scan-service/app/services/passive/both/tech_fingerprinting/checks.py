"""Fingerprinting technologique (roadmap §3.7, §5.1.7).

Lit les en-têtes Server, X-Powered-By, etc., extrait les versions, analyse le HTML
(meta generator, scripts), détecte les versions vulnérables connues, et produit
un rapport « stack probable » avec niveaux de confiance.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config_loader import get_tech_fingerprinting_thresholds
from app.constants import MSG_HEADERS_ANALYSIS_UNAVAILABLE
from app.utils.headers import get_header_insensitive

if TYPE_CHECKING:
    import httpx

# Confiance selon la source : en-tête avec version > en-tête sans version > HTML.
_CONFIDENCE_HEADER_VERSION = 95
_CONFIDENCE_HEADER_RAW = 70
_CONFIDENCE_HTML_META = 60
_CONFIDENCE_HTML_SCRIPT = 50


@dataclass
class StackEntry:
    """Entrée de la stack détectée avec niveau de confiance.

    Attributes:
        product (str): Nom du produit (nginx, PHP, WordPress, etc.).
        version (str | None): Version extraite si disponible.
        confidence (int): Niveau de confiance 0-100.
        source (str): Origine (header_server, header_x_powered_by, html_meta, html_script).
    """

    product: str
    version: str | None
    confidence: int
    source: str


@dataclass
class VulnerableVersion:
    """Version détectée connue comme vulnérable.

    Attributes:
        product (str): Nom du produit.
        version (str): Version détectée.
        min_safe_version (str): Version minimale recommandée.
    """

    product: str
    version: str
    min_safe_version: str


@dataclass
class TechFingerprintingCheckResult:
    """Résultat du fingerprinting technologique.

    Attributes:
        server (str | None): Valeur brute de l'en-tête Server.
        server_version (str | None): Version extraite du Server.
        runtime (str | None): Valeur brute de X-Powered-By.
        runtime_version (str | None): Version extraite du runtime.
        framework_cms (str | None): Framework/CMS probable.
        framework_cms_version (str | None): Version du framework/CMS (ex. HTML meta).
        stack_entries (tuple[StackEntry, ...]): Stack unifiée avec confiance.
        vulnerable_versions (tuple[VulnerableVersion, ...]): Versions vulnérables détectées.
        findings (tuple[str, ...]): Messages informatifs.
        fetch_ok (bool): True si la réponse a pu être analysée.
    """

    server: str | None
    server_version: str | None
    runtime: str | None
    runtime_version: str | None
    framework_cms: str | None
    framework_cms_version: str | None
    stack_entries: tuple[StackEntry, ...]
    vulnerable_versions: tuple[VulnerableVersion, ...]
    findings: tuple[str, ...]
    fetch_ok: bool

    def to_dict(self) -> dict:
        """Sérialise pour l'événement SSE result."""
        stack_serialized = [{"product": e.product, "version": e.version, "confidence": e.confidence, "source": e.source} for e in self.stack_entries]
        vuln_serialized = [{"product": v.product, "version": v.version, "min_safe_version": v.min_safe_version} for v in self.vulnerable_versions]
        return {
            "server": self.server,
            "server_version": self.server_version,
            "runtime": self.runtime,
            "runtime_version": self.runtime_version,
            "framework_cms": self.framework_cms,
            "framework_cms_version": self.framework_cms_version,
            "stack_entries": stack_serialized,
            "vulnerable_versions": vuln_serialized,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


# Regex pour extraire les versions (ex. nginx/1.18.0, PHP/8.1.2, Apache/2.4.52).
_VERSION_PATTERN = re.compile(r"(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)")

# Produits serveur avec préfixe connu.
_SERVER_PRODUCTS = ("nginx", "apache", "iis", "openresty", "caddy", "lighttpd")


def _parse_version(value: str) -> str | None:
    """Extrait la première version (X.Y.Z) d'une chaîne.

    Args:
        value: Chaîne (ex. "nginx/1.18.0 (Ubuntu)").

    Returns:
        str | None: Version extraite ou None.
    """
    m = _VERSION_PATTERN.search(value)
    return m.group(1) if m else None


def _parse_product_from_header(value: str) -> str | None:
    """Extrait le nom du produit depuis une valeur d'en-tête.

    Args:
        value: Valeur (ex. "nginx/1.18.0", "PHP/8.2").

    Returns:
        str | None: Nom du produit en minuscules.
    """
    if not value:
        return None
    # Format "product/version" ou "product version"
    parts = value.split("/")[0].split()[0].lower()
    for prod in _SERVER_PRODUCTS:
        if prod in value.lower():
            return prod
    if "php" in value.lower():
        return "php"
    if "asp.net" in value.lower() or "aspnet" in value.lower():
        return "asp.net"
    if "express" in value.lower():
        return "express"
    return parts if len(parts) > 1 else None


def _version_less_than(ver: str, threshold: str) -> bool:
    """Compare deux versions (format X.Y.Z). Retourne True si ver < threshold."""

    def to_tuple(s: str) -> tuple[int, ...]:
        parts = s.split(".")
        return tuple(int(p) if p.isdigit() else 0 for p in parts[:4])

    try:
        return to_tuple(ver) < to_tuple(threshold)
    except (ValueError, AttributeError):
        return False


def _check_vulnerable(product: str, version: str) -> str | None:
    """Vérifie si la version est en dessous du seuil recommandé (config).

    Returns:
        str | None: min_safe_version si vulnérable, None sinon.
    """
    thresholds = get_tech_fingerprinting_thresholds()
    key = product.lower()
    for prod_key, min_ver in thresholds.items():
        if (prod_key in key or key in prod_key) and _version_less_than(version, min_ver):
            return min_ver
    return None


def _detect_from_headers(response: "httpx.Response") -> tuple[list[StackEntry], list[VulnerableVersion]]:
    """Détecte serveur, runtime et versions depuis les en-têtes."""
    entries: list[StackEntry] = []
    vulnerable: list[VulnerableVersion] = []

    server = get_header_insensitive(response, "Server")
    if server:
        version = _parse_version(server)
        product = _parse_product_from_header(server) or "server"
        conf = _CONFIDENCE_HEADER_VERSION if version else _CONFIDENCE_HEADER_RAW
        entries.append(StackEntry(product=product, version=version, confidence=conf, source="header_server"))
        if version:
            min_safe = _check_vulnerable(product, version)
            if min_safe:
                vulnerable.append(VulnerableVersion(product=product, version=version, min_safe_version=min_safe))

    x_powered_by = get_header_insensitive(response, "X-Powered-By")
    if x_powered_by:
        version = _parse_version(x_powered_by)
        product = _parse_product_from_header(x_powered_by) or "runtime"
        conf = _CONFIDENCE_HEADER_VERSION if version else _CONFIDENCE_HEADER_RAW
        entries.append(StackEntry(product=product, version=version, confidence=conf, source="header_x_powered_by"))
        if version:
            min_safe = _check_vulnerable(product, version)
            if min_safe:
                vulnerable.append(VulnerableVersion(product=product, version=version, min_safe_version=min_safe))

    return entries, vulnerable


def _detect_framework_cms_from_headers(response: "httpx.Response") -> tuple[str | None, str | None]:
    """Détecte framework/CMS via heuristiques sur les en-têtes. Retourne (nom, version)."""
    x_generator = get_header_insensitive(response, "X-Generator")
    x_drupal_cache = get_header_insensitive(response, "X-Drupal-Cache")
    x_powered_by = get_header_insensitive(response, "X-Powered-By") or ""

    if x_drupal_cache is not None:
        return "Drupal", None
    if x_generator and "drupal" in x_generator.lower():
        return "Drupal", _parse_version(x_generator)
    if x_generator and "wordpress" in x_generator.lower():
        return "WordPress", _parse_version(x_generator)
    if "express" in x_powered_by.lower():
        return "Express", _parse_version(x_powered_by)
    if "asp.net" in x_powered_by.lower():
        return "ASP.NET", _parse_version(x_powered_by)
    if "php" in x_powered_by.lower():
        return "PHP", _parse_version(x_powered_by)
    return None, None


def _detect_from_html(html: str) -> list[StackEntry]:
    """Détecte technologies via balises HTML (meta generator, scripts)."""
    entries: list[StackEntry] = []
    if not html or len(html) > 500_000:
        return entries

    html_lower = html.lower()

    # <meta name="generator" content="WordPress 6.4.2">
    meta_gen = re.search(r'<meta\s+name=["\']generator["\']\s+content=["\']([^"\']+)["\']', html_lower, re.I)
    if meta_gen:
        content = meta_gen.group(1)
        if "wordpress" in content.lower():
            ver = _parse_version(content)
            entries.append(StackEntry(product="wordpress", version=ver, confidence=_CONFIDENCE_HTML_META, source="html_meta"))
        elif "drupal" in content.lower():
            ver = _parse_version(content)
            entries.append(StackEntry(product="drupal", version=ver, confidence=_CONFIDENCE_HTML_META, source="html_meta"))

    # Scripts : wp-content, wp-includes, react, vue, jquery
    if "wp-content" in html_lower or "wp-includes" in html_lower:
        entries.append(StackEntry(product="wordpress", version=None, confidence=_CONFIDENCE_HTML_SCRIPT, source="html_script"))
    if "react" in html_lower and "reactdom" in html_lower:
        entries.append(StackEntry(product="react", version=None, confidence=_CONFIDENCE_HTML_SCRIPT, source="html_script"))
    if "vue.js" in html_lower or "vue.min.js" in html_lower:
        entries.append(StackEntry(product="vue", version=None, confidence=_CONFIDENCE_HTML_SCRIPT, source="html_script"))
    if "jquery" in html_lower:
        entries.append(StackEntry(product="jquery", version=None, confidence=_CONFIDENCE_HTML_SCRIPT, source="html_script"))

    return entries


def _merge_stack_entries(header_entries: list[StackEntry], html_entries: list[StackEntry]) -> tuple[StackEntry, ...]:
    """Fusionne les entrées headers et HTML, évite les doublons (garder la plus haute confiance)."""
    by_product: dict[str, StackEntry] = {}
    for e in header_entries + html_entries:
        key = e.product.lower()
        if key not in by_product or e.confidence > by_product[key].confidence:
            by_product[key] = e
    return tuple(sorted(by_product.values(), key=lambda x: -x.confidence))


def _add_framework_cms_if_missing(
    header_entries: list[StackEntry],
    vulnerable: list[VulnerableVersion],
    framework_cms: str,
    framework_cms_version: str | None,
) -> None:
    """Ajoute framework_cms aux entries si pas déjà présent ; enregistre version vulnérable si applicable."""
    if any(e.product.lower() == framework_cms.lower() for e in header_entries):
        return
    conf = _CONFIDENCE_HEADER_VERSION if framework_cms_version else _CONFIDENCE_HEADER_RAW
    header_entries.append(
        StackEntry(
            product=framework_cms,
            version=framework_cms_version,
            confidence=conf,
            source="header_x_generator",
        )
    )
    if framework_cms_version:
        min_safe = _check_vulnerable(framework_cms, framework_cms_version)
        if min_safe:
            vulnerable.append(
                VulnerableVersion(
                    product=framework_cms,
                    version=framework_cms_version,
                    min_safe_version=min_safe,
                )
            )


def _build_findings(
    server: str | None,
    server_version: str | None,
    x_powered_by: str | None,
    runtime_version: str | None,
    framework_cms: str | None,
    framework_cms_version: str | None,
    vulnerable: list[VulnerableVersion],
) -> tuple[str, ...]:
    """Construit la liste des findings à partir des données extraites."""
    findings: list[str] = []
    if server:
        findings.append(f"Serveur détecté : {server}" + (f" (version {server_version})" if server_version else ""))
    if x_powered_by:
        findings.append(f"Runtime : {x_powered_by}" + (f" (version {runtime_version})" if runtime_version else ""))
    if framework_cms:
        findings.append(f"Framework/CMS probable : {framework_cms}" + (f" {framework_cms_version}" if framework_cms_version else ""))
    for v in vulnerable:
        findings.append(f"Version potentiellement vulnérable : {v.product} {v.version} (version minimale recommandée : {v.min_safe_version})")
    if not findings:
        findings.append("Stack : non identifiée (ou masquée)")
    return tuple(findings)


def check_tech_fingerprinting_from_response(
    response: "httpx.Response | None",
    *,
    scan_type: str = "frontend",
) -> TechFingerprintingCheckResult:
    """Analyse en-têtes et HTML pour un fingerprinting technologique complet.

    Extrait les versions, détecte via HTML, vérifie les versions vulnérables,
    produit une stack avec niveaux de confiance.

    Args:
        response: Réponse HTTP (ou None si le fetch a échoué).

    Returns:
        TechFingerprintingCheckResult: Stack, versions vulnérables, findings.
    """
    if response is None:
        return TechFingerprintingCheckResult(
            server=None,
            server_version=None,
            runtime=None,
            runtime_version=None,
            framework_cms=None,
            framework_cms_version=None,
            stack_entries=(),
            vulnerable_versions=(),
            findings=(MSG_HEADERS_ANALYSIS_UNAVAILABLE,),
            fetch_ok=False,
        )

    header_entries, vulnerable = _detect_from_headers(response)
    framework_cms, framework_cms_version = _detect_framework_cms_from_headers(response)

    if framework_cms:
        _add_framework_cms_if_missing(header_entries, vulnerable, framework_cms, framework_cms_version)

    html_entries = _detect_from_html(response.text or "") if scan_type != "backend" and hasattr(response, "text") else []
    stack_entries = _merge_stack_entries(header_entries, html_entries)

    server = get_header_insensitive(response, "Server")
    x_powered_by = get_header_insensitive(response, "X-Powered-By")
    server_version = _parse_version(server) if server else None
    runtime_version = _parse_version(x_powered_by) if x_powered_by else None
    findings = _build_findings(server, server_version, x_powered_by, runtime_version, framework_cms, framework_cms_version, vulnerable)

    return TechFingerprintingCheckResult(
        server=server,
        server_version=server_version,
        runtime=x_powered_by,
        runtime_version=runtime_version,
        framework_cms=framework_cms,
        framework_cms_version=framework_cms_version,
        stack_entries=stack_entries,
        vulnerable_versions=tuple(vulnerable),
        findings=tuple(findings),
        fetch_ok=True,
    )
