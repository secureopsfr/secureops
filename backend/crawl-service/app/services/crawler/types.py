"""Types partagés par les crawlers."""

from typing import Literal, TypedDict

CrawlMode = Literal["html", "playwright", "both"]


class CrawlResultPayload(TypedDict):
    """Payload du résultat d'un crawl (pour SSE)."""

    urls: list[dict]
    timeout_reached: bool
    anti_bot_suspected: bool
    requests_blocked: bool
    disallow_paths: list[str]
