"""Tests unitaires pour les vérifications Cookies (passive)."""

from unittest.mock import MagicMock

from app.services.passive.both.cookies import check_cookies_from_response


def test_check_cookies_response_none() -> None:
    """check_cookies_from_response retourne fetch_ok=False quand response est None."""
    result = check_cookies_from_response(None)

    assert result.fetch_ok is False
    assert result.cookies == ()
    assert len(result.findings) == 1
    assert "cookies" in result.findings[0].lower()


def test_check_cookies_aucun_cookie() -> None:
    """check_cookies_from_response avec réponse sans Set-Cookie retourne liste vide."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [(b"content-type", b"text/html")]

    result = check_cookies_from_response(mock_resp)

    assert result.fetch_ok is True
    assert result.cookies == ()
    assert result.findings == ()


def test_check_cookies_secure_httponly_samesite_ok() -> None:
    """Cookie avec Secure, HttpOnly, SameSite=Strict ne génère pas de finding session-incomplete."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"session_id=abc; Secure; HttpOnly; SameSite=Strict"),
    ]

    result = check_cookies_from_response(mock_resp, is_https=True)

    assert result.fetch_ok is True
    assert len(result.cookies) == 1
    assert result.cookies[0].name == "session_id"
    assert result.cookies[0].secure is True
    assert result.cookies[0].httponly is True
    assert result.cookies[0].samesite == "Strict"
    assert not any("HttpOnly + Secure + SameSite=Strict" in f for f in result.findings)
    assert any("sans préfixe __Host-" in f for f in result.findings)


def test_check_cookies_sans_secure_site_https() -> None:
    """Cookie session sans Secure sur site HTTPS génère un finding session-incomplete."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"session=xyz; HttpOnly; Path=/"),
    ]

    result = check_cookies_from_response(mock_resp, is_https=True)

    assert result.fetch_ok is True
    assert len(result.cookies) == 1
    assert result.cookies[0].secure is False
    assert any("HttpOnly + Secure + SameSite=Strict" in f for f in result.findings)


def test_check_cookies_non_session_sans_secure() -> None:
    """Cookie non-session (ex. lang) sans Secure sur HTTPS génère finding Secure classique."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"lang=fr; HttpOnly; Path=/"),
    ]

    result = check_cookies_from_response(mock_resp, is_https=True)

    assert any("Secure" in f and "interception" in f for f in result.findings)


def test_check_cookies_sans_httponly() -> None:
    """Cookie session sans HttpOnly génère un finding (session-incomplete ou HttpOnly)."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"token=abc; Secure; Path=/"),
    ]

    result = check_cookies_from_response(mock_resp)

    assert any("HttpOnly" in f for f in result.findings)


def test_check_cookies_sans_samesite() -> None:
    """Cookie sans SameSite explicite génère un finding."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"lang=fr; Secure; HttpOnly; Path=/"),
    ]

    result = check_cookies_from_response(mock_resp)

    assert any("SameSite" in f for f in result.findings)


def test_check_cookies_plusieurs_cookies() -> None:
    """Plusieurs Set-Cookie sont tous analysés."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"a=1; Secure; HttpOnly; SameSite=Strict"),
        (b"set-cookie", b"b=2; Path=/"),
    ]

    result = check_cookies_from_response(mock_resp, is_https=True)

    assert len(result.cookies) == 2
    assert result.cookies[0].name == "a"
    assert result.cookies[1].name == "b"
    assert any("'b'" in f for f in result.findings)


def test_check_cookies_samesite_none_sans_secure() -> None:
    """SameSite=None sans Secure génère un finding."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"widget=id; SameSite=None; Path=/"),
    ]

    result = check_cookies_from_response(mock_resp)

    assert any("SameSite=None" in f and "Secure" in f for f in result.findings)


def test_check_cookies_host_prefix_ok() -> None:
    """Cookie __Host- avec triple protection ne génère pas de finding préfixe."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"__Host-session=abc; Secure; HttpOnly; SameSite=Strict; Path=/"),
    ]

    result = check_cookies_from_response(mock_resp, is_https=True)

    assert result.fetch_ok is True
    assert result.cookies[0].has_host_prefix is True
    assert not any("sans préfixe __Host-" in f for f in result.findings)


def test_check_cookies_third_party_sans_partitioned() -> None:
    """Cookie _ga sans Partitioned génère un finding."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"_ga=GA1.2.123; Path=/; Max-Age=63072000; SameSite=Lax"),
    ]

    result = check_cookies_from_response(mock_resp)

    assert any("sans Partitioned" in f for f in result.findings)
    assert any("_ga" in f for f in result.findings)


def test_check_cookies_third_party_avec_partitioned() -> None:
    """Cookie _ga avec Partitioned ne génère pas de finding Partitioned."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"_ga=GA1.2.123; Path=/; Partitioned; SameSite=Lax"),
    ]

    result = check_cookies_from_response(mock_resp)

    assert not any("sans Partitioned" in f for f in result.findings)


def test_check_cookies_session_expires_long() -> None:
    """Cookie de session avec Max-Age > 24h génère un finding."""
    mock_resp = MagicMock()
    mock_resp.headers.raw = [
        (b"set-cookie", b"session_id=abc; Secure; HttpOnly; SameSite=Strict; Max-Age=31536000"),
    ]

    result = check_cookies_from_response(mock_resp)

    assert any("Expires/Max-Age > 24h" in f or "session persistante" in f for f in result.findings)
