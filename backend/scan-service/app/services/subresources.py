"""Extraction des sous-ressources HTML (scripts, feuilles de style, images).

Ce module fournit un utilitaire générique pour analyser le HTML d'une page et
en extraire les URLs de sous-ressources :

- balises ``<script src="...">`` ;
- balises ``<link rel="stylesheet" href="...">`` ;
- balises ``<img src="...">``.

Les URLs retournées sont normalisées en URLs absolues par rapport à l'URL de
base et limitées à un nombre maximal configuré. L'utilitaire est pensé pour
être utilisé par les vérifications non intrusives (cache, SRI, etc.).
"""

import contextlib
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Final
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class _RawSubresource:
    """Représente une sous-ressource extraite du HTML.

    Attributes:
        tag (str): Nom de la balise HTML (script, link, img).
        url (str): URL absolue de la ressource.
    """

    tag: str
    url: str


class _SubresourceHTMLParser(HTMLParser):
    """Parser HTML minimal pour extraire scripts, CSS et images.

    Ce parser ne gère que les balises nécessaires au scan :
    - ``<script src="...">``
    - ``<link rel="stylesheet" href="...">``
    - ``<img src="...">``
    """

    _SCRIPT: Final[str] = "script"
    _LINK: Final[str] = "link"
    _IMG: Final[str] = "img"

    def __init__(self, base_url: str) -> None:
        """Initialise le parser avec une URL de base.

        Args:
            base_url: URL absolue de la page principale utilisée pour normaliser
                les URLs relatives extraites depuis le HTML.
        """
        super().__init__(convert_charrefs=True)
        self._base_url = base_url
        self._raw: list[_RawSubresource] = []

    @property
    def raw_subresources(self) -> list[_RawSubresource]:
        """Retourne la liste des sous-ressources extraites."""
        return self._raw

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Gère les balises d'ouverture pertinentes pour l'extraction.

        Args:
            tag: Nom de la balise HTML.
            attrs: Liste des attributs (nom, valeur) de la balise.
        """
        tag_lower = tag.lower()
        if tag_lower not in (self._SCRIPT, self._LINK, self._IMG):
            return

        attr_map = {name.lower(): (value or "") for name, value in attrs}

        if tag_lower == self._SCRIPT:
            src = attr_map.get("src")
            if src:
                self._add_resource(tag_lower, src)
        elif tag_lower == self._LINK:
            rel = attr_map.get("rel", "").lower()
            href = attr_map.get("href")
            if "stylesheet" in rel and href:
                self._add_resource(tag_lower, href)
        elif tag_lower == self._IMG:
            src = attr_map.get("src")
            if src:
                self._add_resource(tag_lower, src)

    def _add_resource(self, tag: str, url: str) -> None:
        """Ajoute une ressource si l'URL est valide et non vide.

        Args:
            tag: Nom de la balise HTML.
            url: URL brute extraite de la balise.
        """
        absolute = urljoin(self._base_url, url)
        parsed = urlparse(absolute)
        if not parsed.scheme or not parsed.netloc:
            return
        self._raw.append(_RawSubresource(tag=tag, url=absolute))


def _subresource_sort_key(url: str, tag: str) -> tuple[int, str]:
    """Clé de tri pour prioriser scripts > link > img.

    Args:
        url: URL de la ressource.
        tag: Nom de la balise HTML.

    Returns:
        tuple[int, str]: (priorité, url) pour sorted().
    """
    tag_lower = tag.lower()
    if tag_lower == "script":
        return 0, url
    if tag_lower == "link":
        return 1, url
    if tag_lower == "img":
        return 2, url
    return 3, url


def extract_subresource_urls(html: str, base_url: str, max_urls: int) -> list[str]:
    """Extrait les URLs de scripts, feuilles de style et images depuis du HTML.

    L'extraction suit les règles suivantes :

    - seules les balises ``<script src>``, ``<link rel="stylesheet" href>`` et
      ``<img src>`` sont prises en compte ;
    - les URLs sont normalisées en absolu par rapport à ``base_url`` ;
    - les URLs dupliquées sont supprimées ;
    - les URL sont priorisées dans l'ordre suivant :
        1. scripts JS (``<script>``) ;
        2. feuilles de style (``<link rel="stylesheet">``) ;
        3. images (``<img>``) ;
    - la liste finale est tronquée à ``max_urls`` éléments.

    Args:
        html: Contenu HTML de la page principale.
        base_url: URL absolue de la page principale utilisée pour normaliser les
            URLs relatives.
        max_urls: Nombre maximal d'URLs à retourner.

    Returns:
        list[str]: Liste d'URLs absolues de sous-ressources à analyser.
    """
    if not html or max_urls <= 0:
        return []

    parser = _SubresourceHTMLParser(base_url=base_url)
    with contextlib.suppress(Exception):
        parser.feed(html)

    raw_items = parser.raw_subresources
    if not raw_items:
        return []

    # Déduplique en conservant le premier tag observé pour une URL donnée.
    by_url: dict[str, str] = {}
    for item in raw_items:
        if item.url not in by_url:
            by_url[item.url] = item.tag

    ordered = sorted(by_url.items(), key=lambda item: _subresource_sort_key(item[0], item[1]))
    return [url for url, _tag in ordered[:max_urls]]
