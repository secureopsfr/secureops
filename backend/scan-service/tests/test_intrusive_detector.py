"""Tests unitaires — moteur de détection intrusif (app.services.intrusive.lib.detector)."""

from __future__ import annotations

import pytest

from app.services.intrusive.lib.detector import (
    DetectionResult,
    detect_deserialization_error,
    detect_nosql_error,
    detect_path_traversal,
    detect_reflection,
    detect_shell_output,
    detect_sql_error,
    detect_ssti_eval,
    detect_template_error,
    detect_time_based,
    detect_xxe,
    diff_baseline,
)

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _ok(result: DetectionResult) -> None:
    assert isinstance(result, DetectionResult)
    assert result.matched is True
    assert result.pattern is not None


def _nok(result: DetectionResult) -> None:
    assert isinstance(result, DetectionResult)
    assert result.matched is False


# ─── detect_sql_error ─────────────────────────────────────────────────────────


def test_detect_sql_error_mysql_syntax() -> None:
    """detect_sql_error détecte une erreur SQL MySQL."""
    _ok(detect_sql_error("You have an error in your SQL syntax near MySQL"))


def test_detect_sql_error_postgresql() -> None:
    """detect_sql_error détecte une erreur SQL PostgreSQL."""
    _ok(detect_sql_error("PostgreSQL ERROR: unterminated quoted string"))


def test_detect_sql_error_oracle() -> None:
    """detect_sql_error détecte une erreur SQL Oracle."""
    _ok(detect_sql_error("ORA-00933: SQL command not properly ended"))


def test_detect_sql_error_sqlite() -> None:
    """detect_sql_error détecte une erreur SQL SQLite."""
    _ok(detect_sql_error("sqlite3.OperationalError: near ';': syntax error"))


def test_detect_sql_error_mssql() -> None:
    """detect_sql_error détecte une erreur SQL Microsoft SQL Server."""
    _ok(detect_sql_error("Microsoft OLE DB Provider for SQL Server error '80040e14'"))


def test_detect_sql_error_near_syntax() -> None:
    """detect_sql_error détecte une erreur SQL près de la syntaxe."""
    _ok(detect_sql_error('near "drop": syntax error'))


def test_detect_sql_error_no_match() -> None:
    """detect_sql_error ne détecte pas une page sans erreur SQL."""
    _nok(detect_sql_error("Normal page content without database errors"))


def test_detect_sql_error_empty_body() -> None:
    """detect_sql_error ne détecte pas une page vide."""
    _nok(detect_sql_error(""))


def test_detect_sql_error_returns_evidence() -> None:
    """detect_sql_error retourne une preuve de la détection."""
    result = detect_sql_error("prefix PostgreSQL ERROR suffix")
    assert result.matched
    assert result.evidence is not None
    assert len(result.evidence) > 0


def test_detect_sql_error_detection_type() -> None:
    """detect_sql_error retourne le type de détection sql_error."""
    result = detect_sql_error("PostgreSQL ERROR here")
    assert result.detection_type == "sql_error"


# ─── detect_nosql_error ───────────────────────────────────────────────────────


def test_detect_nosql_error_mongo() -> None:
    """detect_nosql_error détecte une erreur NoSQL Mongo."""
    _ok(detect_nosql_error("MongoError: Cast to ObjectId failed"))


def test_detect_nosql_error_where() -> None:
    """detect_nosql_error détecte une erreur NoSQL $where."""
    _ok(detect_nosql_error('{"$where": "1==1"}'))


def test_detect_nosql_error_duplicate_key() -> None:
    """detect_nosql_error détecte une erreur NoSQL duplicate key."""
    _ok(detect_nosql_error("E11000 duplicate key error collection"))


def test_detect_nosql_error_bsontype() -> None:
    """detect_nosql_error détecte une erreur NoSQL BSONTypeError."""
    _ok(detect_nosql_error("BSONTypeError: argument must be a buffer"))


def test_detect_nosql_error_no_match() -> None:
    """detect_nosql_error ne détecte pas une réponse JSON normale."""
    _nok(detect_nosql_error('Regular JSON response: {"key": "value"}'))


def test_detect_nosql_error_detection_type() -> None:
    """detect_nosql_error retourne le type de détection nosql_error."""
    result = detect_nosql_error("MongoError: something")
    assert result.detection_type == "nosql_error"


# ─── detect_template_error ────────────────────────────────────────────────────


def test_detect_template_error_jinja2() -> None:
    """detect_template_error détecte une erreur Jinja2."""
    _ok(detect_template_error("jinja2.exceptions.TemplateSyntaxError"))


def test_detect_template_error_twig() -> None:
    """detect_template_error détecte une erreur Twig."""
    _ok(detect_template_error("Twig_Error_Syntax: unexpected token"))


