"""Exécution métier d'un job scan async (single URL et multi-URL)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from common.async_jobs import parse_sse_chunk, utc_now

from app.services.scan_stream import scan_stream_generator

logger = logging.getLogger(__name__)


async def execute_scan_job(
    *,
    url: str,
    scan_type: str,
    input_json: dict[str, Any] | None = None,
    on_progress: Callable[..., Awaitable[None]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Exécute un job de scan single-URL et retourne (result, error)."""
    if scan_type in {"backend", "custom"}:
        fake_result = {
            "url": url,
            "timestamp": utc_now().isoformat(),
            "duration": 0.1,
            "score": 100,
            "findings": [],
            "status": "success",
            "scan_type": scan_type,
            "message": f"Fake {scan_type} scan result (V1).",
        }
        if on_progress:
            await on_progress("fake_scan_done", f"Fake {scan_type} scan généré.")
        return fake_result, None

    result_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None
    async for chunk in scan_stream_generator(url, authorization=None):
        parsed = parse_sse_chunk(chunk)
        if not parsed:
            continue
        event, data = parsed
        if event == "step" and isinstance(data, dict):
            step = str(data.get("step", "step"))
            message = str(data.get("message", ""))
            anomaly_count_raw = data.get("anomaly_count")
            anomaly_count = int(anomaly_count_raw) if isinstance(anomaly_count_raw, int) else None
            if on_progress:
                if anomaly_count is None:
                    await on_progress(step, message)
                else:
                    await on_progress(step, message, anomaly_count=anomaly_count)
        elif event == "result" and isinstance(data, dict):
            result_payload = data
        elif event == "error" and isinstance(data, dict):
            error_payload = data

    return result_payload, error_payload


async def execute_multi_scan_job(
    *,
    urls: list[str],
    scan_type: str,
    on_progress: Callable[..., Awaitable[None]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Exécute un job de scan multi-URL et retourne (result, error).

    Args:
        urls: Liste d'URLs à scanner (même domaine, validées à la création du job).
        scan_type: Type de scan (uniquement "frontend" supporté en V1).
        on_progress: Callback (step, message) pour la progression.

    Returns:
        tuple[dict | None, dict | None]: (result_payload, error_payload).
    """
    from app.services.multi_scan_orchestrator import run_multi_scan, validate_multi_scan_urls
    from app.utils.url_validator import URLValidationError

    # Serialize all progress callbacks with a lock: asyncio.gather runs page scans
    # concurrently, and each page calls on_progress → session.commit(). Without a
    # lock, concurrent commits on the same SQLAlchemy session raise InvalidRequestError.
    _progress_lock = asyncio.Lock()

    async def _progress(step: str, message: str, **_kwargs: Any) -> None:
        if on_progress:
            async with _progress_lock:
                await on_progress(step, message)

    try:
        validated_urls = await validate_multi_scan_urls(urls)
        result = await run_multi_scan(validated_urls, on_progress=_progress)
        return result.to_dict(), None
    except URLValidationError as exc:
        return None, {"message": str(exc), "status_code": 400, "error_type": "validation_error"}
    except ValueError as exc:
        return None, {"message": str(exc), "status_code": 400, "error_type": "validation_error"}
    except Exception as exc:
        logger.exception("execute_multi_scan_job: erreur inattendue urls=%s", urls[:3])
        return None, {"message": str(exc), "status_code": 500, "error_type": "unexpected_error"}
