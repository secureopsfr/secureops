"""Exécution des crawls par mode (html, playwright, both)."""

import asyncio
import functools
from collections.abc import Callable

from app.services.crawler import core as crawl_core
from app.services.crawler.playwright_crawl import run_crawl_playwright_from_prepared
from app.services.crawler.results import entries_to_payload, merge_entries
from app.services.crawler.types import CrawlMode


def _empty_crawl_result() -> tuple[list[crawl_core.CrawlUrlEntry], bool, bool, bool, bool, bool, int, list[str]]:
    """Résultat vide pour un crawler non exécuté."""
    return [], False, False, False, False, False, 0, []


def _make_progress_callback(prefix: str, on_progress: Callable[[str, str], None]) -> Callable[[str, str], None]:
    """Fabrique un callback de progression préfixé."""
    return lambda step, msg: on_progress(f"{prefix}_{step}", msg)


def _reached_url_limit(entries: list[crawl_core.CrawlUrlEntry], max_urls: int) -> bool:
    """Indique si un crawler a atteint la limite d'URLs demandée."""
    return len(entries) >= max_urls


async def _run_html_from_prepared(
    prepared,
    *,
    on_progress: Callable[[str, str], None],
    stop_event: asyncio.Event | None,
) -> tuple[list[crawl_core.CrawlUrlEntry], bool, bool, bool, bool, bool, int, list[str]]:
    """Normalise le résultat du crawler HTML sur le format 5-tuple."""
    (
        entries,
        timeout_reached,
        requests_blocked,
        max_consecutive_403,
        anti_bot_signature_detected,
        disallow_paths,
    ) = await crawl_core.run_crawl_from_prepared(
        prepared,
        on_progress=on_progress,
        stop_event=stop_event,
    )
    anti_bot_low_url_suspected = len(entries) <= 3 and not anti_bot_signature_detected
    anti_bot_suspected = anti_bot_signature_detected or anti_bot_low_url_suspected
    return (
        entries,
        timeout_reached,
        anti_bot_suspected,
        anti_bot_signature_detected,
        anti_bot_low_url_suspected,
        requests_blocked,
        max_consecutive_403,
        disallow_paths,
    )


async def _run_crawler_impl(
    url: str,
    max_urls: int,
    on_progress: Callable[[str, str], None],
    use_playwright: bool,
    stop_ev: asyncio.Event | None = None,
    progress_cb: Callable[[str, str], None] | None = None,
) -> tuple[list[crawl_core.CrawlUrlEntry], bool, bool, bool, bool, bool, int, list[str]]:
    """Implémentation du crawl (HTML ou Playwright)."""
    cb = progress_cb or on_progress
    if use_playwright:
        from app.services.crawler.playwright_crawl import run_crawl_playwright

        return await run_crawl_playwright(url, max_urls=max_urls, on_progress=cb, stop_event=stop_ev)
    (
        entries,
        timeout_reached,
        requests_blocked,
        max_consecutive_403,
        anti_bot_signature_detected,
        disallow_paths,
    ) = await crawl_core.run_crawl(
        url,
        max_urls=max_urls,
        on_progress=cb,
        stop_event=stop_ev,
    )
    anti_bot_low_url_suspected = len(entries) <= 3 and not anti_bot_signature_detected
    anti_bot_suspected = anti_bot_signature_detected or anti_bot_low_url_suspected
    return (
        entries,
        timeout_reached,
        anti_bot_suspected,
        anti_bot_signature_detected,
        anti_bot_low_url_suspected,
        requests_blocked,
        max_consecutive_403,
        disallow_paths,
    )


def make_run_crawler(
    url: str,
    max_urls: int,
    on_progress: Callable[[str, str], None],
    use_playwright: bool,
):
    """Fabrique une fonction de crawl (html ou playwright) retournant un tuple normalisé.

    Args:
        url: URL de départ.
        max_urls: Nombre maximal d'URLs.
        on_progress: Callback (step, message).
        use_playwright: True pour mode Playwright, False pour HTML.

    Returns:
        Fonction async (stop_ev, progress_cb) -> (
            entries,
            timeout,
            anti_bot,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            requests_blocked,
            max_consecutive_403,
            disallow,
        ).
    """
    return functools.partial(_run_crawler_impl, url, max_urls, on_progress, use_playwright)


