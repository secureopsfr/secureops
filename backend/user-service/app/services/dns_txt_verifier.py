"""Résolution DNS TXT pour la vérification de domaine."""

from __future__ import annotations

import logging

import dns.asyncresolver

logger = logging.getLogger(__name__)

DEFAULT_DNS_LIFETIME_S = 10.0


async def lookup_txt_strings(fqdn: str, *, lifetime_s: float = DEFAULT_DNS_LIFETIME_S) -> list[str]:
    """Retourne une liste de chaînes TXT (une par enregistrement TXT distinct).

    Propage les exceptions ``dns`` (NXDOMAIN, NoAnswer, Timeout, etc.).
    """
    answer = await dns.asyncresolver.resolve(fqdn, "TXT", lifetime=lifetime_s)
    result: list[str] = []
    for rdata in answer:
        combined = b"".join(rdata.strings)
        result.append(combined.decode("utf-8", errors="replace").strip())
    return result
