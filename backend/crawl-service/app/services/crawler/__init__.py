"""Service crawler HTTP (roadmap §7).

Agent indépendant : découvre les URLs d'un site, produit une liste pour validation frontend.

Modes : html (HTTP + parsing), playwright (Chromium + JS), both (parallèle + fusion).
Architecture : core (BFS, fetch), executor (modes), results (fusion), stream_queue (SSE),
playwright_page, anti_bot, url_utils.
"""

from app.services.crawler.core import run_crawl

__all__ = ["run_crawl"]
