"""Types partagés par les crawlers."""

from typing import Literal, TypedDict

CrawlMode = Literal["html", "playwright", "both"]


class CrawlResultPayload(TypedDict):
    """Payload du résultat d'un crawl (pour SSE)."""

    urls: list[dict]
    timeout_reached: bool
    anti_bot_suspected: bool
    anti_bot_signature_detected: bool
    anti_bot_low_url_suspected: bool
    timeout_html: bool
    timeout_playwright: bool
    requests_blocked: bool
    requests_blocked_html: bool
    requests_blocked_playwright: bool
    max_consecutive_403: int
    disallow_paths: list[str]
