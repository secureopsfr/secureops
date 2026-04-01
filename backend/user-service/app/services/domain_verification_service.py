"""Logique métier : challenges, vérification TXT, contrôle d'accès domaine."""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

import dns.exception
import dns.resolver
from common.url_helpers import registered_domain_from_url
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services import domain_verification_repository as repo
from app.services.dns_txt_verifier import lookup_txt_strings
from app.services.user_repository import get_user_by_cognito_sub

logger = logging.getLogger(__name__)

TOKEN_PREFIX = "secureops-verify-"
DNS_TXT_LABEL = "_secureops-verify"

CHALLENGE_TTL_DAYS = int(os.getenv("DOMAIN_VERIFICATION_CHALLENGE_TTL_DAYS", "7"))
VERIFICATION_VALIDITY_DAYS = int(os.getenv("DOMAIN_VERIFICATION_VALIDITY_DAYS", "90"))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_hex(16)


def _normalize_user_input_to_url(raw: str) -> str:
    s = raw.strip()
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    return s


def normalize_domain_from_user_input(raw: str) -> str:
    """Retourne l'eTLD+1 ou lève HTTPException 400 si invalide (IP, vide)."""
    url = _normalize_user_input_to_url(raw)
    domain = registered_domain_from_url(url)
    if not domain:
        raise HTTPException(status_code=400, detail="domain_invalid")
    try:
        ipaddress.ip_address(domain.split("%")[0])
        raise HTTPException(status_code=400, detail="domain_ip_not_supported")
    except ValueError:
        pass
    return domain.lower()


def txt_fqdn_for_domain(domain: str) -> str:
    """FQDN where the proof TXT record must be published."""
    return f"{DNS_TXT_LABEL}.{domain}"


async def create_challenge(session: AsyncSession, *, cognito_sub: str, raw_input: str) -> tuple[str, str, datetime, bool]:
    """Crée ou met à jour un challenge. Retourne (domain, token_plain, challenge_expires_at, already_verified)."""
    user = await get_user_by_cognito_sub(session, cognito_sub)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    domain = normalize_domain_from_user_input(raw_input)
    now = datetime.now(UTC)

    existing = await repo.get_verification_by_domain(session, domain)
    if existing and existing.expires_at > now:
        if existing.user_id == user.id:
            return domain, "", existing.expires_at, True
        raise HTTPException(status_code=409, detail="domain_owned_by_another_user")

    token = _generate_token()
    th = _token_hash(token)
    exp = now + timedelta(days=CHALLENGE_TTL_DAYS)
    await repo.upsert_challenge(session, user_id=user.id, domain=domain, token_hash=th, expires_at=exp)
    return domain, token, exp, False


async def _lookup_txt_or_raise(fqdn: str) -> list[str]:
    """Resolve TXT strings at fqdn or raise HTTPException with a dns_* detail."""
    try:
        return await lookup_txt_strings(fqdn)
    except dns.resolver.NXDOMAIN:
        raise HTTPException(status_code=400, detail="dns_nxdomain")
    except dns.resolver.NoAnswer:
        raise HTTPException(status_code=400, detail="dns_no_txt")
    except dns.exception.Timeout:
        raise HTTPException(status_code=400, detail="dns_timeout")
    except Exception as e:
        logger.warning("DNS TXT lookup failed for %s: %s", fqdn, e)
        raise HTTPException(status_code=400, detail="dns_resolution_failed")


async def _persist_verified_domain(
    session: AsyncSession,
    *,
    user: User,
    domain: str,
    verified_at: datetime,
    expires_at: datetime,
    now: datetime,
) -> None:
    """Insert or update domain_verifications after TXT proof; commit or map IntegrityError to 409."""
    existing = await repo.get_verification_by_domain(session, domain)
    try:
        if existing:
            if existing.user_id == user.id:
                existing.verified_at = verified_at
                existing.expires_at = expires_at
            elif existing.expires_at <= now:
                await repo.delete_verification(session, existing)
                await repo.insert_verification(
                    session,
                    user_id=user.id,
                    domain=domain,
                    verified_at=verified_at,
                    expires_at=expires_at,
                )
            else:
                raise HTTPException(status_code=409, detail="domain_owned_by_another_user")
        else:
            await repo.insert_verification(
                session,
                user_id=user.id,
                domain=domain,
                verified_at=verified_at,
                expires_at=expires_at,
            )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="domain_conflict_on_verify")


async def verify_challenge(session: AsyncSession, *, cognito_sub: str, domain: str) -> None:
    """Vérifie le TXT DNS et enregistre domain_verifications."""
    user = await get_user_by_cognito_sub(session, cognito_sub)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    domain = domain.strip().lower()
    now = datetime.now(UTC)

    taken = await repo.get_verification_by_domain(session, domain)
    if taken and taken.expires_at > now and taken.user_id != user.id:
        raise HTTPException(status_code=409, detail="domain_owned_by_another_user")

    ch = await repo.get_challenge(session, user.id, domain)
    if not ch:
        raise HTTPException(status_code=404, detail="challenge_not_found")
    if ch.expires_at <= now:
        raise HTTPException(status_code=400, detail="challenge_expired")

    fqdn = txt_fqdn_for_domain(domain)
    txts = await _lookup_txt_or_raise(fqdn)

    expected_hash = ch.token_hash
    matched = any(_token_hash(t.strip()) == expected_hash for t in txts)

    if not matched:
        raise HTTPException(status_code=400, detail="txt_mismatch")

    verified_at = now
    expires_at = now + timedelta(days=VERIFICATION_VALIDITY_DAYS)

    await repo.delete_challenges_for_domain(session, domain)
    await _persist_verified_domain(
        session,
        user=user,
        domain=domain,
        verified_at=verified_at,
        expires_at=expires_at,
        now=now,
    )


async def assert_domain_allowed(session: AsyncSession, *, cognito_sub: str, domain: str) -> tuple[bool, Optional[str]]:
    """Retourne (True, None) si le domaine est vérifié et actif pour cet utilisateur."""
    user = await get_user_by_cognito_sub(session, cognito_sub)
    if not user:
        return False, "user_not_found"
    d = domain.strip().lower()
    now = datetime.now(UTC)
    row = await repo.get_verification_by_domain(session, d)
    if not row or row.expires_at <= now:
        return False, "domain_not_verified"
    if row.user_id != user.id:
        return False, "domain_owned_by_another_user"
    return True, None


async def delete_verification_for_user(session: AsyncSession, *, cognito_sub: str, verification_id: UUID) -> None:
    """Remove a verification row owned by the user."""
    user = await get_user_by_cognito_sub(session, cognito_sub)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    row = await repo.get_verification_by_id_and_user(session, verification_id, user.id)
    if not row:
        raise HTTPException(status_code=404, detail="verification_not_found")
    await repo.delete_verification(session, row)
    await session.commit()


def authorization_check_enabled() -> bool:
    """True when scan-service must assert domain ownership for non-passive scans."""
    return os.getenv("AUTHORIZATION_CHECK_ENABLED", "").lower() in ("1", "true", "yes")


async def scheduled_scan_may_run(
    session: AsyncSession,
    *,
    cognito_sub: str,
    normalized_url: str,
    scan_mode: str,
) -> bool:
    """Retourne False si le scan planifié non passif ne peut pas s'exécuter (domaine non vérifié)."""
    if scan_mode == "passive" or not authorization_check_enabled():
        return True

    domain = registered_domain_from_url(normalized_url).lower()
    allowed, _ = await assert_domain_allowed(session, cognito_sub=cognito_sub, domain=domain)
    return allowed
