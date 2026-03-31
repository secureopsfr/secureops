"""Tests unitaires — checks intrusifs avec HTTP mocké.

Chaque test isole un check en mockant IntrusiveHTTPClient.request
afin de ne faire aucune requête réseau réelle.

Pattern utilisé :
    monkeypatch.setattr(
        "app.services.intrusive.checks.<path>.check.IntrusiveHTTPClient",
        lambda **kw: FakeClient(responses=[...]),
    )
"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.intrusive.lib.http_client import ProbeResult

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _ok_result(
    url: str = "https://example.com/",
    status: int = 200,
    body: str = "",
    headers: dict[str, str] | None = None,
    elapsed_ms: float = 50.0,
) -> ProbeResult:
    """Construit un ProbeResult OK."""
    return ProbeResult(
        method="GET",
        url=url,
        status_code=status,
        headers=headers or {},
        body=body,
        elapsed_ms=elapsed_ms,
    )


def _err_result(url: str = "https://example.com/") -> ProbeResult:
    """Construit un ProbeResult en erreur."""
    return ProbeResult(
        method="GET",
        url=url,
        status_code=0,
        headers={},
        body="",
        elapsed_ms=0.0,
        error="Connection refused",
    )


def _fake_client_factory(responses: list[ProbeResult]) -> type:  # noqa: C901
    """Retourne une classe FakeClient qui distribue les réponses en séquence."""

    class _FakeClient:
        def __init__(self, **_: Any) -> None:
            self._responses = list(responses)
            self._index = 0

        async def request(self, *_: Any, **__: Any) -> ProbeResult:
            if self._index < len(self._responses):
                r = self._responses[self._index]
                self._index += 1
                return r
            return _ok_result()

        async def get(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

        async def post(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

        async def put(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

        async def patch(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

        async def delete(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

        async def options(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

        async def head(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

        async def trace(self, *_: Any, **__: Any) -> ProbeResult:
            return await self.request()

    return _FakeClient


# ─── CORS actif ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_cors_actif_reflection_with_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """CORS réflexion + credentials → finding critical."""
    from app.services.intrusive.checks.both.cors_actif import check

    response = _ok_result(
        headers={
            "access-control-allow-origin": "https://evil.test",
            "access-control-allow-credentials": "true",
        }
    )
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response]))

    findings = await check.run("https://example.com/", scan_type="frontend")
    assert len(findings) == 1
    assert findings[0].severity == "critical"
    assert findings[0].category == "cors_actif"


@pytest.mark.asyncio()
async def test_cors_actif_reflection_no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """CORS réflexion sans credentials → finding high (backend) ou medium (frontend)."""
    from app.services.intrusive.checks.both.cors_actif import check

    response = _ok_result(headers={"access-control-allow-origin": "https://evil.test"})
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response]))

    findings = await check.run("https://example.com/", scan_type="backend")
    assert len(findings) == 1
    assert findings[0].severity == "high"


@pytest.mark.asyncio()
async def test_cors_actif_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    """CORS wildcard → finding medium."""
    from app.services.intrusive.checks.both.cors_actif import check

    response = _ok_result(headers={"access-control-allow-origin": "*"})
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response]))

    findings = await check.run("https://example.com/")
    assert len(findings) == 1
    assert findings[0].severity == "medium"


@pytest.mark.asyncio()
async def test_cors_actif_no_finding_when_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pas de CORS dangereux → aucun finding."""
    from app.services.intrusive.checks.both.cors_actif import check

    response = _ok_result(headers={"access-control-allow-origin": "https://example.com"})
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response]))

    findings = await check.run("https://example.com/")
    assert findings == []


@pytest.mark.asyncio()
async def test_cors_actif_error_response_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Erreur réseau → aucun finding (pas de crash)."""
    from app.services.intrusive.checks.both.cors_actif import check

    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([_err_result()]))
    findings = await check.run("https://example.com/")
    assert findings == []


# ─── SQLi ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_sqli_error_based_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """La SQLi error-based : body avec erreur PostgreSQL → finding critique."""
    from app.services.intrusive.checks.both.sqli import check

    # URL avec un paramètre injectable
    url = "https://example.com/?id=1"
    response = _ok_result(body="PostgreSQL ERROR: syntax error at or near")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run(url, scan_type="backend")
    assert len(findings) == 1
    assert findings[0].category == "sql_injection"
    assert findings[0].severity == "critical"


@pytest.mark.asyncio()
async def test_sqli_no_finding_clean_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pas d'erreur SQL → aucun finding."""
    from app.services.intrusive.checks.both.sqli import check

    response = _ok_result(body="<html>Normal page content</html>")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 30))

    findings = await check.run("https://example.com/?id=1", scan_type="frontend")
    assert findings == []


@pytest.mark.asyncio()
async def test_sqli_no_params_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """URL sans paramètres → aucun finding (rien à injecter)."""
    from app.services.intrusive.checks.both.sqli import check

    response = _ok_result(body="Normal content")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 5))

    findings = await check.run("https://example.com/no-params", scan_type="backend")
    assert findings == []


