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

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Final
from urllib.parse import urljoin, urlparse

import httpx

from app.config_loader import get_integrity_settings
from app.utils.headers import get_header_insensitive


@dataclass(frozen=True)
class IntegrityCheckResult:
    """Résultat des vérifications d'intégrité et de sous-ressources.

    Attributes:
        findings (tuple[str, ...]): Messages bruts décrivant les problèmes
            détectés (SRI manquant, autocomplete absent, etc.).
        fetch_ok (bool): Indique si la réponse HTTPS a pu être analysée. False
            si la réponse est absente ou illisible.
    """

    findings: tuple[str, ...]
    fetch_ok: bool


@dataclass(frozen=True)
class _IntegrityHTMLInfo:
    """Informations extraites du HTML pour les checks d'intégrité.

    Attributes:
        external_without_sri (list[str]): URLs de scripts/CSS externes sans
            attribut ``integrity``.
        inline_scripts_without_nonce (int): Nombre de balises ``<script>``
            inline sans attribut ``nonce`` (dans un contexte CSP).
        password_fields_weak_autocomplete (int): Nombre de champs password
            sans ``autocomplete`` approprié.
        target_blank_without_noopener (int): Nombre de liens ``target="_blank"``
            sans ``rel="noopener noreferrer"``.
        robots_meta_present (bool): Indique si une meta ``name="robots"`` a
            été trouvée.
        robots_has_noindex (bool): Indique si au moins une meta robots contient
            ``noindex``.
    """

    external_without_sri: list[str]
    inline_scripts_without_nonce: int
    password_fields_weak_autocomplete: int
    target_blank_without_noopener: int
    robots_meta_present: bool
    robots_has_noindex: bool


