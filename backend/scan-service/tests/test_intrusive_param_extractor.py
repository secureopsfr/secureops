"""Tests unitaires — extraction de paramètres (app.services.intrusive.lib.param_extractor)."""

from __future__ import annotations

import pytest

from app.services.intrusive.lib.param_extractor import (
    COMMON_CMD_PARAMS,
    COMMON_FILE_PARAMS,
    COMMON_INJECTION_PARAMS,
    COMMON_LOGIN_ENDPOINTS,
    COMMON_REDIRECT_PARAMS,
    ExtractedParam,
    ParamContext,
    detect_output_context,
    extract_body_params,
    extract_html_params,
    extract_query_params,
    has_file_input,
    inject_param,
    inject_query_param,
)

# ─── extract_query_params ─────────────────────────────────────────────────────


def test_extract_query_params_basic() -> None:
    """Extract_query_params extrait les paramètres de la chaîne de requête."""
    params = extract_query_params("https://example.com/?id=1&name=foo")
    names = {p.name for p in params}
    assert "id" in names
    assert "name" in names


def test_extract_query_params_values() -> None:
    """Extract_query_params extrait les valeurs des paramètres."""
    params = extract_query_params("https://example.com/?q=hello")
    assert any(p.name == "q" and p.value == "hello" for p in params)


def test_extract_query_params_empty() -> None:
    """Extract_query_params retourne une liste vide si aucun paramètre n'est présent."""
    params = extract_query_params("https://example.com/")
    assert params == []


def test_extract_query_params_context() -> None:
    """Extract_query_params retourne le contexte QUERY_STRING pour chaque paramètre."""
    params = extract_query_params("https://example.com/?x=1")
    assert all(p.context == ParamContext.QUERY_STRING for p in params)


def test_extract_query_params_preserves_url() -> None:
    """Extract_query_params conserve l'URL originale pour chaque paramètre."""
    url = "https://example.com/?x=1"
    params = extract_query_params(url)
    assert all(p.original_url == url for p in params)


def test_extract_query_params_multiple_values_takes_first() -> None:
    """Extract_query_params prend la première valeur si plusieurs sont présentes."""
    params = extract_query_params("https://example.com/?x=1&x=2")
    x_params = [p for p in params if p.name == "x"]
    assert len(x_params) == 1
    assert x_params[0].value == "1"


def test_extract_query_params_encoded_chars() -> None:
    """Extract_query_params gère les caractères encodés."""
    params = extract_query_params("https://example.com/?q=hello%20world")
    assert any(p.name == "q" for p in params)


# ─── inject_query_param ───────────────────────────────────────────────────────


def test_inject_query_param_replaces_existing() -> None:
    """Inject_query_param remplace un paramètre existant."""
    url = inject_query_param("https://example.com/?id=1", "id", "99")
    assert "id=99" in url
    assert "id=1" not in url


def test_inject_query_param_adds_new_param() -> None:
    """Inject_query_param ajoute un nouveau paramètre."""
    url = inject_query_param("https://example.com/", "q", "test")
    assert "q=test" in url


def test_inject_query_param_preserves_other_params() -> None:
    """Inject_query_param conserve les autres paramètres."""
    url = inject_query_param("https://example.com/?a=1&b=2", "a", "99")
    assert "b=2" in url


def test_inject_query_param_returns_string() -> None:
    """Inject_query_param retourne une chaîne de caractères."""
    result = inject_query_param("https://example.com/?x=1", "x", "evil")
    assert isinstance(result, str)


def test_inject_query_param_preserves_scheme() -> None:
    """Inject_query_param conserve le schéma HTTP."""
    result = inject_query_param("https://example.com/?x=1", "x", "v")
    assert result.startswith("https://")


# ─── inject_param ─────────────────────────────────────────────────────────────


def test_inject_param_query_string() -> None:
    """Inject_param injecte un paramètre dans une chaîne de requête."""
    param = ExtractedParam(
        name="id",
        value="1",
        context=ParamContext.QUERY_STRING,
        original_url="https://example.com/?id=1",
    )
    result = inject_param(param, "99")
    assert "id=99" in result


