"""Client HTTP enrichi pour les probes intrusifs.

Responsabilités :
- Injection automatique des credentials (cookie / bearer_token) sur chaque requête
- Toutes méthodes HTTP (GET, POST, PUT, DELETE, OPTIONS, HEAD, TRACE, PATCH)
- Suivi de redirections configurable : capture la chaîne ou suit jusqu'au final
- Timeouts configurables + jitter aléatoire entre requêtes (évite la détection)
- Session isolée par probe (aucun état partagé entre checks distincts)
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.schemas.async_job import ScanCredentials

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SecureOps-Scanner/1.1)",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class ProbeResult:
    """Résultat d'une requête HTTP de probe."""

    method: str
    url: str
    status_code: int
    headers: dict[str, str]
    body: str
    elapsed_ms: float
    redirect_chain: list[str] = field(default_factory=list)
    final_url: str = ""
    error: str | None = None

    @property
    def success(self) -> bool:
        """Indique l'absence d'erreur réseau ou de timeout."""
        return self.error is None

    @property
    def is_redirect(self) -> bool:
        """True si le statut HTTP est une redirection 3xx."""
        return self.status_code in (301, 302, 303, 307, 308)

    def location(self) -> str:
        """Retourne la valeur du header Location (vide si absent)."""
        return self.headers.get("location") or self.headers.get("Location") or ""


class IntrusiveHTTPClient:
    """Client HTTP enrichi pour les scans intrusifs.

    Usage typique (un client par check, pas partagé entre checks) :
        async with IntrusiveHTTPClient(credentials=creds) as client:
            result = await client.get(url)
    """

    def __init__(
        self,
        credentials: ScanCredentials | None = None,
        timeout: float = 8.0,
        jitter_min_ms: int = 50,
        jitter_max_ms: int = 250,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        """Configure credentials, timeouts, jitter et headers additionnels."""
        self._credentials = credentials
        self._timeout = timeout
        self._jitter_min_ms = jitter_min_ms
        self._jitter_max_ms = jitter_max_ms
        self._extra_headers = extra_headers or {}
        self._client: httpx.AsyncClient | None = None

    def _build_headers(self, override: dict[str, str] | None = None) -> dict[str, str]:
        """Fusionne les headers de base, credentials et overrides."""
        headers = dict(_DEFAULT_HEADERS)
        headers.update(self._extra_headers)
        if override:
            headers.update(override)
        # Injection credentials sur chaque requête
        if self._credentials:
            if self._credentials.cookie:
                headers["Cookie"] = self._credentials.cookie
            if self._credentials.bearer_token:
                headers["Authorization"] = f"Bearer {self._credentials.bearer_token}"
        return headers

    async def _jitter(self) -> None:
        """Délai aléatoire entre requêtes pour éviter la détection et réduire la charge."""
        if self._jitter_max_ms > 0:
            ms = random.randint(self._jitter_min_ms, self._jitter_max_ms)
            await asyncio.sleep(ms / 1000.0)

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        content: str | bytes | None = None,
        json: Any = None,
        follow_redirects: bool = False,
        max_redirects: int = 3,
    ) -> ProbeResult:
        """Envoie une requête HTTP et retourne un ProbeResult.

        Args:
            follow_redirects: Si True, suit les redirections jusqu'à max_redirects.
                              Si False, capture le header Location sans suivre.
        """
        await self._jitter()
        merged = self._build_headers(headers)
        start = time.monotonic()

        # Client httpx frais par requête pour isolation complète
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
            verify=False,  # cibles potentiellement avec certs auto-signés
        ) as client:
            try:
                kwargs: dict[str, Any] = {"headers": merged}
                if content is not None:
                    kwargs["content"] = content if isinstance(content, bytes) else content.encode()
                if json is not None:
                    kwargs["json"] = json

                resp = await client.request(method, url, **kwargs)
                elapsed = (time.monotonic() - start) * 1000

                # Chaîne de redirections (httpx l'expose via history)
                redirect_chain = [str(r.url) for r in resp.history] if hasattr(resp, "history") else []

                body = ""
                with suppress(Exception):
                    body = resp.text

                return ProbeResult(
                    method=method,
                    url=url,
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    body=body,
                    elapsed_ms=elapsed,
                    redirect_chain=redirect_chain,
                    final_url=str(resp.url),
                )
            except httpx.TimeoutException as exc:
                elapsed = (time.monotonic() - start) * 1000
                return ProbeResult(
                    method=method,
                    url=url,
                    status_code=0,
                    headers={},
                    body="",
                    elapsed_ms=elapsed,
                    error=f"Timeout: {exc}",
                )
            except Exception as exc:
                elapsed = (time.monotonic() - start) * 1000
                return ProbeResult(
                    method=method,
                    url=url,
                    status_code=0,
                    headers={},
                    body="",
                    elapsed_ms=elapsed,
                    error=str(exc),
                )

    async def get(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un GET."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un POST."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un PUT."""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un PATCH."""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un DELETE."""
        return await self.request("DELETE", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un OPTIONS."""
        return await self.request("OPTIONS", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un HEAD."""
        return await self.request("HEAD", url, **kwargs)

    async def trace(self, url: str, **kwargs: Any) -> ProbeResult:
        """Envoie un TRACE."""
        return await self.request("TRACE", url, **kwargs)