class _IntegrityHTMLParser(HTMLParser):
    """Parser HTML minimal pour extraire les éléments utiles aux checks.

    Ce parser analyse :

    - ``<script src>`` et ``<link rel="stylesheet" href>`` pour les checks SRI ;
    - ``<script>`` inline pour les nonces CSP ;
    - ``<input type="password">`` pour les attributs ``autocomplete`` ;
    - ``<a target="_blank">`` pour les attributs ``rel`` ;
    - ``<meta name="robots" content="...">`` pour les directives ``noindex``.
    """

    _SCRIPT: Final[str] = "script"
    _LINK: Final[str] = "link"
    _INPUT: Final[str] = "input"
    _A: Final[str] = "a"
    _META: Final[str] = "meta"

    def __init__(self, base_url: str, base_host: str) -> None:
        """Initialise le parser avec l'URL et le host de base.

        Args:
            base_url: URL absolue de la page principale.
            base_host: Host (netloc) de la page principale pour distinguer
                les ressources externes.
        """
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
        """Retourne les informations agrégées après le parsing."""
        return self._data

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Gère les balises d'ouverture utiles aux vérifications.

        Args:
            tag: Nom de la balise HTML.
            attrs: Liste des attributs (nom, valeur) de la balise.
        """
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
        """Traite une balise ``<script>`` pour SRI et CSP.

        Args:
            attrs: Attributs de la balise script.
        """
        src = attrs.get("src") or ""
        integrity = attrs.get("integrity") or ""
        nonce = attrs.get("nonce") or ""

        if src:
            # Script externe : on vérifie uniquement si le domaine est différent.
            absolute = urljoin(self._base_url, src)
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                return
            if parsed.netloc.lower() == self._base_host:
                return
            if not integrity.strip():
                self._data.external_without_sri.append(absolute)
            return

        # Script inline : utilisé pour les checks CSP (nonce) si CSP présente.
        if not nonce:
            self._data.inline_scripts_without_nonce += 1

    def _handle_link(self, attrs: dict[str, str]) -> None:
        """Traite une balise ``<link>`` pour SRI sur les CSS externes.

        Args:
            attrs: Attributs de la balise link.
        """
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
        """Traite une balise ``<input>`` pour l'autocomplete des mots de passe.

        Args:
            attrs: Attributs de la balise input.
        """
        input_type = (attrs.get("type") or "").lower()
        if input_type != "password":
            return
        autocomplete = (attrs.get("autocomplete") or "").lower()
        if autocomplete in {"off", "new-password", "current-password"}:
            return
        self._data.password_fields_weak_autocomplete += 1

    def _handle_anchor(self, attrs: dict[str, str]) -> None:
        """Traite une balise ``<a>`` pour target/_blank et rel.

        Args:
            attrs: Attributs de la balise lien.
        """
        target = (attrs.get("target") or "").lower()
        if target != "_blank":
            return
        rel = (attrs.get("rel") or "").lower()
        # On exige au moins noopener ; noreferrer est recommandé mais optionnel.
        if "noopener" not in rel:
            self._data.target_blank_without_noopener += 1

    def _handle_meta(self, attrs: dict[str, str]) -> None:
        """Traite une balise ``<meta>`` pour les directives robots.

        Args:
            attrs: Attributs de la balise meta.
        """
        name = (attrs.get("name") or "").lower()
        if name != "robots":
            return
        content = (attrs.get("content") or "").lower()
        self._data.robots_meta_present = True
        if "noindex" in content:
            self._data.robots_has_noindex = True


def _analyze_html(html: str, page_url: str) -> _IntegrityHTMLInfo:
    """Analyse le HTML pour extraire les informations d'intégrité.

    Args:
        html: Corps HTML tronqué de la page principale.
        page_url: URL absolue de la page principale.

    Returns:
        _IntegrityHTMLInfo: Informations agrégées issues du parsing.
    """
    parsed = urlparse(page_url)
    base_host = parsed.netloc.lower()
    parser = _IntegrityHTMLParser(base_url=page_url, base_host=base_host)
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # En cas d'erreur de parsing, on retourne les données collectées jusque-là.
        return parser.data
    return parser.data


def _extract_html_from_response(response: httpx.Response, max_body_bytes: int) -> tuple[str | None, IntegrityCheckResult | None]:
    """Extrait le HTML tronqué ou retourne un résultat d'erreur.

    Args:
        response: Réponse HTTPS principale.
        max_body_bytes: Taille maximale de HTML à analyser.

    Returns:
        tuple[str | None, IntegrityCheckResult | None]: (html, résultat d'erreur éventuel).
    """
    try:
        text = response.text or ""
    except Exception:
        return None, IntegrityCheckResult(
            findings=("Vérifications d'intégrité impossibles : corps de réponse illisible.",),
            fetch_ok=False,
        )

    if not text:
        return "", IntegrityCheckResult(findings=(), fetch_ok=True)

    return text[:max_body_bytes], None


def _build_integrity_findings(info: _IntegrityHTMLInfo, response: httpx.Response, page_url: str) -> list[str]:
    """Construit la liste des messages de findings à partir du HTML analysé.

    Args:
        info: Informations extraites du HTML.
        response: Réponse HTTPS principale.
        page_url: URL de la page principale.

    Returns:
        list[str]: Messages bruts décrivant les problèmes détectés.
    """
    findings: list[str] = []

    # 1) SRI : scripts/CSS externes sans attribut integrity.
    if info.external_without_sri:
        limited = info.external_without_sri[:5]
        extra = len(info.external_without_sri) - len(limited)
        urls_snippet = ", ".join(limited)
        if extra > 0:
            urls_snippet = f"{urls_snippet}, … (+{extra} autres)"
        findings.append(
            f"Ressources externes sans SRI détectées : {len(info.external_without_sri)} script(s)/CSS sans attribut integrity "
            f"(exemples : {urls_snippet}).",
        )

    # 2) Scripts inline sans nonce : uniquement si CSP présente (sinon tests avancés non appliqués).
    csp_header = get_header_insensitive(response, "Content-Security-Policy")
    csp_present = bool(csp_header and csp_header.strip())
    if not csp_present:
        findings.append(
            "Aucune Content-Security-Policy détectée : les tests avancés sur les scripts (nonces/hashes) n'ont pas été appliqués.",
        )
    elif info.inline_scripts_without_nonce > 0:
        findings.append(
            "Scripts inline sans nonce détectés alors qu'une CSP est présente : "
            f"{info.inline_scripts_without_nonce} balise(s) <script> sans attribut nonce.",
        )

    # 3) Formulaires / champs password sans autocomplete adapté.
    if info.password_fields_weak_autocomplete > 0:
        findings.append(
            "Champs password sans autocomplete explicite détectés : "
            f"{info.password_fields_weak_autocomplete} champ(s) avec un attribut autocomplete manquant ou trop permissif.",
        )

    # 4) Liens target="_blank" sans rel="noopener".
    if info.target_blank_without_noopener > 0:
        findings.append(
            'Liens target="_blank" sans rel="noopener" détectés : '
            f"{info.target_blank_without_noopener} lien(s) vulnérable(s) au tabnabbing potentiel.",
        )

    # 5) Meta robots sur pages sensibles (noindex recommandé).
    parsed = urlparse(page_url)
    path = parsed.path or "/"
    settings = get_integrity_settings()
    if any(path.startswith(p) for p in settings.sensitive_paths):
        if not info.robots_meta_present:
            findings.append(
                "Meta robots absente sur une page sensible : aucune directive noindex définie pour cette URL.",
            )
        elif not info.robots_has_noindex:
            findings.append(
                "Meta robots présente mais sans noindex sur une page sensible : envisager d'ajouter noindex.",
            )

    return findings


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
        return IntegrityCheckResult(
            findings=("Vérifications d'intégrité impossibles : réponse HTTPS indisponible.",),
            fetch_ok=False,
        )

    settings = get_integrity_settings()
    html, error_result = _extract_html_from_response(response, settings.max_body_bytes)
    if error_result is not None:
        return error_result
    if html == "":
        return IntegrityCheckResult(findings=(), fetch_ok=True)

    info = _analyze_html(html, page_url)
    findings = _build_integrity_findings(info, response, page_url)

    return IntegrityCheckResult(findings=tuple(findings), fetch_ok=True)