def test_detect_template_error_undefined() -> None:
    """detect_template_error détecte une erreur UndefinedError."""
    _ok(detect_template_error("UndefinedError: 'config' is undefined"))


def test_detect_template_error_no_match() -> None:
    """detect_template_error ne détecte pas une page sans erreur de template."""
    _nok(detect_template_error("Page rendered successfully"))


def test_detect_template_error_detection_type() -> None:
    """detect_template_error retourne le type de détection template_error."""
    result = detect_template_error("jinja2.exceptions.TemplateSyntaxError: foo")
    assert result.detection_type == "template_error"


# ─── detect_xxe ───────────────────────────────────────────────────────────────


def test_detect_xxe_etc_passwd() -> None:
    """detect_xxe détecte une erreur /etc/passwd."""
    _ok(detect_xxe("root:x:0:0:/root:/bin/bash"))


def test_detect_xxe_win_ini() -> None:
    """detect_xxe détecte une erreur win.ini."""
    _ok(detect_xxe("[boot loader]\ntimeout=30"))


def test_detect_xxe_for_16bit() -> None:
    """detect_xxe détecte une erreur for 16-bit app support."""
    _ok(detect_xxe("; for 16-bit app support"))


def test_detect_xxe_no_match() -> None:
    """detect_xxe ne détecte pas une réponse normale."""
    _nok(detect_xxe("<response>OK</response>"))


def test_detect_xxe_detection_type() -> None:
    """detect_xxe retourne le type de détection xxe."""
    result = detect_xxe("root:x:0:0:")
    assert result.detection_type == "xxe"


# ─── detect_path_traversal ────────────────────────────────────────────────────


def test_detect_path_traversal_passwd() -> None:
    """detect_path_traversal détecte une erreur /etc/passwd."""
    _ok(detect_path_traversal("root:x:0:0:/root:/bin/bash\ndaemon:x:1:1"))


def test_detect_path_traversal_bin_bash() -> None:
    """detect_path_traversal détecte une erreur /bin/bash."""
    _ok(detect_path_traversal("some output with /bin/bash in it"))


def test_detect_path_traversal_win_ini() -> None:
    """detect_path_traversal détecte une erreur win.ini."""
    _ok(detect_path_traversal("[boot loader]\ntimeout=30"))


def test_detect_path_traversal_no_match() -> None:
    """detect_path_traversal ne détecte pas une page sans erreur de path traversal."""
    _nok(detect_path_traversal("File not found"))


def test_detect_path_traversal_detection_type() -> None:
    """detect_path_traversal retourne le type de détection path_traversal."""
    result = detect_path_traversal("/bin/bash present in output")
    assert result.detection_type == "path_traversal"


# ─── detect_shell_output ──────────────────────────────────────────────────────


def test_detect_shell_output_uid() -> None:
    """detect_shell_output détecte une erreur uid."""
    _ok(detect_shell_output("uid=1000(user) gid=1000(user) groups=1000(user)"))


def test_detect_shell_output_gid() -> None:
    """detect_shell_output détecte une erreur gid."""
    _ok(detect_shell_output("gid=0(root)"))


def test_detect_shell_output_no_match() -> None:
    """detect_shell_output ne détecte pas une page sans erreur de shell output."""
    _nok(detect_shell_output("Hello World"))


def test_detect_shell_output_detection_type() -> None:
    """detect_shell_output retourne le type de détection shell_output."""
    result = detect_shell_output("uid=0(root)")
    assert result.detection_type == "shell_output"


# ─── detect_deserialization_error ─────────────────────────────────────────────


def test_detect_deserialization_java_exception() -> None:
    """detect_deserialization_error détecte une erreur java.io.InvalidClassException."""
    _ok(detect_deserialization_error("java.io.InvalidClassException: stream classdesc serialVersionUID"))


def test_detect_deserialization_php() -> None:
    """detect_deserialization_error détecte une erreur PHP Notice: unserialize() error."""
    _ok(detect_deserialization_error("PHP Notice: unserialize() error"))


def test_detect_deserialization_class_not_found() -> None:
    """detect_deserialization_error détecte une erreur ClassNotFoundException."""
    _ok(detect_deserialization_error("ClassNotFoundException: com.example.Payload"))


def test_detect_deserialization_no_match() -> None:
    """detect_deserialization_error ne détecte pas une réponse JSON normale."""
    _nok(detect_deserialization_error("{}"))


def test_detect_deserialization_detection_type() -> None:
    """detect_deserialization_error retourne le type de détection deserialization_error."""
    result = detect_deserialization_error("java.io.IOException: blah")
    assert result.detection_type == "deserialization_error"


# ─── detect_reflection ────────────────────────────────────────────────────────


def test_detect_reflection_present() -> None:
    """detect_reflection détecte une présence de marker."""
    assert detect_reflection("Hello sec0p5-abc123 World", "sec0p5-abc123") is True


