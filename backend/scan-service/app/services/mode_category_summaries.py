"""Category summaries dedicated to non-passive scan modes."""

from __future__ import annotations

from app.models.finding import Finding


def _entry(
    *,
    category: str,
    label_fr: str,
    label_en: str,
    description_fr: str,
    description_en: str,
    checks_fr: list[str],
    checks_en: list[str],
    anomaly_count: int,
    checks_count: int,
) -> dict:
    return {
        "category": category,
        "label_fr": label_fr,
        "label_en": label_en,
        "description_fr": description_fr,
        "description_en": description_en,
        "checks_fr": checks_fr,
        "checks_en": checks_en,
        "anomaly_count": anomaly_count,
        "checks_count": checks_count,
    }


def _count_by_category(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.category] = counts.get(finding.category, 0) + 1
    return counts


def build_intrusive_category_summaries(findings: list[Finding]) -> list[dict]:
    """Build summaries for intrusive fake probes."""
    by_cat = _count_by_category(findings)
    return [
        _entry(
            category="intrusive_reflected_xss",
            label_fr="Injection XSS reflechie",
            label_en="Reflected XSS Injection",
            description_fr=(
                "Le scan envoie des charges de test controlees pour detecter une " "reflexion de contenu potentiellement executable dans la reponse."
            ),
            description_en="The scan sends controlled test payloads to detect reflected content that could become executable in responses.",
            checks_fr=["Injection de payload de reflection XSS"],
            checks_en=["Reflected XSS payload probe"],
            anomaly_count=by_cat.get("intrusive_reflected_xss", 0),
            checks_count=1,
        ),
        _entry(
            category="intrusive_sql_injection",
            label_fr="Injection SQL",
            label_en="SQL Injection",
            description_fr=(
                "Le scan teste des meta-caracteres SQL pour identifier des " "variations de comportement (erreurs, timing, reponses anormales)."
            ),
            description_en="The scan tests SQL metacharacters to identify behavior changes (errors, timing shifts, abnormal responses).",
            checks_fr=["Probe SQLi sur points d'entree detectes"],
            checks_en=["SQLi probe on discovered input points"],
            anomaly_count=by_cat.get("intrusive_sql_injection", 0),
            checks_count=1,
        ),
        _entry(
            category="intrusive_authz_bypass",
            label_fr="Contournement d'autorisation",
            label_en="Authorization Bypass",
            description_fr="Le scan emet des variantes de requetes sur chemins sensibles pour detecter des acces inattendus sans droits requis.",
            description_en="The scan sends request variants on sensitive paths to detect unexpected access without required permissions.",
            checks_fr=["Probe de contournement d'autorisation"],
            checks_en=["Authorization bypass probe"],
            anomaly_count=by_cat.get("intrusive_authz_bypass", 0),
            checks_count=1,
        ),
    ]


def build_custom_category_summaries(findings: list[Finding] | None = None) -> list[dict]:
    """Build summaries for custom fake mode."""
    by_cat = _count_by_category(findings or [])
    return [
        _entry(
            category="custom_strategy",
            label_fr="Strategie personnalisee",
            label_en="Custom Strategy",
            description_fr="Ce mode est reserve aux scenarios sur mesure definis par l'equipe. En V1, aucun test actif n'est execute.",
            description_en="This mode is reserved for team-defined bespoke scenarios. In V1, no active test is executed.",
            checks_fr=["Simulation de strategie custom"],
            checks_en=["Custom strategy simulation probe"],
            anomaly_count=by_cat.get("custom_strategy", 0),
            checks_count=1,
        ),
        _entry(
            category="custom_guardrails",
            label_fr="Garde-fous d'execution",
            label_en="Execution Guardrails",
            description_fr="Verification des garde-fous de securite avant lancement des scripts custom (mode simulation en V1).",
            description_en="Validation of safety guardrails before running custom scripts (simulation mode in V1).",
            checks_fr=["Simulation des garde-fous custom"],
            checks_en=["Custom guardrails simulation probe"],
            anomaly_count=by_cat.get("custom_guardrails", 0),
            checks_count=1,
        ),
    ]


def build_destructive_category_summaries(findings: list[Finding] | None = None) -> list[dict]:
    """Build summaries for destructive fake mode."""
    by_cat = _count_by_category(findings or [])
    return [
        _entry(
            category="destructive_prechecks",
            label_fr="Pre-checks destructifs",
            label_en="Destructive Pre-checks",
            description_fr=(
                "Le mode destructif valide les prerequis et fenetres d'execution " "avant toute action sensible. En V1, execution simulee."
            ),
            description_en=(
                "Destructive mode validates prerequisites and execution windows " "before any sensitive action. In V1, execution is simulated."
            ),
            checks_fr=["Simulation des pre-checks destructifs"],
            checks_en=["Destructive prechecks simulation probe"],
            anomaly_count=by_cat.get("destructive_prechecks", 0),
            checks_count=1,
        ),
        _entry(
            category="destructive_safety",
            label_fr="Controle de surete",
            label_en="Safety Controls",
            description_fr="Verification des mecanismes d'arret d'urgence et des limites de blast radius (mode simulation en V1).",
            description_en="Verification of emergency stop and blast-radius limits (simulation mode in V1).",
            checks_fr=["Simulation des controles de surete"],
            checks_en=["Safety controls simulation probe"],
            anomaly_count=by_cat.get("destructive_safety", 0),
            checks_count=1,
        ),
    ]


def count_total_tests(category_summaries: list[dict]) -> int:
    """Compute total tests count from mode-specific category summaries."""
    return sum(int(entry.get("checks_count", 0)) for entry in category_summaries)
