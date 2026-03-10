"""Pipeline de scan factice : retourne toujours un résultat OK.

Utilisé pour développer la solution API publique (clés API, quotas, rate limiting)
sans dépendre du scan réel (posture sécurité).
"""

import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from app.catalogue.category_summaries import build_category_summaries
from app.errors.fetch_errors import build_validation_error_payload
from app.utils.sse import sse_message
from app.utils.url_validator import URLValidationError, validate_and_normalize_url

logger = logging.getLogger(__name__)


async def fake_scan_stream_generator(
    url: str,
    authorization: str | None = None,
) -> AsyncGenerator[str, None]:
    """Générateur SSE factice : valide l'URL, émet des étapes simulées, retourne toujours OK.

    Args:
        url: URL à « scanner » (validée comme le scan réel).
        authorization: Header Authorization optionnel pour sauvegarder dans l'historique.

    Yields:
        str: Blocs SSE (event + data).
    """
    start = time.monotonic()
    try:
        # Validation URL (même logique que le scan réel)
        yield sse_message("step", {"step": "validation_url_check", "message": "Validation de l'URL…"})
        normalized_url = validate_and_normalize_url(url)
        yield sse_message("step", {"step": "validation_url_done", "message": "URL validée et normalisée."})

        yield sse_message("step", {"step": "ssrf_check", "message": "Vérification SSRF (simulé)…"})
        yield sse_message("step", {"step": "ssrf_done", "message": "Vérification SSRF OK."})

        yield sse_message("step", {"step": "fetch_https_check", "message": "Récupération de la page (simulé)…"})
        yield sse_message("step", {"step": "fetch_https_done", "message": "Page récupérée (simulé)."})

        yield sse_message("step", {"step": "tls_check", "message": "Vérification TLS (simulé)…"})
        yield sse_message("step", {"step": "tls_done", "message": "TLS/HTTPS vérifié (simulé)."})

        # Résultat toujours OK : score 100, aucun finding
        duration = time.monotonic() - start
        timestamp = datetime.now(timezone.utc).isoformat()
        category_summaries = build_category_summaries(
            [],
            tls_posture="ok",
            tls_version="TLS 1.3",
        )
        payload = {
            "url": normalized_url,
            "timestamp": timestamp,
            "duration": duration,
            "score": 100,
            "findings": [],
            "scan_type": "custom",
            "category_summaries": category_summaries,
            "total_tests_count": sum(s.get("checks_count", 0) for s in category_summaries),
        }
        logger.info("Scan fake terminé : url=%s, score=100", normalized_url[:50])
        yield sse_message("result", payload)

        # Sauvegarde dans l'historique si auth présente (même logique que scan_stream)
        if authorization:
            try:
                from app.services.scan_history_save import save_scan_to_history

                scan_id = await save_scan_to_history(payload, authorization)
                if scan_id:
                    yield sse_message("save_done", {"scan_id": scan_id})
            except Exception as e:
                logger.warning("Sauvegarde historique (fake) échouée: %s", e)
                yield sse_message("save_failed", {"message": str(e)})

    except URLValidationError as e:
        logger.info("Scan fake : validation URL échouée: %s", e)
        yield sse_message("error", build_validation_error_payload(str(e)))
    except Exception as e:
        logger.exception("Scan fake : erreur inattendue: %s", e)
        from app.errors.fetch_errors import build_unexpected_error_payload

        yield sse_message("error", build_unexpected_error_payload(str(e)))
