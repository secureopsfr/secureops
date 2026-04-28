"""Section Synthèse du rapport PDF."""

from html import escape
from urllib.parse import urlparse

from app.catalogue.category_summaries import get_checks_count
from app.config.pdf import INTRUSIVE_CATEGORY_MAPPING, get_category_config, get_category_labels
from app.schemas.finding import Finding
from app.services.pdf_report.pdf_i18n import t


def _format_url_display(value: str) -> str:
    """Formate une URL pour un affichage compact dans le tableau."""
    try:
        parsed = urlparse(value)
        host = parsed.netloc
        path = parsed.path or ""
        return f"{host}{path}".strip("/") or host or value
    except Exception:
        return value


def _prevent_break_after_slash(value: str) -> str:
    """Empêche le retour à la ligne juste après '/'.

    Utilise un word-joiner Unicode après chaque slash pour garder
    le segment suivant sur la même ligne (ex: '/actualites').
    """
    return value.replace("/", "/\u2060")


def _build_single_summary_rows(
    by_category: dict[str, list[Finding]],
    info_by_category: dict[str, list[Finding]],
    checked_cats: list[str],
    category_labels: dict[str, str],
    status_ok: str,
    anomalies_one: str,
    anomalies_word: str,
    infos_one: str,
    infos_word: str,
) -> list[str]:
    """Construit les lignes du tableau synthèse en mode single."""
    rows: list[str] = []
    for cat in checked_cats:
        anomaly_count = len(by_category.get(cat, []))
        info_count = len(info_by_category.get(cat, []))
        checks_count = get_checks_count(cat)
        label = category_labels.get(cat, cat)
        if anomaly_count == 0 and info_count == 0:
            status_html = f'<a href="#other-{cat}" class="status-ok status-link">{status_ok}</a>'
        else:
            status_parts = []
            if anomaly_count:
                word = anomalies_one if anomaly_count == 1 else anomalies_word
                status_parts.append(f'<span class="status-warning">{anomaly_count} {word}</span>')
            if info_count:
                word = infos_one if info_count == 1 else infos_word
                status_parts.append(f'<span class="status-info">{info_count} {word}</span>')
            status_html = f'<a href="#sect-{cat}" class="status-link status-mixed">{" · ".join(status_parts)}</a>'
        rows.append("<tr>" f"<td>{escape(label)}</td>" f"<td class='tbl-num'>{checks_count}</td>" f"<td>{status_html}</td>" "</tr>")
    return rows


def _build_multi_compare_rows(
    multi_pages: list[dict],
    checked_cats: list[str],
    category_labels: dict[str, str],
    score_row_label: str,
    scan_mode: str = "passive",
) -> list[str]:
    """Construit les lignes du tableau de comparaison multi-pages."""
    rows = [_build_multi_score_row(multi_pages, score_row_label)]
    anomaly_counts_by_page = [_count_page_anomalies_by_category(page, scan_mode) for page in multi_pages]
    info_counts_by_page = [_count_page_infos_by_category(page, scan_mode) for page in multi_pages]

    for cat in checked_cats:
        label = category_labels.get(cat, cat)
        cat_cells: list[str] = []
        for page, anomaly_counts, info_counts in zip(multi_pages, anomaly_counts_by_page, info_counts_by_page, strict=False):
            counts = _resolve_multi_counts(page, cat, anomaly_counts, info_counts)
            cat_cells.append(_build_multi_category_cell(counts))
        if any(cell != "<td>—</td>" for cell in cat_cells):
            rows.append("<tr>" f"<td>{escape(label)}</td>" f"{''.join(cat_cells)}" "</tr>")

    return rows


def _score_chip_class(score: int) -> str:
    if score >= 80:
        return "score-chip score-chip-good"
    if score >= 50:
        return "score-chip score-chip-medium"
    return "score-chip score-chip-low"


def _build_multi_score_row(multi_pages: list[dict], score_row_label: str) -> str:
    """Construit la ligne des scores du tableau multi-pages."""
    score_cells = "".join(
        "<td class='tbl-num'>" f"<span class='{_score_chip_class(int(page.get('score', 0)))}'>{int(page.get('score', 0))}/100</span>" "</td>"
        for page in multi_pages
    )
    return "<tr>" f"<td>{escape(score_row_label)}</td>" f"{score_cells}" "</tr>"


def _summary_map_for_page(page: dict) -> dict[str, dict]:
    summaries = page.get("category_summaries")
    if not isinstance(summaries, list):
        return {}
    return {str(s.get("category", "")): s for s in summaries if isinstance(s, dict)}