async def execute_crawl_by_mode(
    mode: CrawlMode,
    url: str,
    max_urls: int,
    on_progress: Callable[[str, str], None],
    run_html_fn: Callable,
    run_playwright_fn: Callable,
) -> tuple[
    list[dict],
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    int,
    list[str],
]:
    """Exécute le crawl selon le mode.

    Args:
        mode: 'html', 'playwright' ou 'both'.
        url: URL de départ.
        max_urls: Nombre maximal d'URLs.
        on_progress: Callback (step, message).
        run_html_fn: Fonction de crawl HTML.
        run_playwright_fn: Fonction de crawl Playwright.

    Returns:
        (
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
        ).
    """
    if mode == "html":
        (
            entries,
            timeout_reached,
            anti_bot,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            requests_blocked,
            max_consecutive_403,
            disallow_paths,
        ) = await run_html_fn()
        return (
            entries_to_payload(entries),
            timeout_reached,
            anti_bot,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            timeout_reached,
            False,
            requests_blocked,
            requests_blocked,
            False,
            max_consecutive_403,
            disallow_paths,
        )
    if mode == "playwright":
        (
            entries,
            timeout_reached,
            anti_bot,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            requests_blocked,
            max_consecutive_403,
            disallow_paths,
        ) = await run_playwright_fn()
        return (
            entries_to_payload(entries),
            timeout_reached,
            anti_bot,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            False,
            timeout_reached,
            requests_blocked,
            False,
            requests_blocked,
            max_consecutive_403,
            disallow_paths,
        )
    return await run_mode_both(url, max_urls, on_progress, run_html_fn, run_playwright_fn)


