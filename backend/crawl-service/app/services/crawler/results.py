"""Fusion et conversion des résultats de crawl (HTML / Playwright)."""

from app.services.crawler.core import CrawlUrlEntry


def merge_entries(
    entries_html: list[CrawlUrlEntry],
    entries_playwright: list[CrawlUrlEntry],
    max_urls: int,
) -> list[dict]:
    """Fusionne les entrées des deux crawlers : déduplication par URL, préférence pour type 'page'.

    Args:
        entries_html: Entrées du crawler HTML.
        entries_playwright: Entrées du crawler Playwright.
        max_urls: Nombre maximal d'URLs dans le résultat fusionné.

    Returns:
        Liste de dict (url, type, depth) triée et limitée.
    """
    seen: dict[str, CrawlUrlEntry] = {}
    for e in entries_html + entries_playwright:
        if e.url in seen:
            if e.type == "page":
                seen[e.url] = e
        else:
            seen[e.url] = e
    merged = sorted(seen.values(), key=lambda x: (x.depth, x.url))
    return [e.to_dict() for e in merged[:max_urls]]


def entries_to_payload(entries: list[CrawlUrlEntry]) -> list[dict]:
    """Convertit une liste d'entrées en payload pour la réponse SSE.

    Args:
        entries: Liste de CrawlUrlEntry.

    Returns:
        Liste de dict (url, type, depth).
    """
    return [e.to_dict() for e in entries]
