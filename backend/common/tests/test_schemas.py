"""Tests unitaires pour common.schemas."""

from common.schemas import (
    DeleteResponse,
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
    make_pagination_meta,
)


def test_success_response_defaults() -> None:
    """SuccessResponse has success=True by default."""
    r = SuccessResponse(message="OK")
    assert r.success is True
    assert r.message == "OK"


def test_error_response_defaults() -> None:
    """ErrorResponse a success=False par défaut."""
    r = ErrorResponse(error="Something went wrong")
    assert r.success is False
    assert r.error == "Something went wrong"
    assert r.detail is None


def test_error_response_with_detail() -> None:
    """ErrorResponse can have an optional detail field."""
    r = ErrorResponse(error="Err", detail="Extra info")
    assert r.detail == "Extra info"


def test_delete_response_defaults() -> None:
    """DeleteResponse has a default message."""
    r = DeleteResponse()
    assert r.success is True
    assert "Suppression" in r.message or r.message


def test_paginated_response() -> None:
    """PaginatedResponse serializes correctly."""
    r = PaginatedResponse(items=[{"id": 1}], total=100, limit=10, offset=0)
    assert r.items == [{"id": 1}]
    assert r.total == 100
    assert r.limit == 10
    assert r.offset == 0


def test_make_pagination_meta() -> None:
    """make_pagination_meta calcule page, per_page, total_pages."""
    meta = make_pagination_meta(total=95, limit=10, offset=20)
    assert meta["total"] == 95
    assert meta["page"] == 3
    assert meta["per_page"] == 10
    assert meta["total_pages"] == 10
