"""Sommaire du rapport PDF (sections et sous-parties)."""

from html import escape

from app.config.pdf import get_category_labels
from app.schemas.finding import Finding
from app.services.pdf_report.constants import severity_index
from app.services.pdf_report.pdf_i18n import t


def build_sommaire(
    by_category: dict[str, list[Finding]],
    ordered_cats: list[str],
    lang: str,
) -> str:
    """Construit le HTML du sommaire (sections et sous-parties 2.1, 2.2, etc.)."""
    from app.config.pdf import get_pdf_settings

    sommaire_label = t("sommaire", lang)
    synthese_label = t("synthese", lang)
    references_label = t("references_section", lang)
    category_labels = get_category_labels(lang)
    settings = get_pdf_settings()
    cats_to_toc = [c for c in settings.categories.checked if c in settings.categories.order] or list(settings.categories.order)

    other_tests_label = t("other_tests_section", lang)

    items = [f'<li class="toc-item"><a href="#synthese" class="toc-link"><span class="toc-num">1</span> {synthese_label}</a></li>']
    section_num = 2
    for cat in cats_to_toc:
        cat_findings = by_category.get(cat, [])
        if not cat_findings:
            continue
        label = category_labels.get(cat, cat)
        items.append(
            f'<li class="toc-item"><a href="#sect-{cat}" class="toc-link"><span class="toc-num">{section_num}</span> {escape(label)}</a></li>'
        )
        summary_label = t("summary", lang)
        items.append(
            f'<li class="toc-item toc-sub"><a href="#sect-{cat}-intro" class="toc-link">'
            f'<span class="toc-num">{section_num}.1</span> {escape(summary_label)}</a></li>'
        )
        for idx, f in enumerate(sorted(cat_findings, key=lambda x: severity_index(x.severity)), start=2):
            title = escape(f.title)
            items.append(
                f'<li class="toc-item toc-sub"><a href="#finding-{section_num}-{idx}" class="toc-link">'
                f'<span class="toc-num">{section_num}.{idx}</span> {title}</a></li>'
            )
        section_num += 1
    ok_cats = [c for c in cats_to_toc if len(by_category.get(c, [])) == 0]
    if ok_cats:
        items.append(
            f'<li class="toc-item"><a href="#sect-other-tests" class="toc-link">'
            f'<span class="toc-num">{section_num}</span> {escape(other_tests_label)}</a></li>'
        )
        other_summary_label = t("summary", lang)
        items.append(
            f'<li class="toc-item toc-sub"><a href="#sect-other-tests-intro" class="toc-link">'
            f'<span class="toc-num">{section_num}.1</span> {escape(other_summary_label)}</a></li>'
        )
        for sub_num, cat in enumerate(ok_cats, start=2):
            label = category_labels.get(cat, cat)
            items.append(
                f'<li class="toc-item toc-sub"><a href="#other-{cat}" class="toc-link">'
                f'<span class="toc-num">{section_num}.{sub_num}</span> {escape(label)}</a></li>'
            )
        section_num += 1
    items.append(
        f'<li class="toc-item"><a href="#references" class="toc-link"><span class="toc-num">{section_num}</span> {escape(references_label)}</a></li>'
    )
    return f"""
    <div class="report-section sommaire" id="sommaire">
        <h2 class="section-title">{sommaire_label}</h2>
        <ol class="toc-list">{"".join(items)}</ol>
    </div>
    """
