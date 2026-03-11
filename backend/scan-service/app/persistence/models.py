"""Modèles SQLAlchemy pour la persistance des jobs async scan."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db import Base


class ScanAsyncJob(Base):
    """Job asynchrone de scan."""

    __tablename__ = "scan_async_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(String(128), nullable=True, index=True)
    url = Column(Text, nullable=False)
    scan_type = Column(String(20), nullable=False, default="frontend", server_default="frontend")
    input_json = Column(JSONB, nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    result_json = Column(JSONB, nullable=True)
    error_json = Column(JSONB, nullable=True)
    progress_log_json = Column(JSONB, nullable=False, default=list)
    last_step = Column(String(128), nullable=True)
    last_message = Column(Text, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    max_attempts = Column(Integer, nullable=False, default=3, server_default="3")
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    job_token_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