def test_inject_param_non_query_returns_url() -> None:
    """Inject_param retourne l'URL originale si le paramètre n'est pas dans la chaîne de requête."""
    param = ExtractedParam(
        name="field",
        value="val",
        context=ParamContext.BODY_JSON,
        original_url="https://example.com/",
    )
    result = inject_param(param, "payload")
    assert result == "https://example.com/"


# ─── extract_body_params ──────────────────────────────────────────────────────


def test_extract_body_params_json_flat() -> None:
    """Extract_body_params extrait les paramètres d'un body JSON plat."""
    body = '{"username": "admin", "password": "secret"}'
    params = extract_body_params(body, "application/json")
    names = {p.name for p in params}
    assert "username" in names
    assert "password" in names


def test_extract_body_params_json_context() -> None:
    """Extract_body_params retourne le contexte BODY_JSON pour chaque paramètre."""
    params = extract_body_params('{"key": "val"}', "application/json")
    assert all(p.context == ParamContext.BODY_JSON for p in params)


def test_extract_body_params_json_nested_ignored() -> None:
    """Extract_body_params ignore les objets imbriqués."""
    body = '{"user": {"name": "admin"}}'
    params = extract_body_params(body, "application/json")
    # Les objets imbriqués ne sont pas extraits (non scalar)
    names = {p.name for p in params}
    assert "user" not in names


def test_extract_body_params_form_urlencoded() -> None:
    """Extract_body_params extrait les paramètres d'un body form-urlencoded."""
    body = "username=admin&password=secret"
    params = extract_body_params(body, "application/x-www-form-urlencoded")
    names = {p.name for p in params}
    assert "username" in names
    assert "password" in names


def test_extract_body_params_form_context() -> None:
    """Extract_body_params retourne le contexte BODY_FORM pour chaque paramètre."""
    params = extract_body_params("key=val", "application/x-www-form-urlencoded")
    assert all(p.context == ParamContext.BODY_FORM for p in params)


def test_extract_body_params_invalid_json_returns_empty() -> None:
    """Extract_body_params retourne une liste vide si le JSON est invalide."""
    params = extract_body_params("{not valid json", "application/json")
    assert params == []


def test_extract_body_params_unknown_content_type() -> None:
    """Extract_body_params retourne une liste vide si le content type est inconnu."""
    params = extract_body_params("data=value", "text/plain")
    assert params == []


# ─── extract_html_params ──────────────────────────────────────────────────────


_FORM_HTML = """
<html><body>
<form action="/search" method="GET">
  <input type="text" name="query" value="">
  <input type="text" name="page" value="1">
  <input type="submit" value="Search">
</form>
<a href="/items?id=42">Item</a>
</body></html>
"""

_FORM_POST_HTML = """
<html><body>
<form action="/login" method="POST">
  <input type="text" name="username">
  <input type="password" name="password">
  <input type="hidden" name="_csrf" value="token123">
</form>
</body></html>
"""


def test_extract_html_params_from_form() -> None:
    """Extract_html_params extrait les paramètres d'un formulaire HTML."""
    params = extract_html_params(_FORM_HTML, "https://example.com/")
    names = {p.name for p in params}
    assert "query" in names
    assert "page" in names


def test_extract_html_params_excludes_submit() -> None:
    """Extract_html_params exclut les champs submit."""
    params = extract_html_params(_FORM_HTML, "https://example.com/")
    names = {p.name for p in params}
    assert "value" not in names


def test_extract_html_params_from_links() -> None:
    """Extract_html_params extrait les paramètres d'un lien HTML."""
    params = extract_html_params(_FORM_HTML, "https://example.com/")
    names = {p.name for p in params}
    assert "id" in names


def test_extract_html_params_excludes_hidden() -> None:
    """Extract_html_params exclut les champs hidden."""
    params = extract_html_params(_FORM_POST_HTML, "https://example.com/")
    names = {p.name for p in params}
    # Les champs hidden sont exclus
    assert "_csrf" not in names


def test_extract_html_params_form_context() -> None:
    """Extract_html_params retourne le contexte HTML_FORM pour chaque paramètre."""
    params = extract_html_params(_FORM_HTML, "https://example.com/")
    form_params = [p for p in params if p.context == ParamContext.HTML_FORM]
    assert len(form_params) > 0


