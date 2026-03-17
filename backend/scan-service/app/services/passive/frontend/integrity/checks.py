"""Vérifications Intégrité et sous-ressources (SRI + analyse HTML).

Ce module implémente les contrôles décrits dans
``docs/verifications/integrite-et-sous-ressources.md`` :

- détection des scripts et feuilles de style externes sans attribut SRI
  (``integrity``) ;
- vérifications optionnelles liées à CSP sur les balises ``<script>`` ;
- formulaires avec champs password sans attribut ``autocomplete`` adapté ;
- liens ``target="_blank"`` sans ``rel="noopener noreferrer"`` ;
- meta ``robots`` manquante sur certaines pages sensibles (login, admin, API) ;
- formulaires POST sans champ CSRF détecté (csrf_token, _token, etc.).

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
            "robots_no_noindex", "forms_post_without_csrf", "connection_failed".
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


@dataclass
class _IntegrityHTMLInfo:
    """Informations extraites du HTML pour les checks d'intégrité."""

    external_without_sri: list[str]
    inline_scripts_without_nonce: int
    password_fields_weak_autocomplete: int
    target_blank_without_noopener: int
    robots_meta_present: bool
    robots_has_noindex: bool
    forms_post_without_csrf: int


class _IntegrityHTMLParser(HTMLParser):
    """Parser HTML minimal pour extraire les éléments utiles aux checks."""

    _SCRIPT: Final[str] = "script"
    _LINK: Final[str] = "link"
    _INPUT: Final[str] = "input"
    _A: Final[str] = "a"
    _META: Final[str] = "meta"
    _FORM: Final[str] = "form"

    def __init__(
        self,
        base_url: str,
        base_host: str,
        csrf_field_names: tuple[str, ...],
    ) -> None:
        super().__init__(convert_charrefs=True)
        self._base_url = base_url
        self._base_host = base_host
        self._csrf_names = frozenset(n.lower() for n in csrf_field_names)
        self._form_stack: list[dict] = []
        self._data = _IntegrityHTMLInfo(
            external_without_sri=[],
            inline_scripts_without_nonce=0,
            password_fields_weak_autocomplete=0,
            target_blank_without_noopener=0,
            robots_meta_present=False,
            robots_has_noindex=False,
            forms_post_without_csrf=0,
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
        elif tag_lower == self._FORM:
            self._handle_form_start(attr_map)
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

    def _handle_form_start(self, attrs: dict[str, str]) -> None:
        """Ouverture d'un <form>. Évalue le formulaire précédent si existant."""
        self._close_current_form()
        method = (attrs.get("method") or "get").lower()
        if method == "post":
            self._form_stack.append({"method": "post", "has_csrf": False})

    def _close_current_form(self) -> None:
        """Évalue et ferme le formulaire en cours."""
        if not self._form_stack:
            return
        f = self._form_stack.pop()
        if f.get("method") == "post" and not f.get("has_csrf"):
            self._data.forms_post_without_csrf += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == self._FORM:
            self._close_current_form()

    def close(self) -> None:
        """Ferme le parser et traite les formulaires non fermés correctement."""
        self._close_current_form()
        super().close()

    def _handle_input(self, attrs: dict[str, str]) -> None:
        input_type = (attrs.get("type") or "text").lower()
        if input_type == "hidden" and self._form_stack:
            name = (attrs.get("name") or "").strip().lower()
            if name and name in self._csrf_names:
                self._form_stack[-1]["has_csrf"] = True
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


def _analyze_html(
    html: str,
    page_url: str,
    csrf_field_names: tuple[str, ...],
) -> _IntegrityHTMLInfo:
    """Analyse le HTML pour extraire les informations d'intégrité."""
    parsed = urlparse(page_url)
    base_host = parsed.netloc.lower()
    parser = _IntegrityHTMLParser(
        base_url=page_url,
        base_host=base_host,
        csrf_field_names=csrf_field_names,
    )
    try:
        parser.feed(html)
    except Exception:
        pass
    parser.close()
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


def _issue_sri_missing(info: _IntegrityHTMLInfo) -> IntegrityIssue | None:
    if not info.external_without_sri:
        return None
    limited = info.external_without_sri[:5]
    extra = len(info.external_without_sri) - len(limited)
    urls_snippet = ", ".join(limited)
    if extra > 0:
        urls_snippet = f"{urls_snippet}, … (+{extra} autres)"
    msg = (
        f"Ressources externes sans SRI détectées : {len(info.external_without_sri)} script(s)/CSS sans attribut integrity "
        f"(exemples : {urls_snippet})."
    )
    return IntegrityIssue(kind="sri_missing", message=msg)


def _issue_csp_or_inline(info: _IntegrityHTMLInfo, response: httpx.Response) -> IntegrityIssue | None:
    csp_header = get_header_insensitive(response, "Content-Security-Policy")
    csp_present = bool(csp_header and csp_header.strip())
    if not csp_present:
        return IntegrityIssue(
            kind="csp_absent",
            message="Aucune Content-Security-Policy détectée : les tests avancés sur les scripts (nonces/hashes) n'ont pas été appliqués.",
        )
    if info.inline_scripts_without_nonce > 0:
        return IntegrityIssue(
            kind="inline_no_nonce",
            message=(
                f"Scripts inline sans nonce détectés alors qu'une CSP est présente : "
                f"{info.inline_scripts_without_nonce} balise(s) <script> sans attribut nonce."
            ),
        )
    return None


def _issue_robots_on_sensitive(info: _IntegrityHTMLInfo, page_url: str) -> IntegrityIssue | None:
    parsed = urlparse(page_url)
    path = parsed.path or "/"
    settings = get_integrity_settings()
    if not any(path.startswith(p) for p in settings.sensitive_paths):
        return None
    if not info.robots_meta_present:
        return IntegrityIssue(
            kind="robots_missing",
            message="Meta robots absente sur une page sensible : aucune directive noindex définie pour cette URL.",
        )
    if not info.robots_has_noindex:
        return IntegrityIssue(
            kind="robots_no_noindex",
            message="Meta robots présente mais sans noindex sur une page sensible : envisager d'ajouter noindex.",
        )
    return None


def _build_integrity_issues(info: _IntegrityHTMLInfo, response: httpx.Response, page_url: str) -> list[IntegrityIssue]:
    """Construit les issues typées à partir du HTML analysé."""
    issues: list[IntegrityIssue] = []

    if sri := _issue_sri_missing(info):
        issues.append(sri)
    if csp := _issue_csp_or_inline(info, response):
        issues.append(csp)
    if info.password_fields_weak_autocomplete > 0:
        issues.append(
            IntegrityIssue(
                kind="password_autocomplete",
                message=(
                    f"Champs password sans autocomplete explicite détectés : "
                    f"{info.password_fields_weak_autocomplete} champ(s) avec un attribut autocomplete manquant ou trop permissif."
                ),
            )
        )
    if info.target_blank_without_noopener > 0:
        issues.append(
            IntegrityIssue(
                kind="target_blank",
                message=(
                    'Liens target="_blank" sans rel="noopener" détectés : '
                    f"{info.target_blank_without_noopener} lien(s) vulnérable(s) au tabnabbing potentiel."
                ),
            )
        )
    if robots := _issue_robots_on_sensitive(info, page_url):
        issues.append(robots)
    if info.forms_post_without_csrf > 0:
        n = info.forms_post_without_csrf
        mot, det = ("formulaire", "détecté") if n == 1 else ("formulaires", "détectés")
        issues.append(IntegrityIssue(kind="forms_post_without_csrf", message=f"{n} {mot} POST sans champ CSRF {det}."))

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

    info = _analyze_html(html, page_url, settings.csrf_field_names)
    issues = _build_integrity_issues(info, response, page_url)
    findings = tuple(issue.message for issue in issues)

    return IntegrityCheckResult(findings=findings, fetch_ok=True, issues=tuple(issues))
