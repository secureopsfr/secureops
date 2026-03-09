"""Route de crawl HTTP (roadmap §7).

Endpoint streaming POST /api/crawl/stream : crawl SSE avec étapes (validation, SSRF, robots, crawl).
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.crawler.crawl_stream import crawl_stream_generator
from app.services.crawler.types import CrawlMode

router = APIRouter(prefix="/api", tags=["crawl"])


class CrawlRequest(BaseModel):
    """Requête de crawl."""

    url: str = Field(..., description="URL de départ")
    max_urls: int = Field(default=50, ge=5, le=200, description="Limite d'URLs (5–200)")
    mode: CrawlMode = Field(
        default="html",
        description="Mode de crawl : html (HTTP), playwright (SPA), both (fusion des deux)",
    )


@router.post(
    "/crawl/stream",
    summary="Lancer un crawl (streaming)",
    description="Crawl en streaming SSE : étapes (validation, SSRF, robots, crawl) puis result ou error.",
)
async def post_crawl_stream(body: CrawlRequest) -> StreamingResponse:
    """Crawl en streaming : émet des événements step à chaque étape, puis result ou error."""
    return StreamingResponse(
        crawl_stream_generator(body.url, max_urls=body.max_urls, mode=body.mode),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
