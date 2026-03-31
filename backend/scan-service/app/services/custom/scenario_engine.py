"""Moteur d'exécution de scénarios custom.

Format d'entrée (input_json.scenario) :
[
    {
        "step": "request",
        "method": "POST",
        "url": "https://target.com/api/transfer",
        "body": {"amount": -100},
        "headers": {"Content-Type": "application/json"},
        "expect": {"status": [200, 201], "body_contains": "success"}
    },
    {
        "step": "assert",
        "condition": "previous.status in [200, 201]",
        "finding": {
            "slug": "custom-business-logic",
            "severity": "high",
            "title": "Business logic bypass",
            "evidence": "Montant négatif accepté"
        }
    }
]
"""

from __future__ import annotations

import json
import logging
from contextlib import suppress
from typing import Any

from app.models.finding import Finding
from app.schemas.async_job import ScanCredentials
from app.services.intrusive.checks._finding_builder import make_finding
from app.services.intrusive.lib.http_client import IntrusiveHTTPClient

logger = logging.getLogger(__name__)


class ScenarioContext:
    """Contexte d'exécution d'un scénario : résultats des steps précédents."""

    def __init__(self) -> None:
        """Initialise l'historique de steps et le résultat du step précédent."""
        self.steps: list[dict[str, Any]] = []
        self.previous: dict[str, Any] = {}

    def record(self, step_result: dict[str, Any]) -> None:
        """Enregistre un résultat et le met à jour comme contexte « previous »."""
        self.steps.append(step_result)
        self.previous = step_result


async def _process_request_step(
    client: IntrusiveHTTPClient,
    ctx: ScenarioContext,
    step_def: dict[str, Any],
    base_url: str,
) -> None:
    result = await _execute_request_step(client, step_def, base_url)
    ctx.record(result)
    expect = step_def.get("expect") or {}
    expected_statuses = expect.get("status", [])
    body_contains = expect.get("body_contains", "")
    if expected_statuses and result["status"] not in expected_statuses:
        ctx.record({"status": result["status"], "matched_expect": False})
    if body_contains and body_contains not in result.get("body", ""):
        ctx.record({"body_contains_matched": False})


async def _process_assert_step(ctx: ScenarioContext, findings: list[Finding], step_def: dict[str, Any]) -> None:
    finding_def = step_def.get("finding")
    if not finding_def:
        return
    condition = step_def.get("condition", "")
    if not _evaluate_condition(condition, ctx):
        return
    findings.append(
        make_finding(
            slug=finding_def.get("slug", "custom-finding"),
            category="custom",
            title=finding_def.get("title", "Custom finding"),
            severity=finding_def.get("severity", "medium"),
            evidence=finding_def.get("evidence", f"Condition: {condition}"),
        )
    )


async def _process_wait_step(step_def: dict[str, Any]) -> None:
    import asyncio

    ms = int(step_def.get("ms", 500))
    await asyncio.sleep(min(ms, 5000) / 1000)


async def run_scenario(
    scenario: list[dict[str, Any]],
    credentials: ScanCredentials | None = None,
    base_url: str = "",
) -> list[Finding]:
    """Exécute un scénario custom step par step et retourne les findings.

    Args:
        scenario: Liste de steps (request, assert, wait).
        credentials: Credentials de l'application cible.
        base_url: URL de base pour résoudre les URLs relatives.
    """
    if not scenario:
        return []

    client = IntrusiveHTTPClient(credentials=credentials, timeout=10.0)
    ctx = ScenarioContext()
    findings: list[Finding] = []

    for step_def in scenario:
        step_type = step_def.get("step", "")
        try:
            if step_type == "request":
                await _process_request_step(client, ctx, step_def, base_url)
            elif step_type == "assert":
                await _process_assert_step(ctx, findings, step_def)
            elif step_type == "wait":
                await _process_wait_step(step_def)
        except Exception:
            logger.exception("scenario step failed: %s", step_def)

    return findings


async def _execute_request_step(
    client: IntrusiveHTTPClient,
    step: dict[str, Any],
    base_url: str,
) -> dict[str, Any]:
    """Exécute un step de type 'request' et retourne le résultat."""
    method = step.get("method", "GET").upper()
    url = step.get("url", "")
    if not url.startswith("http") and base_url:
        url = base_url.rstrip("/") + "/" + url.lstrip("/")

    headers = step.get("headers") or {}
    body_data = step.get("body")

    kwargs: dict[str, Any] = {"headers": headers}
    if body_data is not None:
        if isinstance(body_data, (dict, list)):
            kwargs["json"] = body_data
        else:
            kwargs["content"] = str(body_data)

    result = await client.request(method, url, **kwargs)
    return {
        "method": method,
        "url": url,
        "status": result.status_code,
        "body": result.body[:2000],
        "headers": result.headers,
        "elapsed_ms": result.elapsed_ms,
        "error": result.error,
    }


def _evaluate_condition(condition: str, ctx: ScenarioContext) -> bool:
    """Évalue une condition simple basée sur le contexte précédent.

    Conditions supportées :
    - "previous.status in [200, 201]"
    - "previous.status == 200"
    - "previous.body_contains_matched == False"
    - "always" (toujours vrai)
    - "never" (toujours faux)
    """
    if not condition or condition == "always":
        return True
    if condition == "never":
        return False

    prev = ctx.previous
    condition_lower = condition.lower().strip()
    prefix_in = "previous.status in "
    with suppress(Exception):
        if condition_lower.startswith(prefix_in):
            start = len(prefix_in)
            statuses_str = condition[start:].strip()
            statuses = json.loads(statuses_str.replace("(", "[").replace(")", "]"))
            return prev.get("status") in statuses
        if condition_lower.startswith("previous.status =="):
            target_status = int(condition.split("==")[1].strip())
            return prev.get("status") == target_status
        if "previous.body_contains_matched == false" in condition_lower:
            return not prev.get("body_contains_matched", True)

    return False