def _resolve_multi_counts(page: dict, cat: str, anomaly_counts: dict[str, int], info_counts: dict[str, int]) -> tuple[int, int] | None:
    """Retourne (anomalies, infos) pour une catégorie, ou None si non applicable."""
    if cat in anomaly_counts:
        return anomaly_counts[cat], info_counts.get(cat, 0)
    if cat in info_counts:
        return 0, info_counts[cat]
    if isinstance(page.get("findings"), list):
        return 0, 0

    summary = _summary_map_for_page(page).get(cat)
    if isinstance(summary, dict):
        return int(summary.get("anomaly_count", 0) or 0), 0
    return None


def _build_multi_category_cell(counts: tuple[int, int] | None) -> str:
    if counts is None:
        return "<td>—</td>"
    anomaly_count, info_count = counts
    if anomaly_count == 0 and info_count == 0:
        return "<td><span class='status-ok'>✓</span></td>"
    chips = []
    if anomaly_count:
        chips.append(f"<span class='anomaly-chip'>{anomaly_count}</span>")
    if info_count:
        chips.append(f"<span class='info-chip'>{info_count}</span>")
    return "<td>" f"{''.join(chips)}" "</td>"


def _count_page_anomalies_by_category(page: dict, scan_mode: str) -> dict[str, int]:
    """Compte les findings non informatifs par catégorie pour une page multi."""
    counts: dict[str, int] = {}
    findings = page.get("findings") if isinstance(page.get("findings"), list) else []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity", "info") or "info").lower()
        if severity == "info":
            continue
        category = str(finding.get("category", "other") or "other")
        effective_cat = INTRUSIVE_CATEGORY_MAPPING.get(category, "other") if scan_mode == "intrusive" else category
        counts[effective_cat] = counts.get(effective_cat, 0) + 1
    return counts


def _count_page_infos_by_category(page: dict, scan_mode: str) -> dict[str, int]:
    """Compte les findings informatifs par catégorie pour une page multi."""
    counts: dict[str, int] = {}
    findings = page.get("findings") if isinstance(page.get("findings"), list) else []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity", "info") or "info").lower()
        if severity != "info":
            continue
        category = str(finding.get("category", "other") or "other")
        effective_cat = INTRUSIVE_CATEGORY_MAPPING.get(category, "other") if scan_mode == "intrusive" else category
        counts[effective_cat] = counts.get(effective_cat, 0) + 1
    return counts


def _build_single_table_html(
    repartition_label: str,
    cat_label: str,
    nb_tests_label: str,
    status_label: str,
    rows: list[str],
) -> str:
    """Construit le tableau synthèse standard (single)."""
    return f"""
    <h3 class="subsection-title">{repartition_label}</h3>
    <table class="data-table">
        <thead><tr><th>{cat_label}</th><th>{nb_tests_label}</th><th>{status_label}</th></tr></thead>
        <tbody>{"".join(rows) if rows else "<tr><td colspan='3'>—</td></tr>"}</tbody>
    </table>
    """


def _build_multi_table_html(
    note_html: str,
    cat_label: str,
    headers: str,
    rows: list[str],
) -> str:
    """Construit le tableau de comparaison multi-pages."""
    return f"""
    <div class="multi-compare-landscape">
        {note_html}
        <table class="data-table data-table-compact multi-compare-table">
            <thead>
                <tr>
                    <th>{cat_label}</th>
                    {headers}
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    </div>
    """


def _build_anomalies_block_html(
    findings_count: int,
    anomaly_label: str,
    anomalies_label: str,
) -> str:
    """Construit le bloc de compteur d'anomalies pour le mode single."""
    label = anomaly_label if findings_count == 1 else anomalies_label
    return f"""
    <div class="synthese-anomalies-block">
        <div class="synthese-anomalies-counter">
            <span class="synthese-anomalies-value">{findings_count}</span>
            <span class="synthese-anomalies-label">{label}</span>
        </div>
    </div>
    """


def _chunk_pages(pages: list[dict], chunk_size: int) -> list[list[dict]]:
    """Découpe la liste de pages en blocs de taille fixe."""
    if chunk_size <= 0:
        return [pages]
    return [pages[i : i + chunk_size] for i in range(0, len(pages), chunk_size)]  # noqa: E203


def _build_multi_headers_and_hosts(
    pages: list[dict],
    base_url: str,
) -> tuple[str, set[str]]:
    """Construit les en-têtes de colonnes et la liste des hôtes externes."""
    base_host = (urlparse(base_url).hostname or "").lower()
    external_hosts: set[str] = set()
    header_cells: list[str] = []

    for page in pages:
        page_url = str(page.get("url", "") or "")
        parsed = urlparse(page_url)
        host = (parsed.hostname or "").lower()
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        if host and host == base_host:
            label = path
        else:
            label = f"{host}{path}" if host else _format_url_display(page_url)
            if host:
                external_hosts.add(host)

        header_cells.append(f"<th>{escape(_prevent_break_after_slash(label))}</th>")

    return "".join(header_cells), external_hosts