async def run_mode_both(
    url: str,
    max_urls: int,
    on_progress: Callable[[str, str], None],
    run_html_fn: Callable,
    run_playwright_fn: Callable,
) -> tuple[
    list[dict],
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    bool,
    int,
    list[str],
]:
    """Exécute les deux crawlers en parallèle, fusionne et retourne le résultat.

    Args:
        url: URL de départ.
        max_urls: Nombre maximal d'URLs.
        on_progress: Callback (step, message).
        run_html_fn: Fonction de crawl HTML.
        run_playwright_fn: Fonction de crawl Playwright.

    Returns:
        (
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
        ).
    """
    if not hasattr(crawl_core, "prepare_crawl_inputs") or not hasattr(crawl_core, "run_crawl_from_prepared"):
        # Compat mode for mixed runtime versions (fallback to legacy behavior).
        stop_ev = asyncio.Event()
        task_html = asyncio.create_task(run_html_fn(stop_ev, _make_progress_callback("html", on_progress)))
        task_playwright = asyncio.create_task(run_playwright_fn(stop_ev, _make_progress_callback("playwright", on_progress)))
        done, pending = await asyncio.wait([task_html, task_playwright], return_when=asyncio.FIRST_COMPLETED)

        if task_html in done:
            first_label = "html"
            (
                entries_html,
                to_html,
                anti_html,
                anti_sig_html,
                anti_low_html,
                req_html,
                max_403_html,
                disallow_html,
            ) = task_html.result()
            (
                entries_pw,
                to_pw,
                anti_pw,
                anti_sig_pw,
                anti_low_pw,
                req_pw,
                max_403_pw,
                disallow_pw,
            ) = _empty_crawl_result()
        else:
            first_label = "playwright"
            (
                entries_pw,
                to_pw,
                anti_pw,
                anti_sig_pw,
                anti_low_pw,
                req_pw,
                max_403_pw,
                disallow_pw,
            ) = task_playwright.result()
            (
                entries_html,
                to_html,
                anti_html,
                anti_sig_html,
                anti_low_html,
                req_html,
                max_403_html,
                disallow_html,
            ) = _empty_crawl_result()

        on_progress(f"crawl_{first_label}_done", f"Crawl {first_label} terminé. Arrêt de l'autre…")
        stop_ev.set()
        on_progress("crawl_stopping_other", "Arrêt du crawler restant…")
        await asyncio.gather(*pending)

        for pending_task in pending:
            if pending_task is task_html:
                (
                    entries_html,
                    to_html,
                    anti_html,
                    anti_sig_html,
                    anti_low_html,
                    req_html,
                    max_403_html,
                    disallow_html,
                ) = pending_task.result()
            else:
                (
                    entries_pw,
                    to_pw,
                    anti_pw,
                    anti_sig_pw,
                    anti_low_pw,
                    req_pw,
                    max_403_pw,
                    disallow_pw,
                ) = pending_task.result()

        on_progress("crawl_merging", "Fusion des résultats…")
        payload = merge_entries(entries_html, entries_pw, max_urls)
        timeout_reached = to_html or to_pw
        anti_bot_signature_detected = anti_sig_html and anti_sig_pw
        anti_bot_low_url_suspected = anti_low_html and anti_low_pw
        anti_bot_suspected = anti_bot_signature_detected or anti_bot_low_url_suspected
        requests_blocked = req_html or req_pw
        max_consecutive_403 = max(max_403_html, max_403_pw)
        disallow_paths = disallow_html if disallow_html else disallow_pw
        return (
            payload,
            timeout_reached,
            anti_bot_suspected,
            anti_bot_signature_detected,
            anti_bot_low_url_suspected,
            to_html,
            to_pw,
            requests_blocked,
            req_html,
            req_pw,
            max_consecutive_403,
            disallow_paths,
        )

    prepared = await crawl_core.prepare_crawl_inputs(url, max_urls=max_urls, on_progress=on_progress)
    stop_ev = asyncio.Event()
    task_html = asyncio.create_task(
        _run_html_from_prepared(
            prepared,
            on_progress=_make_progress_callback("html", on_progress),
            stop_event=stop_ev,
        )
    )
    task_playwright = asyncio.create_task(
        run_crawl_playwright_from_prepared(
            prepared,
            on_progress=_make_progress_callback("playwright", on_progress),
            stop_event=stop_ev,
        )
    )
    done, pending = await asyncio.wait([task_html, task_playwright], return_when=asyncio.FIRST_COMPLETED)

    if task_html in done:
        first_label = "html"
        (
            entries_html,
            to_html,
            anti_html,
            anti_sig_html,
            anti_low_html,
            req_html,
            max_403_html,
            disallow_html,
        ) = task_html.result()
        (
            entries_pw,
            to_pw,
            anti_pw,
            anti_sig_pw,
            anti_low_pw,
            req_pw,
            max_403_pw,
            disallow_pw,
        ) = _empty_crawl_result()
        first_entries = entries_html
    else:
        first_label = "playwright"
        (
            entries_pw,
            to_pw,
            anti_pw,
            anti_sig_pw,
            anti_low_pw,
            req_pw,
            max_403_pw,
            disallow_pw,
        ) = task_playwright.result()
        (
            entries_html,
            to_html,
            anti_html,
            anti_sig_html,
            anti_low_html,
            req_html,
            max_403_html,
            disallow_html,
        ) = _empty_crawl_result()
        first_entries = entries_pw

    stop_other = _reached_url_limit(first_entries, max_urls)
    if stop_other:
        on_progress(f"crawl_{first_label}_done", f"Crawl {first_label} terminé (limite atteinte). Arrêt de l'autre…")
        stop_ev.set()
        on_progress("crawl_stopping_other", "Arrêt du crawler restant…")
    else:
        on_progress(f"crawl_{first_label}_done", f"Crawl {first_label} terminé. L'autre continue…")
    await asyncio.gather(*pending)

    for pending_task in pending:
        if pending_task is task_html:
            (
                entries_html,
                to_html,
                anti_html,
                anti_sig_html,
                anti_low_html,
                req_html,
                max_403_html,
                disallow_html,
            ) = pending_task.result()
        else:
            (
                entries_pw,
                to_pw,
                anti_pw,
                anti_sig_pw,
                anti_low_pw,
                req_pw,
                max_403_pw,
                disallow_pw,
            ) = pending_task.result()

    on_progress("crawl_merging", "Fusion des résultats…")
    payload = merge_entries(entries_html, entries_pw, max_urls)
    timeout_reached = to_html or to_pw
    anti_bot_signature_detected = anti_sig_html and anti_sig_pw
    anti_bot_low_url_suspected = anti_low_html and anti_low_pw
    anti_bot_suspected = anti_bot_signature_detected or anti_bot_low_url_suspected
    requests_blocked = req_html or req_pw
    max_consecutive_403 = max(max_403_html, max_403_pw)
    disallow_paths = disallow_html if disallow_html else disallow_pw
    return (
        payload,
        timeout_reached,
        anti_bot_suspected,
        anti_bot_signature_detected,
        anti_bot_low_url_suspected,
        to_html,
        to_pw,
        requests_blocked,
        req_html,
        req_pw,
        max_consecutive_403,
        disallow_paths,
    )
