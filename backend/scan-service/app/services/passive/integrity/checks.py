"""Vérifications Intégrité et sous-ressources (SRI + analyse HTML).

Ce module implémente les contrôles décrits dans
``docs/verifications/integrite-et-sous-ressources.md`` :

- détection des scripts et feuilles de style externes sans attribut SRI
  (``integrity``) ;
- vérifications optionnelles liées à CSP sur les balises ``<script>`` ;
- formulaires avec champs password sans attribut ``autocomplete`` adapté ;
- liens ``target="_blank"`` sans ``rel="noopener noreferrer"`` ;
- meta ``robots`` manquante sur certaines pages sensibles (login, admin, API).

Les vérifications restent passives : seule la réponse HTTPS principale
(headers + corps tronqué) est analysée, sans requêtes supplémentaires pour
recalculer les hashes SRI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Final
from urllib.parse import urljoin, urlparse

import httpx

from app.config_loader import get_integrity_settings
from app.utils.headers import get_header_insensitive


@dataclass(frozen=True)
class IntegrityIssue:
    """Issue d'intégrité typée pour une normalisation sans correspondance de chaînes.

    Attributes:
        kind: Discriminant sémantique du problème.
            Valeurs possibles : "sri_missing", "csp_absent", "inline_no_nonce",
            "password_autocomplete", "target_blank", "robots_missing",
            "robots_no_noindex", "connection_failed".
        message: Message lisible pour l'affichage SSE et le rapport.
    """

    kind: str
    message: str


@dataclass(frozen=True)
class IntegrityCheckResult:
    """Résultat des vérifications d'intégrité et de sous-ressources.

    Attributes:
        findings (tuple[str, ...]): Messages bruts pour la sérialisation SSE
            (compat ascendante). Dérivés des ``issues``.
        fetch_ok (bool): Indique si la réponse HTTPS a pu être analysée.
        issues (tuple[IntegrityIssue, ...]): Issues typées consommées par le normalizer
            sans correspondance de chaînes.
    """

    findings: tuple[str, ...]
    fetch_ok: bool
    issues: tuple[IntegrityIssue, ...] = field(default=())


@dataclass(frozen=True)
class _IntegrityHTMLInfo:
    """Informations extraites du HTML pour les checks d'intégrité."""

    external_without_sri: list[str]
    inline_scripts_without_nonce: int
    password_fields_weak_autocomplete: int
    target_blank_without_noopener: int
    robots_meta_present: bool
    robots_has_noindex: bool


