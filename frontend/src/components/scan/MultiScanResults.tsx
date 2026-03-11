"use client";

import { useState } from "react";
import { AlertTriangle, Globe, LayoutGrid } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../ui/cards/Card";
import ScanSummarySection from "./ScanSummarySection";
import { getScoreBadge, CHECKED_CATEGORIES_ORDER } from "./scanConstants";
import type {
  MultiScanResult,
  PageScanResult,
} from "../../services/scanService";
import { formatUrlDisplay } from "../../utils/urlFormat";

interface MultiScanResultsProps {
  result: MultiScanResult;
  onNewScan: () => void;
}

/** Score badge couleur compact pour les onglets et l'overview. */
function ScoreChip({ score }: { score: number }) {
  const { ringColor, labelKey } = getScoreBadge(score);
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold text-white"
      style={{ background: ringColor }}
      title={labelKey}
    >
      {score}/100
    </span>
  );
}

/** Vue détaillée d'une page : table des tests, résumés et findings complets. */
function PageDetail({ page }: { page: PageScanResult }) {
  const { t } = useLanguage();

  if (page.error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-[rgb(var(--danger))]/30 bg-[rgb(var(--danger))]/5 px-4 py-3 text-sm text-[rgb(var(--danger))]">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          {t("scanner.multiPageError")} : {page.error}
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ScanSummarySection
        findings={page.findings ?? []}
        category_summaries={page.category_summaries}
        total_tests_count={page.total_tests_count}
        anchorPrefix={`page-${encodeURIComponent(page.url)}-`}
        animate={false}
      />
    </div>
  );
}

