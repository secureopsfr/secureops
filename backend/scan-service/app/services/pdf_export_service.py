"""Service d'orchestration pour l'export PDF d'un scan historique."""

from __future__ import annotations

import logging
from urllib.parse import urljoin

import httpx

from app.schemas.scan import ScanForPdfSchema

logger = logging.getLogger(__name__)


class PdfExportError(Exception):
    """Erreur contrôlée pendant le flux d'export PDF."""

    def __init__(self, status_code: int, message: str) -> None:
        """Initialise l'exception avec un code HTTP et un message."""
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def normalize_lang(lang: str) -> str:
    """Normalise la langue pour les libellés d'export."""
    return "en" if lang == "en" else "fr"


def _build_pages_evidence(page_urls: list[str], lang: str) -> str:
    shown_urls = page_urls[:20]
    extra = len(page_urls) - len(shown_urls)
    pages_list = ", ".join(shown_urls)
    if extra > 0:
        pages_list = f"{pages_list}, +{extra}"
    if lang == "en":
        return f"Detected on {len(page_urls)} page(s): {pages_list}"
    return f"Repéré sur {len(page_urls)} page(s): {pages_list}"


def _finding_group_key(finding: dict) -> tuple[str, str, str, str, str]:
    return (
        str(finding.get("id", "") or ""),
        str(finding.get("category", "") or ""),
        str(finding.get("severity", "") or ""),
        str(finding.get("title", "") or ""),
        str(finding.get("recommendation", "") or ""),
    )


def _merge_references(existing: dict, incoming: dict) -> None:
    refs = existing.get("references")
    if not isinstance(refs, list):
        refs = []
    new_refs = incoming.get("references")
    if isinstance(new_refs, list):
        refs = list(dict.fromkeys([*refs, *new_refs]))
    existing["references"] = refs


def _aggregate_multi_page_findings(page_results: list[dict], lang: str) -> list[dict]:
    grouped: dict[tuple[str, str, str, str, str], dict] = {}
    page_urls_by_group: dict[tuple[str, str, str, str, str], set[str]] = {}

    for page in page_results:
        if not isinstance(page, dict):
            continue
        page_url = str(page.get("url", "")).strip()
        page_findings = page.get("findings") if isinstance(page.get("findings"), list) else []
        for finding in page_findings:
            if not isinstance(finding, dict):
                continue
            key = _finding_group_key(finding)
            if key not in grouped:
                grouped[key] = dict(finding)
                page_urls_by_group[key] = set()
            if page_url:
                page_urls_by_group[key].add(page_url)
            _merge_references(grouped[key], finding)

    merged_findings: list[dict] = []
    for key, finding in grouped.items():
        page_urls = sorted(page_urls_by_group.get(key, set()))
        if page_urls:
            original_evidence = str(finding.get("evidence", "") or "").strip()
            page_evidence = _build_pages_evidence(page_urls, lang)
            finding["evidence"] = f"{page_evidence}\n{original_evidence}" if original_evidence else page_evidence
        merged_findings.append(finding)
    return merged_findings


def _build_pdf_payload_from_history_scan(
    data: dict,
    lang: str,
) -> dict:
    result_mode = data.get("result_mode", "single")
    if result_mode != "multi":
        return {
            "url": data.get("url"),
            "score": data.get("score"),
            "timestamp": data.get("timestamp", ""),
            "duration": data.get("duration", 0.0),
            "findings": data.get("findings", []),
        }

    page_results = data.get("page_results")
    urls = data.get("urls")
    if not isinstance(page_results, list) or not isinstance(urls, list) or len(page_results) == 0 or len(urls) == 0:
        raise PdfExportError(
            status_code=409,
            message=("Export PDF indisponible: données multi-pages incomplètes " "dans l'historique."),
        )

    findings = _aggregate_multi_page_findings(page_results, normalize_lang(lang))
    return {
        "url": data.get("url"),
        "score": data.get("score"),
        "timestamp": data.get("timestamp", ""),
        "duration": data.get("duration", 0.0),
        "findings": findings,
        "result_mode": "multi",
        "page_results": page_results,
    }


def _build_pdf_filename(url: str, timestamp: str) -> str:
    host = url.replace("https://", "").replace("http://", "").split("/")[0][:30]
    return f"scan-{host}-{timestamp[:10]}.pdf".replace(":", "-")


async def export_scan_pdf_bytes(
    *,
    authorization: str | None,
    scan_id: str,
    include_matrices: bool,
    lang: str,
    gateway_url: str,
    pdf_service_url: str,
    fetch_scan_timeout: float,
    pdf_request_timeout: float,
    pdf_service_internal_api_key: str | None,
) -> tuple[bytes, str]:
    """Orchestre l'export PDF: fetch historique -> build payload -> call pdf-service."""
    if not authorization:
        raise PdfExportError(status_code=401, message="Authentification requise")

    history_url = urljoin(
        f"{gateway_url.rstrip('/')}/",
        f"user/api/scans/history/{scan_id}",
    )
    headers = {"Authorization": authorization}

    async with httpx.AsyncClient(timeout=fetch_scan_timeout) as client:
        resp = await client.get(history_url, headers=headers)
    if resp.status_code == 404:
        raise PdfExportError(status_code=404, message="Scan non trouvé")
    if resp.status_code == 401:
        raise PdfExportError(status_code=401, message="Authentification requise")
    if resp.status_code >= 400:
        logger.warning(
            "Erreur récupération scan pour PDF: %s %s",
            resp.status_code,
            resp.text[:200],
        )
        raise PdfExportError(
            status_code=502,
            message="Impossible de récupérer le scan",
        )

    payload_data = _build_pdf_payload_from_history_scan(resp.json(), lang=lang)
    try:
        scan_data = ScanForPdfSchema.model_validate(payload_data)
    except Exception as exc:  # pragma: no cover - defensive boundary
        logger.warning("Schéma scan invalide pour PDF: %s", exc)
        raise PdfExportError(status_code=502, message="Données du scan invalides")

    pdf_endpoint = urljoin(f"{pdf_service_url.rstrip('/')}/", "api/report/pdf")
    pdf_headers: dict[str, str] = {}
    if pdf_service_internal_api_key:
        pdf_headers["X-Internal-Api-Key"] = pdf_service_internal_api_key
    params = {
        "lang": normalize_lang(lang),
        "include_matrices": include_matrices,
    }
    payload = {
        "url": scan_data.url,
        "score": scan_data.score,
        "timestamp": scan_data.timestamp,
        "duration": scan_data.duration,
        "findings": scan_data.findings,
        "result_mode": payload_data.get("result_mode"),
        "page_results": payload_data.get("page_results"),
    }

    async with httpx.AsyncClient(timeout=pdf_request_timeout) as client:
        pdf_resp = await client.post(
            pdf_endpoint,
            json=payload,
            params=params,
            headers=pdf_headers,
        )
    if pdf_resp.status_code >= 400:
        logger.warning(
            "Erreur pdf-service pour export PDF: %s %s",
            pdf_resp.status_code,
            pdf_resp.text[:200],
        )
        raise PdfExportError(
            status_code=502,
            message="Impossible de générer le PDF",
        )

    filename = _build_pdf_filename(scan_data.url, scan_data.timestamp)
    return pdf_resp.content, filename
