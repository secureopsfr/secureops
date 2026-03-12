"""Gestion de la queue SSE du pipeline de crawl : items, erreurs, consommation.

Centralise le format des messages (result, error_*) et la conversion des exceptions.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator, Callable

from app.utils.url_validator import URLValidationError

logger = logging.getLogger(__name__)


def exception_to_error_info(exc: BaseException, url: str) -> tuple[str, str, int]:
    """Convertit une exception en (queue_tag, message, status_code).

    Args:
        exc: Exception levée.
        url: URL concernée (pour le log).

    Returns:
        (tag, message, status_code) pour la queue SSE.
    """
    if isinstance(exc, URLValidationError):
        return "error_validation", str(exc), 400
    if isinstance(exc, ImportError):
        if "playwright" in str(exc).lower():
            return "error_503", "Mode SPA non disponible : Playwright n'est pas installé.", 503
        return "error_500", str(exc), 500
    logger.exception("Erreur crawl pour %s : %s", url, exc)
    return "error_500", "Erreur lors du crawl.", 500


def handle_queue_item(item: tuple, sse_message_fn: Callable) -> tuple[list[str], bool]:
    """Traite un item de la queue. Retourne (messages_sse, is_terminal).

    Args:
        item: Tuple (tag, ...) ou
            (
                tag,
                payload,
                timeout,
                anti_bot,
                anti_bot_signature_detected,
                anti_bot_low_url_suspected,
                timeout_html,
                timeout_playwright,
                blocked,
                requests_blocked_html,
                requests_blocked_playwright,
                max_consecutive_403,
                disallow,
            ).
        sse_message_fn: Fonction pour formater un message SSE.

    Returns:
        (liste de messages à émettre, True si terminaison).
    """
    tag = item[0]
    if tag == "result":
        (
            _,
            payload,
            timeout_reached,
            anti_bot_suspected,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            timeout_html,
            timeout_playwright,
            requests_blocked,
            requests_blocked_html,
            requests_blocked_playwright,
            max_consecutive_403,
            disallow_paths,
        ) = item
        nb = len(payload)
        urls_label = "1 URL" if nb == 1 else f"{nb} URLs"
        messages = [
            sse_message_fn("step", {"step": "crawl_done", "message": f"Exploration terminée ({urls_label})."}),
            sse_message_fn(
                "result",
                {
                    "urls": payload,
                    "timeout_reached": timeout_reached,
                    "anti_bot_suspected": anti_bot_suspected,
                    "anti_bot_signature_detected": anti_bot_signature_detected,
                    "anti_bot_low_url_suspected": anti_bot_low_url_suspected,
                    "timeout_html": timeout_html,
                    "timeout_playwright": timeout_playwright,
                    "requests_blocked": requests_blocked,
                    "requests_blocked_html": requests_blocked_html,
                    "requests_blocked_playwright": requests_blocked_playwright,
                    "max_consecutive_403": max_consecutive_403,
                    "disallow_paths": disallow_paths,
                },
            ),
        ]
        return messages, True
    if tag == "error_validation":
        return [sse_message_fn("error", {"message": item[1], "status_code": 400})], True
    if tag == "error_503":
        return [sse_message_fn("error", {"message": item[1], "status_code": 503})], True
    if tag == "error_500":
        return [sse_message_fn("error", {"message": item[1], "status_code": 500})], True
    return [sse_message_fn("step", {"step": item[0], "message": item[1]})], False


def put_error_from_exception(exc: BaseException, url: str, queue: asyncio.Queue) -> tuple[str, int]:
    """Envoie l'erreur dans la queue et retourne (message, status_code)."""
    tag, message, status_code = exception_to_error_info(exc, url)
    queue.put_nowait((tag, message, False))
    return message, status_code


def error_response_for_exception(exc: BaseException, url: str) -> tuple[str, int]:
    """Convertit une exception en (message, status_code) pour la réponse SSE."""
    _, message, status_code = exception_to_error_info(exc, url)
    return message, status_code


async def consume_crawl_queue(
    queue: asyncio.Queue,
    stream_timeout: float,
    crawl_task: asyncio.Task,
    sse_message_fn: Callable,
) -> AsyncGenerator[str, None]:
    """Consomme la queue du crawl et yield les événements SSE jusqu'à terminaison.

    Args:
        queue: Queue des items (steps, result, errors).
        stream_timeout: Timeout en secondes avant annulation du crawl.
        crawl_task: Task du crawl à annuler en cas de timeout.
        sse_message_fn: Fonction pour formater un message SSE.

    Yields:
        Messages SSE formatés.
    """
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=stream_timeout)
        except asyncio.TimeoutError:
            crawl_task.cancel()
            yield sse_message_fn("error", {"message": "Timeout du crawl.", "status_code": 504})
            return
        messages, is_terminal = handle_queue_item(item, sse_message_fn)
        for msg in messages:
            yield msg
        if is_terminal:
            return
