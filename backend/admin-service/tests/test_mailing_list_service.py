"""Tests unitaires du service mailing list."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

import app.services.mailing_list_service as mailing_list_service_module


@dataclass
class _FakeUser:
    id: str
    email: str
    created_at: datetime
    subscription: object | None = None


@dataclass
class _FakeSubscription:
    user_id: str
    newsletter_enabled: bool = False
    new_features_notifications_enabled: bool = False
    updated_at: datetime | None = None


class _FakeQuery:
    def __init__(self, user: _FakeUser | None = None, subscription: _FakeSubscription | None = None):
        self._user = user
        self._subscription = subscription

    def filter(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self

    def first(self):  # type: ignore[no-untyped-def]
        if self._subscription is not None:
            return self._subscription
        return self._user

    def join(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self

    def order_by(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self

    def offset(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self

    def limit(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self

    def all(self):  # type: ignore[no-untyped-def]
        return []

    def count(self):  # type: ignore[no-untyped-def]
        return 0


class _FakeDB:
    def __init__(self, user: _FakeUser | None = None, subscription: _FakeSubscription | None = None):
        self.user = user
        self.subscription = subscription
        self.committed = False
        self.rolled_back = False

    def query(self, model):  # type: ignore[no-untyped-def]
        model_name = getattr(model, "__name__", "")
        if model_name == "User":
            return _FakeQuery(user=self.user)
        return _FakeQuery(subscription=self.subscription)

    def add(self, obj):  # type: ignore[no-untyped-def]
        self.subscription = obj

    def commit(self):  # type: ignore[no-untyped-def]
        self.committed = True

    def rollback(self):  # type: ignore[no-untyped-def]
        self.rolled_back = True


class _Ctx:
    def __init__(self, db: _FakeDB):
        self.db = db

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self.db

    def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
        return False


def test_verify_email_returns_success(monkeypatch) -> None:
    """verify_email doit renvoyer success=True."""
    now = datetime.now(timezone.utc)
    user = _FakeUser(id="u1", email="john@example.com", created_at=now)
    db = _FakeDB(user=user, subscription=None)
    monkeypatch.setattr(mailing_list_service_module, "get_sync_session", lambda: _Ctx(db))

    service = mailing_list_service_module.MailingListService()
    result = service.verify_email("john@example.com")

    assert result["success"] is True
    assert result["email"] == "john@example.com"
    assert db.committed is True


def test_unsubscribe_email_missing_user_raises_value_error(monkeypatch) -> None:
    """unsubscribe_email doit lever ValueError si utilisateur introuvable."""
    db = _FakeDB(user=None, subscription=None)
    monkeypatch.setattr(mailing_list_service_module, "get_sync_session", lambda: _Ctx(db))

    service = mailing_list_service_module.MailingListService()
    with pytest.raises(ValueError):
        service.unsubscribe_email("nobody@example.com")