def _collect_external_hosts(pages: list[dict], base_url: str) -> set[str]:
    """Retourne les hôtes différents du domaine de base."""
    base_host = (urlparse(base_url).hostname or "").lower()
    hosts: set[str] = set()
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_url = str(page.get("url", "") or "")
        host = (urlparse(page_url).hostname or "").lower()
        if host and host != base_host:
            hosts.add(host)
    return hosts


def build_synthese(
    by_category: dict[str, list[Finding]],
    ordered_cats: list[str],
    findings: list[Finding],
    score_val: int,
    score_color: str,
    lang: str,
    base_url: str = "",
    result_mode: str | None = None,
    page_results: list[dict] | None = None,
    scan_mode: str = "passive",
    info_by_category: dict[str, list[Finding]] | None = None,
) -> str:
    """Construit le HTML de la section Synthèse."""
    synthese_label = t("synthese", lang)
    score_synthese = t("score", lang)
    status_label = t("status", lang)
    status_ok = t("status_ok", lang)
    anomalies_word = t("anomalies", lang)
    anomalies_one = t("anomalies_one", lang)
    repartition_label = t("repartition", lang)
    cat_label = t("category", lang)
    nb_tests_label = t("nb_tests", lang)
    anomalies_label = t("anomalies_detected", lang)
    anomaly_label = t("anomaly_detected", lang)
    infos_label = t("infos", lang)
    info_label = t("infos_one", lang)
    info_by_category = info_by_category or {}

    cat_config = get_category_config(scan_mode)
    checked_cats = cat_config.checked
    category_labels = get_category_labels(lang, scan_mode=scan_mode)

    synthese_rows = _build_single_summary_rows(
        by_category=by_category,
        info_by_category=info_by_category,
        checked_cats=checked_cats,
        category_labels=category_labels,
        status_ok=status_ok,
        anomalies_one=anomalies_one,
        anomalies_word=anomalies_word,
        infos_one=info_label,
        infos_word=infos_label,
    )

    circumference = 2 * 3.14159 * 42
    stroke_dashoffset = circumference * (1 - score_val / 100)
    is_multi = result_mode == "multi" and isinstance(page_results, list) and len(page_results) > 0
    score_label = t("average_score", lang) if is_multi else score_synthese
    anomalies_block_html = (
        ""
        if is_multi
        else _build_anomalies_block_html(
            findings_count=len(findings),
            anomaly_label=anomaly_label,
            anomalies_label=anomalies_label,
        )
    )
    if is_multi:
        max_cols_per_table = 8
        score_row_label = t("score", lang)
        page_chunks = _chunk_pages(page_results, max_cols_per_table)
        all_external_hosts = _collect_external_hosts(page_results, base_url)

        note_base = t("comparison_note_base_paths", lang)
        tables_html: list[str] = []
        for idx, chunk in enumerate(page_chunks):
            headers, _ = _build_multi_headers_and_hosts(chunk, base_url)
            compare_rows = _build_multi_compare_rows(
                multi_pages=chunk,
                checked_cats=checked_cats,
                category_labels=category_labels,
                score_row_label=score_row_label,
                scan_mode=scan_mode,
            )
            note_html = ""
            if idx == 0:
                note_external = ""
                if all_external_hosts:
                    note_external = t("comparison_note_external_hosts", lang).format(hosts=", ".join(sorted(all_external_hosts)))
                note_html = f'<p class="comparison-note">{escape(note_base)}' + (f"<br/>{escape(note_external)}" if note_external else "") + "</p>"

            tables_html.append(
                _build_multi_table_html(
                    note_html=note_html,
                    cat_label=cat_label,
                    headers=headers,
                    rows=compare_rows,
                )
            )

        synthese_table_html = "".join(tables_html)
    else:
        synthese_table_html = _build_single_table_html(
            repartition_label=repartition_label,
            cat_label=cat_label,
            nb_tests_label=nb_tests_label,
            status_label=status_label,
            rows=synthese_rows,
        )

    return f"""
    <div class="report-section" id="synthese">
        <h2 class="section-title">1. {synthese_label}</h2>
        <div class="synthese-gauge-block">
            <span class="synthese-gauge-label">{score_label}</span>
            <div class="synthese-gauge-wrapper">
                <svg class="synthese-gauge" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(148,163,184,0.3)" stroke-width="8"/>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="{score_color}" stroke-width="8" stroke-linecap="round"
                            stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}"
                            transform="rotate(-90 50 50)"/>
                </svg>
                <span class="synthese-gauge-value" style="color:{score_color}">{score_val}</span>
            </div>
        </div>
        {anomalies_block_html}
        {synthese_table_html}
    </div>
    """