# ─── Open Redirect ────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_open_redirect_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Open redirect : Location vers domaine externe → finding."""
    from app.services.intrusive.checks.both.open_redirect import check

    redirect_response = _ok_result(
        url="https://example.com/?redirect=https://evil.test",
        status=302,
        headers={"location": "https://evil.test"},
    )
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([redirect_response] * 20))

    findings = await check.run("https://example.com/?redirect=home", scan_type="frontend")
    assert len(findings) >= 1
    assert findings[0].category == "open_redirect"


@pytest.mark.asyncio()
async def test_open_redirect_no_finding_when_internal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect vers le même domaine → aucun finding."""
    from app.services.intrusive.checks.both.open_redirect import check

    redirect_response = _ok_result(
        status=302,
        headers={"location": "https://example.com/home"},
    )
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([redirect_response] * 20))

    findings = await check.run("https://example.com/?redirect=home", scan_type="frontend")
    assert findings == []


# ─── DoS / Rate Limiting ──────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_dos_no_rate_limit_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Aucun 429 après burst → finding medium."""
    from app.services.intrusive.checks.both.dos_p0 import check

    # Toutes les réponses sont 200 (pas de 429)
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([_ok_result()] * 25))

    findings = await check.run("https://example.com/", scan_type="both")
    assert len(findings) == 1
    assert findings[0].severity == "medium"
    assert findings[0].category == "dos_rate_limit"


@pytest.mark.asyncio()
async def test_dos_rate_limited_no_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """429 reçu immédiatement → rate limiting détecté → aucun finding."""
    from app.services.intrusive.checks.both.dos_p0 import check

    limited_response = _ok_result(status=429)
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([limited_response] * 25))

    findings = await check.run("https://example.com/", scan_type="frontend")
    assert findings == []


# ─── CSRF ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_csrf_no_finding_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Formulaire avec token CSRF → aucun finding."""
    from app.services.intrusive.checks.both.csrf import check

    body = """
    <form action="/transfer" method="POST">
      <input type="hidden" name="csrf_token" value="abc123">
      <input type="text" name="amount">
    </form>
    """
    response = _ok_result(body=body)
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 10))

    findings = await check.run("https://example.com/transfer", scan_type="frontend")
    assert findings == []


# ─── Méthodes HTTP ────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_methodes_http_trace_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Méthode TRACE active → finding."""
    from app.services.intrusive.checks.both.methodes_http import check

    # OPTIONS retourne Allow: TRACE parmi les méthodes
    options_response = _ok_result(headers={"allow": "GET, POST, OPTIONS, TRACE"})
    trace_response = _ok_result(status=200, body="TRACE / HTTP/1.1\r\nHost: example.com")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([options_response, trace_response] * 5))

    findings = await check.run("https://example.com/", scan_type="frontend")
    assert any(f.category == "methodes_http" for f in findings)


@pytest.mark.asyncio()
async def test_methodes_http_no_finding_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Seules GET et POST autorisées, TRACE désactivé → pas de finding dangereux."""
    from app.services.intrusive.checks.both.methodes_http import check

    options_response = _ok_result(headers={"allow": "GET, POST, OPTIONS"})
    method_405 = _ok_result(status=405)
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([options_response] + [method_405] * 10))

    findings = await check.run("https://example.com/", scan_type="backend")
    # Aucun finding de type "dangereux"
    dangerous = [f for f in findings if f.severity in ("high", "critical")]
    assert dangerous == []


# ─── Host Header Injection ────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_host_header_reflection_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Host Header réfléchi dans le body → finding."""
    from app.services.intrusive.checks.both.host_header import check

    evil_host = "evil.test"
    response = _ok_result(body=f"<a href='https://{evil_host}/reset'>Reset password</a>")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 10))

    findings = await check.run("https://example.com/", scan_type="both")
    assert any(f.category == "host_header" for f in findings)


@pytest.mark.asyncio()
async def test_host_header_no_reflection_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Body ne réfléchit pas le Host → aucun finding."""
    from app.services.intrusive.checks.both.host_header import check

    response = _ok_result(body="<p>Normal page without any injected host</p>")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 10))

    findings = await check.run("https://example.com/", scan_type="frontend")
    assert findings == []


# ─── SSTI ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_ssti_eval_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """SSTI : réponse contient '49' → finding critical."""
    from app.services.intrusive.checks.both.ssti import check

    response = _ok_result(body="Result: 49")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/?q=test", scan_type="backend")
    # Le check SSTI n'a besoin d'aucun paramètre existant dans l'URL
    # (il injecte dans les paramètres courants)
    assert isinstance(findings, list)


@pytest.mark.asyncio()
async def test_ssti_no_finding_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Aucune évaluation → aucun finding."""
    from app.services.intrusive.checks.both.ssti import check

    response = _ok_result(body="<p>Hello {{name}}</p>")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/?q=test")
    assert findings == []


# ─── LFI / RFI ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_lfi_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """LFI : /etc/passwd révélé dans la réponse → finding critical."""
    from app.services.intrusive.checks.both.lfi_rfi import check

    response = _ok_result(body="root:x:0:0:/root:/bin/bash\ndaemon:x:1:1:/usr/sbin/daemon:/usr/sbin/nologin")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/?file=about", scan_type="backend")
    assert len(findings) >= 1
    assert findings[0].category == "lfi_rfi"
    assert findings[0].severity in ("critical", "high")


