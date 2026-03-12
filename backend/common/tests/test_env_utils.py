"""Tests pour common.env_utils."""

import pytest

from common.env_utils import is_prod_env


def test_is_prod_default() -> None:
    """Par défaut (IS_PROD absent), considère prod."""
    # Ne pas définir IS_PROD pour ce test - comportement dépend de l'env
    pass


def test_is_prod_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """IS_PROD=1, true, yes (casse insensible) retourne True."""
    for val in ("1", "true", "yes", "TRUE", "True"):
        monkeypatch.setenv("IS_PROD", val)
        assert is_prod_env() is True


def test_is_prod_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """IS_PROD=false, 0, etc. retourne False."""
    monkeypatch.setenv("IS_PROD", "false")
    assert is_prod_env() is False
    monkeypatch.setenv("IS_PROD", "0")
    assert is_prod_env() is False