def test_extract_html_params_empty_html() -> None:
    """Extract_html_params retourne une liste vide si le HTML est vide."""
    params = extract_html_params("", "https://example.com/")
    assert params == []


def test_extract_html_params_no_form() -> None:
    """Extract_html_params retourne une liste vide si le HTML ne contient pas de formulaire."""
    html = "<html><body><p>No form here</p></body></html>"
    params = extract_html_params(html, "https://example.com/")
    assert params == []


# ─── has_file_input ───────────────────────────────────────────────────────────


def test_has_file_input_present() -> None:
    """has_file_input retourne True si le HTML contient un <input type='file'>."""
    html = '<form><input type="file" name="upload"></form>'
    assert has_file_input(html) is True


def test_has_file_input_absent() -> None:
    """has_file_input retourne False si le HTML ne contient pas un <input type='file'>."""
    html = '<form><input type="text" name="query"></form>'
    assert has_file_input(html) is False


def test_has_file_input_empty_html() -> None:
    """has_file_input retourne False si le HTML est vide."""
    assert has_file_input("") is False


def test_has_file_input_case_insensitive_type() -> None:
    """has_file_input retourne True si le HTML contient un <input type='FILE'>."""
    html = '<form><input type="FILE" name="upload"></form>'
    assert has_file_input(html) is True


# ─── detect_output_context ────────────────────────────────────────────────────


def test_detect_output_context_script() -> None:
    """detect_output_context détecte un script."""
    html = "<script>var x = 'sec0p5-abc';</script>"
    assert detect_output_context(html, "sec0p5-abc") == "script"


def test_detect_output_context_attr() -> None:
    """detect_output_context détecte un attribut."""
    html = '<img src="sec0p5-abc" />'
    assert detect_output_context(html, "sec0p5-abc") == "attr"


def test_detect_output_context_text() -> None:
    """detect_output_context détecte du texte."""
    html = "<p>Hello sec0p5-abc world</p>"
    assert detect_output_context(html, "sec0p5-abc") == "text"


def test_detect_output_context_none_if_absent() -> None:
    """detect_output_context retourne none si le marker n'est pas présent."""
    html = "<p>Nothing here</p>"
    assert detect_output_context(html, "sec0p5-abc") == "none"


def test_detect_output_context_empty_body() -> None:
    """detect_output_context retourne none si le body est vide."""
    assert detect_output_context("", "marker") == "none"


# ─── Listes de constantes ─────────────────────────────────────────────────────


def test_common_redirect_params_not_empty() -> None:
    """Les paramètres de redirection ne sont pas vides."""
    assert len(COMMON_REDIRECT_PARAMS) > 0
    assert "redirect" in COMMON_REDIRECT_PARAMS
    assert "next" in COMMON_REDIRECT_PARAMS


def test_common_file_params_not_empty() -> None:
    """Les paramètres de fichier ne sont pas vides."""
    assert len(COMMON_FILE_PARAMS) > 0
    assert "file" in COMMON_FILE_PARAMS


def test_common_cmd_params_not_empty() -> None:
    """Les paramètres de commande ne sont pas vides."""
    assert len(COMMON_CMD_PARAMS) > 0
    assert "cmd" in COMMON_CMD_PARAMS


def test_common_injection_params_not_empty() -> None:
    """Les paramètres d'injection ne sont pas vides."""
    assert len(COMMON_INJECTION_PARAMS) > 0
    assert "id" in COMMON_INJECTION_PARAMS


def test_common_login_endpoints_not_empty() -> None:
    """Les endpoints de login ne sont pas vides."""
    assert len(COMMON_LOGIN_ENDPOINTS) > 0
    assert "/login" in COMMON_LOGIN_ENDPOINTS


def test_extracted_param_dataclass_frozen() -> None:
    """La ExtractedParam est un dataclass immuable."""
    p = ExtractedParam(name="x", value="1", context=ParamContext.QUERY_STRING, original_url="https://example.com/")
    try:
        p.name = "y"  # type: ignore[misc]
        assert pytest.fail("Should be frozen")
    except Exception:
        pass