class _IntegrityHTMLParser(HTMLParser):
    """Parser HTML minimal pour extraire les éléments utiles aux checks."""

    _SCRIPT: Final[str] = "script"
    _LINK: Final[str] = "link"
    _INPUT: Final[str] = "input"
    _A: Final[str] = "a"
    _META: Final[str] = "meta"

    def __init__(self, base_url: str, base_host: str) -> None:
        super().__init__(convert_charrefs=True)
        self._base_url = base_url
        self._base_host = base_host
        self._data = _IntegrityHTMLInfo(
            external_without_sri=[],
            inline_scripts_without_nonce=0,
            password_fields_weak_autocomplete=0,
            target_blank_without_noopener=0,
            robots_meta_present=False,
            robots_has_noindex=False,
        )

    @property
    def data(self) -> _IntegrityHTMLInfo:
        return self._data

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        attr_map = {name.lower(): (value or "") for name, value in attrs}

        if tag_lower == self._SCRIPT:
            self._handle_script(attr_map)
        elif tag_lower == self._LINK:
            self._handle_link(attr_map)
        elif tag_lower == self._INPUT:
            self._handle_input(attr_map)
        elif tag_lower == self._A:
            self._handle_anchor(attr_map)
        elif tag_lower == self._META:
            self._handle_meta(attr_map)

    def _handle_script(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src") or ""
        integrity = attrs.get("integrity") or ""
        nonce = attrs.get("nonce") or ""

        if src:
            absolute = urljoin(self._base_url, src)
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                return
            if parsed.netloc.lower() == self._base_host:
                return
            if not integrity.strip():
                self._data.external_without_sri.append(absolute)
            return

        if not nonce:
            self._data.inline_scripts_without_nonce += 1

    def _handle_link(self, attrs: dict[str, str]) -> None:
        rel = attrs.get("rel", "").lower()
        href = attrs.get("href") or ""
        integrity = attrs.get("integrity") or ""
        if "stylesheet" not in rel or not href:
            return
        absolute = urljoin(self._base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return
        if parsed.netloc.lower() == self._base_host:
            return
        if not integrity.strip():
            self._data.external_without_sri.append(absolute)

    def _handle_input(self, attrs: dict[str, str]) -> None:
        input_type = (attrs.get("type") or "").lower()
        if input_type != "password":
            return
        autocomplete = (attrs.get("autocomplete") or "").lower()
        if autocomplete in {"off", "new-password", "current-password"}:
            return
        self._data.password_fields_weak_autocomplete += 1

    def _handle_anchor(self, attrs: dict[str, str]) -> None:
        target = (attrs.get("target") or "").lower()
        if target != "_blank":
            return
        rel = (attrs.get("rel") or "").lower()
        if "noopener" not in rel:
            self._data.target_blank_without_noopener += 1

    def _handle_meta(self, attrs: dict[str, str]) -> None:
        name = (attrs.get("name") or "").lower()
        if name != "robots":
            return
        content = (attrs.get("content") or "").lower()
        self._data.robots_meta_present = True
        if "noindex" in content:
            self._data.robots_has_noindex = True


def _analyze_html(html: str, page_url: str) -> _IntegrityHTMLInfo:
    """Analyse le HTML pour extraire les informations d'intégrité."""
    parsed = urlparse(page_url)
    base_host = parsed.netloc.lower()
    parser = _IntegrityHTMLParser(base_url=page_url, base_host=base_host)
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return parser.data
    return parser.data


def _extract_html_from_response(response: httpx.Response, max_body_bytes: int) -> tuple[str | None, IntegrityCheckResult | None]:
    """Extrait le HTML tronqué ou retourne un résultat d'erreur."""
    try:
        text = response.text or ""
    except Exception:
        msg = "Vérifications d'intégrité impossibles : corps de réponse illisible."
        issue = IntegrityIssue(kind="connection_failed", message=msg)
        return None, IntegrityCheckResult(findings=(msg,), fetch_ok=False, issues=(issue,))

    if not text:
        return "", IntegrityCheckResult(findings=(), fetch_ok=True)

    return text[:max_body_bytes], None


def _build_integrity_issues(info: _IntegrityHTMLInfo, response: httpx.Response, page_url: str) -> list[IntegrityIssue]:
    """Construit les issues typées à partir du HTML analysé.

    Args:
        info: Informations extraites du HTML.
        response: Réponse HTTPS principale.
        page_url: URL de la page principale.

    Returns:
        list[IntegrityIssue]: Issues typées prêtes pour le normalizer.
    """
    issues: list[IntegrityIssue] = []

    if info.external_without_sri:
        limited = info.external_without_sri[:5]
        extra = len(info.external_without_sri) - len(limited)
        urls_snippet = ", ".join(limited)
        if extra > 0:
            urls_snippet = f"{urls_snippet}, … (+{extra} autres)"
        msg = (
            f"Ressources externes sans SRI détectées : {len(info.external_without_sri)} script(s)/CSS sans attribut integrity "
            f"(exemples : {urls_snippet})."
        )
        issues.append(IntegrityIssue(kind="sri_missing", message=msg))

    csp_header = get_header_insensitive(response, "Content-Security-Policy")
    csp_present = bool(csp_header and csp_header.strip())
    if not csp_present:
        msg = "Aucune Content-Security-Policy détectée : les tests avancés sur les scripts (nonces/hashes) n'ont pas été appliqués."
        issues.append(IntegrityIssue(kind="csp_absent", message=msg))
    elif info.inline_scripts_without_nonce > 0:
        msg = (
            "Scripts inline sans nonce détectés alors qu'une CSP est présente : "
            f"{info.inline_scripts_without_nonce} balise(s) <script> sans attribut nonce."
        )
        issues.append(IntegrityIssue(kind="inline_no_nonce", message=msg))

    if info.password_fields_weak_autocomplete > 0:
        msg = (
            "Champs password sans autocomplete explicite détectés : "
            f"{info.password_fields_weak_autocomplete} champ(s) avec un attribut autocomplete manquant ou trop permissif."
        )
        issues.append(IntegrityIssue(kind="password_autocomplete", message=msg))

    if info.target_blank_without_noopener > 0:
        msg = (
            'Liens target="_blank" sans rel="noopener" détectés : '
            f"{info.target_blank_without_noopener} lien(s) vulnérable(s) au tabnabbing potentiel."
        )
        issues.append(IntegrityIssue(kind="target_blank", message=msg))

    parsed = urlparse(page_url)
    path = parsed.path or "/"
    settings = get_integrity_settings()
    if any(path.startswith(p) for p in settings.sensitive_paths):
        if not info.robots_meta_present:
            msg = "Meta robots absente sur une page sensible : aucune directive noindex définie pour cette URL."
            issues.append(IntegrityIssue(kind="robots_missing", message=msg))
        elif not info.robots_has_noindex:
            msg = "Meta robots présente mais sans noindex sur une page sensible : envisager d'ajouter noindex."
            issues.append(IntegrityIssue(kind="robots_no_noindex", message=msg))

    return issues


def check_integrity_from_response(response: httpx.Response | None, page_url: str) -> IntegrityCheckResult:
    """Vérifie l'intégrité et les bonnes pratiques HTML de la page principale.

    Cette fonction est appelée par la pipeline de scan après la récupération
    de la page HTTPS principale. Elle reste purement passive : aucune requête
    réseau supplémentaire n'est effectuée.

    Args:
        response: Réponse HTTPS principale (peut être None si indisponible).
        page_url: URL absolue de la page principale.

    Returns:
        IntegrityCheckResult: Résultat agrégé des vérifications.
    """
    if response is None:
        msg = "Vérifications d'intégrité impossibles : réponse HTTPS indisponible."
        issue = IntegrityIssue(kind="connection_failed", message=msg)
        return IntegrityCheckResult(findings=(msg,), fetch_ok=False, issues=(issue,))

    settings = get_integrity_settings()
    html, error_result = _extract_html_from_response(response, settings.max_body_bytes)
    if error_result is not None:
        return error_result
    if html == "":
        return IntegrityCheckResult(findings=(), fetch_ok=True)

    info = _analyze_html(html, page_url)
    issues = _build_integrity_issues(info, response, page_url)
    findings = tuple(issue.message for issue in issues)

    return IntegrityCheckResult(findings=findings, fetch_ok=True, issues=tuple(issues))