/** Tableau comparatif : catégories × pages (heatmap rapide). */
function CompareTable({
  pageResults,
  lang,
}: {
  pageResults: PageScanResult[];
  lang: "fr" | "en";
}) {
  const allCategories = CHECKED_CATEGORIES_ORDER;
  const summaryMaps = pageResults.map((p) =>
    Object.fromEntries(
      (p.category_summaries ?? []).map((s) => [s.category, s]),
    ),
  );

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="sticky left-0 bg-[var(--surface)] px-3 py-2 text-left font-medium text-[var(--muted)] border-b border-[var(--border)]">
              Catégorie
            </th>
            {pageResults.map((p) => (
              <th
                key={p.url}
                className="px-2 py-2 text-center font-medium text-[var(--muted)] border-b border-[var(--border)] max-w-[100px]"
                title={p.url}
              >
                <span className="block truncate max-w-[90px]">
                  {formatUrlDisplay(p.url)}
                </span>
                <ScoreChip score={p.score} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {allCategories.map((cat) => {
            const hasData = summaryMaps.some((m) => m[cat]);
            if (!hasData) return null;
            const labelFr =
              summaryMaps.find((m) => m[cat])?.[cat]?.label_fr ?? cat;
            const labelEn =
              summaryMaps.find((m) => m[cat])?.[cat]?.label_en ?? cat;
            return (
              <tr
                key={cat}
                className="border-b border-[var(--border)] hover:bg-[var(--muted)]/5"
              >
                <td className="sticky left-0 bg-[var(--surface)] px-3 py-2 font-medium text-[var(--text)]">
                  {lang === "fr" ? labelFr : labelEn}
                </td>
                {pageResults.map((p) => {
                  const s = summaryMaps[pageResults.indexOf(p)]?.[cat];
                  if (!s)
                    return (
                      <td
                        key={p.url}
                        className="px-2 py-2 text-center text-[var(--muted)]"
                      >
                        —
                      </td>
                    );
                  const count = s.anomaly_count;
                  return (
                    <td key={p.url} className="px-2 py-2 text-center">
                      {count === 0 ? (
                        <span className="text-[rgb(var(--success))]">✓</span>
                      ) : (
                        <span className="inline-flex items-center justify-center rounded-full w-5 h-5 text-[10px] font-bold bg-[rgb(var(--warning))]/20 text-[rgb(var(--warning))]">
                          {count}
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

type TabId = "overview" | "compare" | number;

export default function MultiScanResults({
  result,
  onNewScan,
}: MultiScanResultsProps) {
  const { t, locale } = useLanguage();
  const lang = (locale === "fr" ? "fr" : "en") as "fr" | "en";
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  const { ringColor: globalRingColor } = getScoreBadge(result.score_global);
  const errorCount = result.page_results.filter((p) => p.error).length;
  const duration = result.duration.toFixed(1);

  return (
    <AnimateInView className="space-y-4 w-full" initialOnly>
      {/* Header global */}
      <Card disableHover>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Globe className="h-6 w-6 text-[rgb(var(--primary))]" />
            <div>
              <h2 className="section-title !mb-0 !text-left">
                {t("scanner.multiResultTitle")}
              </h2>
              <p
                className="text-sm text-[var(--muted)]"
                title={result.base_url}
              >
                {formatUrlDisplay(result.base_url)} —{" "}
                {t("scanner.multiPageCount", { count: result.urls.length })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-center">
              <div
                className="text-4xl font-black"
                style={{ color: globalRingColor }}
              >
                {result.score_global}
              </div>
              <div className="text-xs text-[var(--muted)]">
                {t("scanner.score")}
              </div>
            </div>
            <div className="text-xs text-[var(--muted)] space-y-0.5">
              <div>
                {result.urls.length} {t("scanner.multiPages")}
              </div>
              <div>{duration}s</div>
              {errorCount > 0 && (
                <div className="text-[rgb(var(--warning))]">
                  {errorCount} {t("scanner.multiPagesError")}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-4">
          <GenericButton
            type="button"
            label={t("scanner.newScan")}
            variant="secondary"
            onClick={onNewScan}
          />
        </div>
      </Card>

      {/* Navigation tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        <button
          type="button"
          onClick={() => setActiveTab("overview")}
          className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
            activeTab === "overview"
              ? "bg-[rgb(var(--primary))] text-white"
              : "bg-[var(--muted)]/10 text-[var(--muted)] hover:bg-[var(--muted)]/20"
          }`}
        >
          <span className="flex items-center gap-1.5">
            <LayoutGrid className="h-3.5 w-3.5" />
            {t("scanner.multiTabOverview")}
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("compare")}
          className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
            activeTab === "compare"
              ? "bg-[rgb(var(--primary))] text-white"
              : "bg-[var(--muted)]/10 text-[var(--muted)] hover:bg-[var(--muted)]/20"
          }`}
        >
          {t("scanner.multiTabCompare")}
        </button>
        {result.page_results.map((page, i) => (
          <button
            key={page.url}
            type="button"
            onClick={() => setActiveTab(i)}
            title={page.url}
            className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === i
                ? "bg-[rgb(var(--primary))] text-white"
                : "bg-[var(--muted)]/10 text-[var(--muted)] hover:bg-[var(--muted)]/20"
            }`}
          >
            {page.error ? (
              <AlertTriangle className="h-3 w-3 text-[rgb(var(--warning))]" />
            ) : (
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{
                  background: getScoreBadge(page.score).ringColor,
                }}
              />
            )}
            <span className="max-w-[120px] truncate">
              {formatUrlDisplay(page.url)}
            </span>
          </button>
        ))}
      </div>

      {/* Contenu de l'onglet actif */}
      {activeTab === "overview" && (
        <Card disableHover>
          <h3 className="section-title !text-left mb-4">
            {t("scanner.multiTabOverview")}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {result.page_results.map((page) => (
              <button
                key={page.url}
                type="button"
                onClick={() => setActiveTab(result.page_results.indexOf(page))}
                className="text-left rounded-lg border border-[var(--border)] p-3 hover:bg-[var(--muted)]/5 transition-colors"
              >
                <div className="flex items-center justify-between mb-1 gap-2">
                  <span
                    className="text-sm font-medium text-[var(--text)] truncate"
                    title={page.url}
                  >
                    {formatUrlDisplay(page.url)}
                  </span>
                  {page.error ? (
                    <AlertTriangle className="h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                  ) : (
                    <ScoreChip score={page.score} />
                  )}
                </div>
                {page.error ? (
                  <p className="text-xs text-[rgb(var(--warning))]">
                    {t("scanner.multiPageError")}
                  </p>
                ) : (
                  <p className="text-xs text-[var(--muted)]">
                    {page.findings?.length ?? 0} {t("scanner.findings")}
                    {page.total_tests_count
                      ? ` / ${page.total_tests_count} ${t("scanner.tests")}`
                      : ""}
                  </p>
                )}
              </button>
            ))}
          </div>
        </Card>
      )}

      {activeTab === "compare" && (
        <Card disableHover>
          <h3 className="section-title !text-left mb-4">
            {t("scanner.multiTabCompare")}
          </h3>
          <CompareTable pageResults={result.page_results} lang={lang} />
        </Card>
      )}

      {typeof activeTab === "number" && result.page_results[activeTab] && (
        <Card disableHover>
          <div className="flex items-center justify-between mb-4 gap-2">
            <h3
              className="section-title !text-left !mb-0 truncate"
              title={result.page_results[activeTab].url}
            >
              {formatUrlDisplay(result.page_results[activeTab].url)}
            </h3>
            {!result.page_results[activeTab].error && (
              <ScoreChip score={result.page_results[activeTab].score} />
            )}
          </div>
          <PageDetail page={result.page_results[activeTab]} />
        </Card>
      )}
    </AnimateInView>
  );
}