def test_detect_reflection_absent() -> None:
    """detect_reflection ne détecte pas une absence de marker."""
    assert detect_reflection("Hello World", "sec0p5-abc123") is False


def test_detect_reflection_empty_marker() -> None:
    """detect_reflection ne détecte pas une absence de marker."""
    assert detect_reflection("Hello World", "") is False


def test_detect_reflection_empty_body() -> None:
    """detect_reflection ne détecte pas une absence de marker."""
    assert detect_reflection("", "marker") is False


def test_detect_reflection_case_sensitive() -> None:
    """detect_reflection ne détecte pas une absence de marker."""
    assert detect_reflection("SEC0P5-ABC123", "sec0p5-abc123") is False


# ─── detect_ssti_eval ─────────────────────────────────────────────────────────


def test_detect_ssti_eval_positive() -> None:
    """detect_ssti_eval détecte une évaluation SSTI positive."""
    assert detect_ssti_eval("Result is 49 here") is True


def test_detect_ssti_eval_in_context() -> None:
    """detect_ssti_eval détecte une évaluation SSTI positive."""
    assert detect_ssti_eval("<p>49</p>") is True


def test_detect_ssti_eval_false_on_longer_number() -> None:
    """detect_ssti_eval ne détecte pas une évaluation SSTI positive."""
    assert detect_ssti_eval("497") is False
    assert detect_ssti_eval("149") is False


def test_detect_ssti_eval_not_present() -> None:
    """detect_ssti_eval ne détecte pas une évaluation SSTI positive."""
    assert detect_ssti_eval("Result is 50") is False


def test_detect_ssti_eval_empty() -> None:
    """detect_ssti_eval ne détecte pas une évaluation SSTI positive."""
    assert detect_ssti_eval("") is False


# ─── diff_baseline ────────────────────────────────────────────────────────────


def test_diff_baseline_identical() -> None:
    """diff_baseline retourne 0.0 pour deux réponses identiques."""
    assert diff_baseline("hello\nworld", "hello\nworld") == 0.0


def test_diff_baseline_completely_different() -> None:
    """diff_baseline retourne 1.0 pour deux réponses complètement différentes."""
    result = diff_baseline("aaa", "bbb")
    assert result == 1.0


def test_diff_baseline_partial() -> None:
    """diff_baseline retourne une valeur entre 0.0 et 1.0 pour deux réponses partiellement différentes."""
    result = diff_baseline("a\nb\nc", "a\nb\nd")
    assert 0.0 < result < 1.0


def test_diff_baseline_both_empty() -> None:
    """diff_baseline retourne 0.0 pour deux réponses vides."""
    assert diff_baseline("", "") == 0.0


def test_diff_baseline_one_empty() -> None:
    """diff_baseline retourne 1.0 pour une réponse vide et une réponse non vide."""
    assert diff_baseline("", "something") == 1.0
    assert diff_baseline("something", "") == 1.0


def test_diff_baseline_returns_float() -> None:
    """diff_baseline retourne un float."""
    result = diff_baseline("a\nb", "a\nc")
    assert isinstance(result, float)


# ─── detect_time_based (async) ────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_detect_time_based_positive() -> None:
    """detect_time_based détecte une réponse lente."""
    call_count = 0

    async def fast_delayed_probe() -> float:
        nonlocal call_count
        call_count += 1
        return 1200.0  # > 900ms threshold

    result = await detect_time_based(fast_delayed_probe, threshold_ms=900.0, confirmations=2)
    assert result.matched is True
    assert result.detection_type == "timing"
    assert call_count >= 2


@pytest.mark.asyncio()
async def test_detect_time_based_negative() -> None:
    """detect_time_based ne détecte pas une réponse rapide."""

    async def fast_probe() -> float:
        return 100.0  # < 900ms threshold

    result = await detect_time_based(fast_probe, threshold_ms=900.0, confirmations=2)
    assert result.matched is False


@pytest.mark.asyncio()
async def test_detect_time_based_reset_on_slow() -> None:
    """Un probe rapide entre deux lents reset le compteur."""
    calls: list[float] = [1200.0, 100.0, 1200.0]
    idx = 0

    async def alternating_probe() -> float:
        nonlocal idx
        val = calls[idx % len(calls)]
        idx += 1
        return val

    result = await detect_time_based(alternating_probe, threshold_ms=900.0, confirmations=2)
    assert result.matched is False


@pytest.mark.asyncio()
async def test_detect_time_based_exception_handled() -> None:
    """probe_fn qui lève une exception → pas de crash, matched=False."""

    async def failing_probe() -> float:
        raise OSError("network error")

    result = await detect_time_based(failing_probe, threshold_ms=900.0, confirmations=2)
    assert result.matched is False
