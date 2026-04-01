"""Tests minimum des endpoints async scan."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from common.async_jobs import hash_job_token


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


def test_create_async_scan_returns_job_token_for_anonymous(client):
    """POST create returns token for anonymous frontend scan jobs."""
    job = _fake_job(id="123e4567-e89b-12d3-a456-426614174000")
    with (
        patch("app.routers.scan.get_async_session", _fake_session_ctx),
        patch("app.routers.scan.create_job", new=AsyncMock(return_value=job)),
    ):
        resp = client.post("/api/scan/async", json={"url": "https://example.com", "scan_type": "frontend", "input": {}})
    assert resp.status_code == 202
    data = resp.json()
    assert data["job_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert data["status"] == "pending"
    assert data["scan_type"] == "frontend"
    assert data.get("job_token")


def test_create_async_scan_anonymous_rejects_non_passive_mode(client):
    """Anonymous create only allows frontend passive scans."""
    resp = client.post(
        "/api/scan/async",
        json={
            "url": "https://example.com",
            "scan_type": "frontend",
            "scan_mode": "intrusive",
            "input": {},
        },
    )
    assert resp.status_code == 401
    assert "mode passif" in resp.json().get("detail", "")


def test_get_async_scan_status_enforces_ownership(client):
    """Status endpoint denies access when authenticated user mismatches owner."""
    job = _fake_job(user_id="user-a")
    with (
        patch("app.routers.scan.get_async_session", _fake_session_ctx),
        patch("app.routers.scan.get_job_by_id", new=AsyncMock(return_value=job)),
    ):
        resp = client.get("/api/scan/async/00000000-0000-0000-0000-000000000001", headers={"X-Authenticated-User-Id": "user-b"})
    assert resp.status_code == 403


def test_get_async_scan_result_returns_409_when_not_completed(client):
    """Result endpoint returns 409 when job is not yet completed."""
    job = _fake_job(user_id="user-a", status="running")
    with (
        patch("app.routers.scan.get_async_session", _fake_session_ctx),
        patch("app.routers.scan.get_job_by_id", new=AsyncMock(return_value=job)),
    ):
        resp = client.get("/api/scan/async/00000000-0000-0000-0000-000000000001/result", headers={"X-Authenticated-User-Id": "user-a"})
    assert resp.status_code == 409


def test_get_async_scan_status_anonymous_requires_valid_job_token(client):
    """Anonymous status access requires a valid X-Job-Token."""
    token = "plain-token"
    token_hash = hash_job_token(token, "dev-async-job-secret")
    job = _fake_job(user_id=None, job_token_hash=token_hash)
    with (
        patch("app.routers.scan.get_async_session", _fake_session_ctx),
        patch("app.routers.scan.get_job_by_id", new=AsyncMock(return_value=job)),
    ):
        ok = client.get(
            "/api/scan/async/00000000-0000-0000-0000-000000000001",
            headers={"X-Job-Token": token},
        )
        ko = client.get("/api/scan/async/00000000-0000-0000-0000-000000000001")
    assert ok.status_code == 200
    assert ko.status_code == 403


def test_internal_run_scan_forwards_scan_type_and_mode(client):
    """Internal single scan endpoint forwards scan_type/scan_mode to executor."""
    with patch(
        "app.routers.scan.execute_scan_job",
        new=AsyncMock(return_value=({"status": "success", "score": 99}, None)),
    ) as mocked_execute:
        resp = client.post(
            "/api/internal/scan/run",
            json={
                "url": "https://example.com",
                "scan_type": "backend",
                "scan_mode": "intrusive",
            },
        )

    assert resp.status_code == 200
    assert resp.json()["score"] == 99
    mocked_execute.assert_awaited_once_with(
        url="https://example.com/",
        scan_type="backend",
        scan_mode="intrusive",
    )


def test_internal_run_scan_uses_default_scan_type_and_mode(client):
    """Internal single scan endpoint applies frontend/passive defaults."""
    with patch(
        "app.routers.scan.execute_scan_job",
        new=AsyncMock(return_value=({"status": "success", "score": 100}, None)),
    ) as mocked_execute:
        resp = client.post(
            "/api/internal/scan/run",
            json={"url": "https://example.com"},
        )

    assert resp.status_code == 200
    assert resp.json()["score"] == 100
    mocked_execute.assert_awaited_once_with(
        url="https://example.com/",
        scan_type="frontend",
        scan_mode="passive",
    )


def test_internal_run_multi_scan_forwards_scan_type_and_mode(client):
    """Internal multi scan endpoint forwards scan_type/scan_mode to executor."""
    with patch(
        "app.routers.scan.execute_multi_scan_job",
        new=AsyncMock(return_value=({"status": "success", "score_global": 88}, None)),
    ) as mocked_execute:
        resp = client.post(
            "/api/internal/scan/run-multi",
            json={
                "urls": ["https://example.com/a", "https://example.com/b"],
                "scan_type": "backend",
                "scan_mode": "destructive",
            },
        )

    assert resp.status_code == 200
    assert resp.json()["score_global"] == 88
    mocked_execute.assert_awaited_once_with(
        urls=["https://example.com/a", "https://example.com/b"],
        scan_type="backend",
        scan_mode="destructive",
    )
