"""Tests minimum des endpoints async crawl."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from common.async_jobs import hash_job_token
from fastapi.testclient import TestClient

from app.main import app


def _fake_job(**overrides):
    now = datetime.now(UTC)
    base = {
        "id": overrides.get("id", "00000000-0000-0000-0000-000000000001"),
        "user_id": overrides.get("user_id"),
        "url": overrides.get("url", "https://example.com"),
        "scan_type": overrides.get("scan_type", "frontend"),
        "status": overrides.get("status", "pending"),
        "result_json": overrides.get("result_json"),
        "error_json": overrides.get("error_json"),
        "progress_log_json": overrides.get("progress_log_json", []),
        "last_step": overrides.get("last_step"),
        "last_message": overrides.get("last_message"),
        "attempt_count": overrides.get("attempt_count", 0),
        "max_attempts": overrides.get("max_attempts", 3),
        "next_retry_at": None,
        "job_token_hash": overrides.get("job_token_hash"),
        "created_at": overrides.get("created_at", now),
        "started_at": overrides.get("started_at"),
        "completed_at": overrides.get("completed_at"),
        "expires_at": None,
    }
    return SimpleNamespace(**base)


@asynccontextmanager
async def _fake_session_ctx():
    yield object()


def test_create_async_crawl_returns_job_token_for_anonymous() -> None:
    """POST create returns token for anonymous frontend crawl jobs."""
    client = TestClient(app)
    job = _fake_job(id="123e4567-e89b-12d3-a456-426614174000")
    with (
        patch("app.routers.crawl.get_async_session", _fake_session_ctx),
        patch("app.routers.crawl.create_job", new=AsyncMock(return_value=job)),
    ):
        resp = client.post("/api/crawl/async", json={"url": "https://example.com", "scan_type": "frontend", "input": {}})
    assert resp.status_code == 202
    data = resp.json()
    assert data["job_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert data["status"] == "pending"
    assert data["scan_type"] == "frontend"
    assert data.get("job_token")


def test_get_async_crawl_status_enforces_ownership() -> None:
    """Status endpoint denies access when authenticated user mismatches owner."""
    client = TestClient(app)
    job = _fake_job(user_id="user-a")
    with (
        patch("app.routers.crawl.get_async_session", _fake_session_ctx),
        patch("app.routers.crawl.get_job_by_id", new=AsyncMock(return_value=job)),
    ):
        resp = client.get("/api/crawl/async/00000000-0000-0000-0000-000000000001", headers={"X-Authenticated-User-Id": "user-b"})
    assert resp.status_code == 403


def test_get_async_crawl_result_returns_409_when_not_completed() -> None:
    """Result endpoint returns 409 when job is not yet completed."""
    client = TestClient(app)
    job = _fake_job(user_id="user-a", status="running")
    with (
        patch("app.routers.crawl.get_async_session", _fake_session_ctx),
        patch("app.routers.crawl.get_job_by_id", new=AsyncMock(return_value=job)),
    ):
        resp = client.get("/api/crawl/async/00000000-0000-0000-0000-000000000001/result", headers={"X-Authenticated-User-Id": "user-a"})
    assert resp.status_code == 409


def test_get_async_crawl_status_anonymous_requires_valid_job_token() -> None:
    """Anonymous status access requires a valid X-Job-Token."""
    client = TestClient(app)
    token = "plain-token"
    token_hash = hash_job_token(token, "dev-async-job-secret")
    job = _fake_job(user_id=None, job_token_hash=token_hash)
    with (
        patch("app.routers.crawl.get_async_session", _fake_session_ctx),
        patch("app.routers.crawl.get_job_by_id", new=AsyncMock(return_value=job)),
    ):
        ok = client.get(
            "/api/crawl/async/00000000-0000-0000-0000-000000000001",
            headers={"X-Job-Token": token},
        )
        ko = client.get("/api/crawl/async/00000000-0000-0000-0000-000000000001")
    assert ok.status_code == 200
    assert ko.status_code == 403