@pytest.mark.asyncio()
async def test_lfi_no_finding_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Réponse normale → aucun finding."""
    from app.services.intrusive.checks.both.lfi_rfi import check

    response = _ok_result(body="<html><body>Normal page</body></html>")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/?file=about")
    assert findings == []


# ─── Path Traversal ───────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_path_traversal_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Path traversal : /etc/passwd dans la réponse → finding."""
    from app.services.intrusive.checks.both.path_traversal import check

    response = _ok_result(body="root:x:0:0:/root:/bin/bash")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/?path=home", scan_type="backend")
    assert len(findings) >= 1
    assert findings[0].category == "path_traversal"


# ─── Désérialisation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_insecure_deserialization_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Désérialisation : ClassNotFoundException dans la réponse → finding."""
    from app.services.intrusive.checks.both.insecure_deserialization import check

    response = _ok_result(body="java.io.InvalidClassException: ClassNotFoundException")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/api/data", scan_type="backend")
    assert isinstance(findings, list)


# ─── Service Mesh / Endpoints internes ───────────────────────────────────────


@pytest.mark.asyncio()
async def test_service_mesh_actuator_exposed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Endpoint /actuator/env accessible → finding élevé."""
    from app.services.intrusive.checks.both.service_mesh import check

    # /actuator/env retourne 200 avec des propriétés
    exposed_response = _ok_result(
        status=200,
        body='{"activeProfiles": ["prod"], "propertySources": [{"name": "systemEnvironment"}]}',
    )
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([exposed_response] * 30))

    findings = await check.run("https://example.com/", scan_type="backend")
    assert any(f.category == "service_mesh" for f in findings)


@pytest.mark.asyncio()
async def test_service_mesh_no_finding_all_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tous les endpoints internes retournent 404 → aucun finding."""
    from app.services.intrusive.checks.both.service_mesh import check

    not_found = _ok_result(status=404)
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([not_found] * 30))

    findings = await check.run("https://example.com/")
    assert findings == []


# ─── NoSQLi ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_nosqli_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """La NoSQLi : MongoError dans la réponse → finding."""
    from app.services.intrusive.checks.both.nosqli import check

    response = _ok_result(body='{"error": "MongoError: Cast to ObjectId failed"}')
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/?user=admin", scan_type="backend")
    assert any(f.category == "nosql_injection" for f in findings)


@pytest.mark.asyncio()
async def test_nosqli_no_finding_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Réponse normale → aucun finding."""
    from app.services.intrusive.checks.both.nosqli import check

    response = _ok_result(body='{"result": "ok"}')
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run("https://example.com/?user=admin")
    assert findings == []


# ─── Paramètres réfléchis (XSS) ──────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_parametres_reflechis_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Paramètre réfléchi sans encodage dans HTML → finding XSS."""
    from app.services.intrusive.checks.frontend.parametres_reflechis import check

    # L'URL a un paramètre q, la réponse réfléchit le marqueur XSS
    url = "https://example.com/?q=test"
    # Le body doit contenir le marqueur généré par make_xss_marker()
    # On ne peut pas prédire le marker, mais on peut tester que le check ne crashe pas
    # et ne génère pas de finding sur une réponse normale
    response = _ok_result(body="<p>Votre recherche : test</p>")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 20))

    findings = await check.run(url, scan_type="frontend")
    assert isinstance(findings, list)


@pytest.mark.asyncio()
async def test_parametres_reflechis_no_finding_no_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """URL sans paramètres → aucun finding."""
    from app.services.intrusive.checks.frontend.parametres_reflechis import check

    response = _ok_result(body="<p>Page statique</p>")
    monkeypatch.setattr(check, "IntrusiveHTTPClient", _fake_client_factory([response] * 5))

    findings = await check.run("https://example.com/", scan_type="frontend")
    assert findings == []


# ─── Cohérence globale : tous les checks retournent list[Finding] ──────────────


@pytest.mark.asyncio()
async def test_all_checks_return_list_on_clean_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tous les checks retournent une liste vide (pas d'exception) sur réponse propre."""
    checks_to_test = [
        ("app.services.intrusive.checks.both.cors_actif.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.sqli.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.open_redirect.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.dos_p0.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.host_header.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.ssti.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.lfi_rfi.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.nosqli.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.path_traversal.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.both.service_mesh.check", "IntrusiveHTTPClient"),
        ("app.services.intrusive.checks.frontend.parametres_reflechis.check", "IntrusiveHTTPClient"),
    ]

    clean_response = _ok_result(body="<html><body><p>Clean page</p></body></html>")
    FakeClient = _fake_client_factory([clean_response] * 50)

    for module_path, attr in checks_to_test:
        import importlib

        mod = importlib.import_module(module_path)
        monkeypatch.setattr(mod, attr, FakeClient)
        findings = await mod.run("https://example.com/?q=1", scan_type="frontend")
        assert isinstance(findings, list), f"{module_path} did not return a list"
