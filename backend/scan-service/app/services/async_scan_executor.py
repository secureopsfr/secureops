"""Exécution métier d'un job scan async (single URL et multi-URL)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from common.async_jobs import parse_sse_chunk

from app.services.custom.multi_scan_orchestrator import run_multi_scan as run_custom_multi_scan
from app.services.custom.multi_scan_orchestrator import validate_multi_scan_urls as validate_custom_multi_scan_urls
from app.services.custom.scan_stream import scan_stream_generator as custom_scan_stream_generator
from app.services.destructive.multi_scan_orchestrator import run_multi_scan as run_destructive_multi_scan
from app.services.destructive.multi_scan_orchestrator import validate_multi_scan_urls as validate_destructive_multi_scan_urls
from app.services.destructive.scan_stream import scan_stream_generator as destructive_scan_stream_generator
from app.services.intrusive.multi_scan_orchestrator import run_multi_scan as run_intrusive_multi_scan
from app.services.intrusive.multi_scan_orchestrator import validate_multi_scan_urls as validate_intrusive_multi_scan_urls
from app.services.intrusive.scan_stream import scan_stream_generator as intrusive_scan_stream_generator
from app.services.passive.multi_scan_orchestrator import run_multi_scan as run_passive_multi_scan
from app.services.passive.multi_scan_orchestrator import validate_multi_scan_urls as validate_passive_multi_scan_urls
from app.services.passive.scan_stream import scan_stream_generator as passive_scan_stream_generator
from app.utils.url_validator import URLValidationError

logger = logging.getLogger(__name__)


async def _handle_step_event(
    data: dict[str, Any],
    on_progress: Callable[..., Awaitable[None]] | None,
    flush_fn: Callable[[], Awaitable[None]] | None,
) -> None:
    step = str(data.get("step", "step"))
    message = str(data.get("message", ""))
    extra = {k: v for k, v in data.items() if k not in ("step", "message")}
    if on_progress:
        await on_progress(step, message, **extra)
    # Flush immédiat après _check : le step va s'exécuter, le frontend
    # doit voir l'état loading en DB avant que _done n'arrive.
    if step.endswith("_check") and flush_fn:
        await flush_fn()


async def execute_scan_job(
    *,
    url: str,
    scan_type: str,
    scan_mode: str = "passive",
    input_json: dict[str, Any] | None = None,
    on_progress: Callable[..., Awaitable[None]] | None = None,
    flush_fn: Callable[[], Awaitable[None]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Exécute un job de scan single-URL et retourne (result, error).

    Args:
        flush_fn: Optionnel — appelé après chaque événement _check pour forcer
                  l'écriture en DB avant l'exécution du step. Permet au frontend
                  de voir l'état loading pendant que le step tourne.
    """
    stream_factory = {
        "intrusive": intrusive_scan_stream_generator,
        "destructive": destructive_scan_stream_generator,
        "custom": custom_scan_stream_generator,
    }.get(scan_mode, passive_scan_stream_generator)
    result_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None
    stream = (
        passive_scan_stream_generator(url, authorization=None, scan_type=scan_type)
        if stream_factory is passive_scan_stream_generator
        else stream_factory(url, authorization=None)
    )
    async for chunk in stream:
        parsed = parse_sse_chunk(chunk)
        if not parsed:
            continue
        event, data = parsed
        if event == "step" and isinstance(data, dict):
            await _handle_step_event(data, on_progress, flush_fn)
        elif event == "result" and isinstance(data, dict):
            result_payload = data
        elif event == "error" and isinstance(data, dict):
            error_payload = data

    if result_payload is not None:
        result_payload["scan_type"] = scan_type
        result_payload["scan_mode"] = scan_mode

    return result_payload, error_payload


async def execute_multi_scan_job(
    *,
    urls: list[str],
    scan_type: str,
    scan_mode: str = "passive",
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
    if scan_mode == "destructive":
        run_multi_scan = run_destructive_multi_scan
        validate_multi_scan_urls = validate_destructive_multi_scan_urls
    elif scan_mode == "custom":
        run_multi_scan = run_custom_multi_scan
        validate_multi_scan_urls = validate_custom_multi_scan_urls
    elif scan_mode == "intrusive":
        run_multi_scan = run_intrusive_multi_scan
        validate_multi_scan_urls = validate_intrusive_multi_scan_urls
    else:
        run_multi_scan = run_passive_multi_scan
        validate_multi_scan_urls = validate_passive_multi_scan_urls

    # Serialize all progress callbacks with a lock: asyncio.gather runs page scans
    # concurrently, and each page calls on_progress → session.commit(). Without a
    # lock, concurrent commits on the same SQLAlchemy session raise InvalidRequestError.
    _progress_lock = asyncio.Lock()

    async def _progress(step: str, message: str, **kwargs: Any) -> None:
        if on_progress:
            async with _progress_lock:
                await on_progress(step, message, **kwargs)

    try:
        validated_urls = await validate_multi_scan_urls(urls)
        result = await run_multi_scan(validated_urls, on_progress=_progress, scan_type=scan_type)
        payload = result.to_dict()
        payload["scan_type"] = scan_type
        payload["scan_mode"] = scan_mode
        return payload, None
    except URLValidationError as exc:
        return None, {"message": str(exc), "status_code": 400, "error_type": "validation_error"}
    except ValueError as exc:
        return None, {"message": str(exc), "status_code": 400, "error_type": "validation_error"}
    except Exception as exc:
        logger.exception("execute_multi_scan_job: erreur inattendue urls=%s", urls[:3])
        return None, {"message": str(exc), "status_code": 500, "error_type": "unexpected_error"}
