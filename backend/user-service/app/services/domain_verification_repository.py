"""Accès base pour domain_verifications et domain_verification_challenges."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_verification import DomainVerification, DomainVerificationChallenge


async def get_verification_by_domain(session: AsyncSession, domain: str) -> Optional[DomainVerification]:
    """Return active verification row for this domain, if any."""
    r = await session.execute(select(DomainVerification).where(DomainVerification.domain == domain))
    return r.scalar_one_or_none()


async def list_verifications_for_user(
    session: AsyncSession,
    user_id: UUID,
    *,
    active_only: bool = True,
) -> list[DomainVerification]:
    """List verifications for a user; optionally filter out expired rows."""
    q = select(DomainVerification).where(DomainVerification.user_id == user_id)
    if active_only:
        q = q.where(DomainVerification.expires_at > datetime.now(UTC))
    q = q.order_by(DomainVerification.domain)
    r = await session.execute(q)
    return list(r.scalars().all())


async def get_verification_by_id_and_user(
    session: AsyncSession,
    verification_id: UUID,
    user_id: UUID,
) -> Optional[DomainVerification]:
    """Return verification row for (user_id, verification_id), if any."""
    r = await session.execute(
        select(DomainVerification).where(
            DomainVerification.id == verification_id,
            DomainVerification.user_id == user_id,
        )
    )
    return r.scalar_one_or_none()


async def insert_verification(
    session: AsyncSession,
    *,
    user_id: UUID,
    domain: str,
    verified_at: datetime,
    expires_at: datetime,
) -> DomainVerification:
    """Insert a new domain_verifications row."""
    row = DomainVerification(
        user_id=user_id,
        domain=domain,
        verified_at=verified_at,
        expires_at=expires_at,
    )
    session.add(row)
    await session.flush()
    return row


async def delete_verification(session: AsyncSession, row: DomainVerification) -> None:
    """Delete a domain_verifications row."""
    await session.delete(row)


async def get_challenge(session: AsyncSession, user_id: UUID, domain: str) -> Optional[DomainVerificationChallenge]:
    """Return pending challenge for (user_id, domain), if any."""
    r = await session.execute(
        select(DomainVerificationChallenge).where(
            DomainVerificationChallenge.user_id == user_id,
            DomainVerificationChallenge.domain == domain,
        )
    )
    return r.scalar_one_or_none()


async def upsert_challenge(
    session: AsyncSession,
    *,
    user_id: UUID,
    domain: str,
    token_hash: str,
    expires_at: datetime,
) -> DomainVerificationChallenge:
    """Create or replace token hash and expiry for a user's domain challenge."""
    existing = await get_challenge(session, user_id, domain)
    now = datetime.now(UTC)
    if existing:
        existing.token_hash = token_hash
        existing.expires_at = expires_at
        existing.created_at = now
        await session.flush()
        return existing
    row = DomainVerificationChallenge(
        user_id=user_id,
        domain=domain,
        token_hash=token_hash,
        created_at=now,
        expires_at=expires_at,
    )
    session.add(row)
    await session.flush()
    return row


async def delete_challenge(session: AsyncSession, row: DomainVerificationChallenge) -> None:
    """Delete a single challenge row."""
    await session.delete(row)


async def delete_challenges_for_domain(session: AsyncSession, domain: str) -> None:
    """Remove all pending challenges for this domain (any user)."""
    await session.execute(delete(DomainVerificationChallenge).where(DomainVerificationChallenge.domain == domain))
