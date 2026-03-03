"use client";

import { useCallback, useState, useEffect } from "react";
import Image from "next/image";
import { createPortal } from "react-dom";
import {
  Download,
  FileSpreadsheet,
  FileJson,
  FileText,
  FileOutput,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../cards/Card";
import Badge from "../Badge";
import Modal from "../Modal";
import FindingCard from "./FindingCard";
import type { ScanResult } from "../../services/scanService";
import {
  getScoreBadge,
  getCategoryKey,
  getCategorySummaryOkKey,
  severitySort,
  CHECKED_CATEGORIES_ORDER,
} from "./scanConstants";
import type { CategorySummary } from "../../services/scanService";
import { exportScanResult, type ExportFormat } from "../../utils/exportScan";
import { formatUrlDisplay } from "../../utils/urlFormat";
import { downloadScanPdf } from "../../services/scanHistoryService";
import { showErrorToast } from "../../utils/toastNotifications";
import { renderWithBold } from "../../utils/renderWithBold";

interface ScanResultsProps {
  result: ScanResult;
  scanId: string | null;
  onNewScan: () => void;
}

const EXPORT_FORMATS: {
  value: ExportFormat | "pdf";
  labelKey: string;
  icon: React.ReactNode;
  requiresScanId?: boolean;
}[] = [
  {
    value: "csv",
    labelKey: "scanner.exportCsv",
    icon: <FileText className="w-5 h-5" />,
  },
  {
    value: "json",
    labelKey: "scanner.exportJson",
    icon: <FileJson className="w-5 h-5" />,
  },
  {
    value: "xlsx",
    labelKey: "scanner.exportXlsx",
    icon: <FileSpreadsheet className="w-5 h-5" />,
  },
  {
    value: "pdf",
    labelKey: "scanner.exportPdf",
    icon: <FileOutput className="w-5 h-5" />,
    requiresScanId: true,
  },
];

/** Icône globe SVG vectorielle pour fallback favicon (évite la pixellisation). */
const DefaultFavicon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-8 w-8 text-[var(--muted)]"
    aria-hidden
  >
    <circle cx="12" cy="12" r="10" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    <path d="M2 12h20" />
  </svg>
);

const EXPORT_BUTTON_BOTTOM_DEFAULT = 20;
/** Hauteur fixe au-dessus du footer quand il est visible (footer ~200px + marge). */
const EXPORT_BUTTON_BOTTOM_ABOVE_FOOTER = 220;

/** Construit des résumés de fallback quand category_summaries n'est pas dans la réponse (ex. historique). */
function buildFallbackSummaries(
  byCategory: Record<string, number>,
): CategorySummary[] {
  return CHECKED_CATEGORIES_ORDER.map((cat) => ({
    category: cat,
    label_fr: "",
    label_en: "",
    description_fr: "",
    description_en: "",
    checks_fr: [],
    checks_en: [],
    anomaly_count: byCategory[cat] ?? 0,
  }));
}

export default function ScanResults({
  result,
  scanId,
  onNewScan,
}: ScanResultsProps) {
  const { t, language } = useLanguage();
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [faviconError, setFaviconError] = useState(false);
  const [gaugeScore, setGaugeScore] = useState(0);

  useEffect(() => {
    setFaviconError(false);
  }, [result.url]);

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      setGaugeScore(result.score);
    });
    return () => cancelAnimationFrame(raf);
  }, [result.score]);
  const [exportButtonBottom, setExportButtonBottom] = useState(
    EXPORT_BUTTON_BOTTOM_DEFAULT,
  );
  const badge = getScoreBadge(result.score);

  useEffect(() => {
    const footer = document.getElementById("site-footer");
    if (!footer) return;
    const updateBottom = (): void => {
      const rect = footer.getBoundingClientRect();
      const footerVisible = rect.top < window.innerHeight;
      setExportButtonBottom(
        footerVisible
          ? EXPORT_BUTTON_BOTTOM_ABOVE_FOOTER
          : EXPORT_BUTTON_BOTTOM_DEFAULT,
      );
    };
    const observer = new IntersectionObserver(updateBottom, {
      threshold: 0,
      rootMargin: "0px",
    });
    observer.observe(footer);
    const throttledUpdate = (): void => {
      requestAnimationFrame(updateBottom);
    };
    window.addEventListener("scroll", throttledUpdate, { passive: true });
    window.addEventListener("resize", throttledUpdate);
    updateBottom();
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", throttledUpdate);
      window.removeEventListener("resize", throttledUpdate);
    };
  }, []);
  const sortedFindings = [...result.findings].sort(severitySort);

  const handleExport = useCallback(
    async (format: ExportFormat | "pdf") => {
      if (format === "pdf") {
        if (!scanId) return;
        setPdfLoading(true);
        try {
          await downloadScanPdf(scanId, language as "fr" | "en");
          setExportModalOpen(false);
        } catch {
          showErrorToast(t("scanner.exportPdfDownload") + " — erreur");
        } finally {
          setPdfLoading(false);
        }
      } else {
        exportScanResult(result, format);
        setExportModalOpen(false);
      }
    },
    [result, scanId, language, t],
  );

  const byCategory = sortedFindings.reduce<Record<string, number>>((acc, f) => {
    acc[f.category] = (acc[f.category] ?? 0) + 1;
    return acc;
  }, {});

  const displayUrl = formatUrlDisplay(result.url);

  const domain = (() => {
    try {
      return new URL(result.url).hostname;
    } catch {
      return displayUrl.split("/")[0] || displayUrl;
    }
  })();

  const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;

  return (
    <div className="space-y-6">
      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <Card
          disableHover
          className="scanner-block overflow-hidden border-2 border-[var(--color-border)]"
        >
          <div className="p-6 sm:p-8 text-center">
            <div className="mb-4 flex justify-center">
              {faviconError ? (
                <div
                  className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-surface-hover)]"
                  aria-hidden
                >
                  <DefaultFavicon />
                </div>
              ) : (
                <Image
                  src={faviconUrl}
                  alt=""
                  width={56}
                  height={56}
                  className="h-14 w-14 rounded-xl object-cover"
                  onError={() => setFaviconError(true)}
                />
              )}
            </div>
            <h2
              className="text-xl sm:text-2xl lg:text-3xl font-bold text-[var(--text)] break-all"
              title={result.url}
            >
              {displayUrl}
            </h2>
            <p className="text-xs sm:text-sm text-muted-theme mt-2">
              {t("scanner.duration")} {result.duration.toFixed(1)}
              {t("scanner.seconds")}
            </p>
            <div className="mt-6 flex flex-col items-center gap-2">
              <div
                className="relative flex h-20 w-20 flex-shrink-0 sm:h-24 sm:w-24"
                aria-hidden
              >
                <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke="var(--color-surface-hover)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke={badge.ringColor}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 42}
                    strokeDashoffset={2 * Math.PI * 42 * (1 - gaugeScore / 100)}
                    style={{
                      transition: "stroke-dashoffset 0.8s ease-out",
                    }}
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-[var(--text)] sm:text-3xl">
                  {result.score}
                </span>
              </div>
              <p className="text-base font-medium text-[var(--muted)]">
                {t(badge.labelKey)}
              </p>
            </div>
            <div className="mt-8 flex flex-col items-center gap-2">
              <span className="text-2xl font-bold text-[var(--text)] sm:text-3xl">
                {sortedFindings.length}
              </span>
              <p className="text-center text-sm font-semibold uppercase tracking-wider text-[var(--muted)]">
                {t("scanner.findings")}
              </p>
            </div>
            {Object.keys(byCategory).length > 0 && (
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {Object.entries(byCategory).map(([cat, count]) => (
                  <Badge key={cat} variant="default" className="text-sm">
                    {t(getCategoryKey(cat))}: {count}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </Card>
      </AnimateInView>

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <Card disableHover className="scanner-block p-4 overflow-x-auto">
          <h3 className="mb-4 text-center text-sm font-semibold uppercase tracking-wider text-[var(--text)]">
            {t("scanner.testsPerformed")}
          </h3>
          <table className="w-full min-w-[280px] text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="py-3 px-4 text-left font-semibold text-[var(--text)]">
                  {t("scanner.test")}
                </th>
                <th className="py-3 px-4 text-right font-semibold text-[var(--text)]">
                  {t("scanner.status")}
                </th>
              </tr>
            </thead>
            <tbody>
              {CHECKED_CATEGORIES_ORDER.map((cat) => {
                const count = byCategory[cat] ?? 0;
                return (
                  <tr
                    key={cat}
                    className="border-b border-[var(--color-border)] last:border-b-0"
                  >
                    <td className="py-3 px-4 text-[var(--text)]">
                      {t(getCategoryKey(cat))}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {count === 0 ? (
                        <span className="font-medium text-[rgb(var(--success))]">
                          {t("scanner.statusOk")}
                        </span>
                      ) : (
                        <span className="font-medium text-[rgb(var(--warning))]">
                          {count}{" "}
                          {t(
                            count === 1
                              ? "scanner.anomalies_one"
                              : "scanner.anomalies",
                          )}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      </AnimateInView>

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <Card disableHover className="scanner-block p-4 sm:p-6">
          <h3 className="mb-6 text-center text-sm font-semibold uppercase tracking-wider text-[var(--text)]">
            {t("scanner.summarySectionTitle")}
          </h3>
          <div className="space-y-6">
            {(
              result.category_summaries ?? buildFallbackSummaries(byCategory)
            ).map((entry) => {
              const desc =
                language === "en" ? entry.description_en : entry.description_fr;
              const label =
                (language === "en" ? entry.label_en : entry.label_fr) ||
                t(getCategoryKey(entry.category));
              const shortSummary =
                desc || t(getCategorySummaryOkKey(entry.category));
              const hasAnomalies = entry.anomaly_count > 0;

              return (
                <div
                  key={entry.category}
                  className="rounded-lg border border-[var(--color-border)] p-4"
                >
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <h4 className="font-semibold text-[var(--text)]">
                      {label}
                    </h4>
                    <div className="flex flex-wrap items-center gap-2">
                      {entry.category === "tls" && entry.tls_posture ? (
                        <span
                          className={`text-sm font-medium ${
                            entry.tls_posture === "ok"
                              ? "text-[rgb(var(--success))]"
                              : entry.tls_posture === "warning"
                                ? "text-[rgb(var(--warning))]"
                                : "text-[rgb(var(--danger))]"
                          }`}
                        >
                          {t(
                            `scanner.tlsPosture${entry.tls_posture.charAt(0).toUpperCase()}${entry.tls_posture.slice(1)}`,
                          )}
                        </span>
                      ) : hasAnomalies ? (
                        <a
                          href={`#anomalies-${entry.category}`}
                          onClick={(e) => {
                            e.preventDefault();
                            document
                              .getElementById(`anomalies-${entry.category}`)
                              ?.scrollIntoView({ behavior: "smooth" });
                          }}
                          className="text-sm font-medium text-[rgb(var(--primary))] hover:underline"
                        >
                          {entry.anomaly_count}{" "}
                          {t(
                            entry.anomaly_count === 1
                              ? "scanner.anomalies_one"
                              : "scanner.anomalies",
                          )}{" "}
                          <span className="text-xs">
                            ({t("scanner.details")})
                          </span>
                        </a>
                      ) : (
                        <span className="text-sm font-medium text-[rgb(var(--success))]">
                          {t("scanner.statusOk")}
                        </span>
                      )}
                      {entry.category === "tls" &&
                        entry.tls_posture &&
                        hasAnomalies && (
                          <a
                            href={`#anomalies-${entry.category}`}
                            onClick={(e) => {
                              e.preventDefault();
                              document
                                .getElementById(`anomalies-${entry.category}`)
                                ?.scrollIntoView({ behavior: "smooth" });
                            }}
                            className="text-sm font-medium text-[rgb(var(--primary))] hover:underline"
                          >
                            {entry.anomaly_count}{" "}
                            {t(
                              entry.anomaly_count === 1
                                ? "scanner.anomalies_one"
                                : "scanner.anomalies",
                            )}{" "}
                            <span className="text-xs">
                              ({t("scanner.details")})
                            </span>
                          </a>
                        )}
                    </div>
                  </div>
                  {(desc || shortSummary) && (
                    <p className="mb-3 text-sm text-[var(--muted)] leading-relaxed">
                      {renderWithBold(desc || shortSummary)}
                    </p>
                  )}
                  {entry.category === "tls" && entry.tls_version && (
                    <p className="mb-3 text-sm text-[var(--muted)] leading-relaxed">
                      {t("scanner.tlsVersionPhraseBefore")}
                      <strong>{entry.tls_version}</strong>
                      {t("scanner.tlsVersionPhraseAfter")}
                    </p>
                  )}
                  <p className="text-sm text-[var(--muted)] leading-relaxed">
                    {hasAnomalies ? (
                      (() => {
                        const categoryFindings = result.findings.filter(
                          (f) => f.category === entry.category,
                        );
                        const titles = categoryFindings
                          .map((f) => f.title)
                          .join(", ");
                        const boldPart =
                          entry.anomaly_count === 1
                            ? t("scanner.summaryOneAnomalyBold")
                            : `${entry.anomaly_count} ${t("scanner.anomalies")}`;
                        const afterKey =
                          entry.anomaly_count === 1
                            ? "scanner.summaryOneAnomalyAfter"
                            : "scanner.summaryAnomaliesCountAfter";
                        const afterParams: Record<string, string | number> =
                          entry.anomaly_count === 1
                            ? { titles }
                            : { count: entry.anomaly_count, titles };
                        return (
                          <>
                            <strong>{boldPart}</strong>
                            {t(afterKey, afterParams)}
                          </>
                        );
                      })()
                    ) : (
                      <>
                        <strong>{t("scanner.summaryNoAnomaliesBold")}</strong>
                        {t("scanner.summaryNoAnomaliesAfter")}
                      </>
                    )}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>
      </AnimateInView>

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
        id="anomalies-section"
      >
        <Card disableHover className="scanner-block p-4">
          <h3 className="mb-4 text-center text-sm font-semibold uppercase tracking-wider text-[var(--text)]">
            {t("scanner.findings")}
          </h3>
          {sortedFindings.length === 0 ? (
            <p className="text-muted-theme">{t("scanner.noFindings")}</p>
          ) : (
            <ul className="divide-y-0">
              {(() => {
                const seenCategories = new Set<string>();
                return sortedFindings.map((f, i) => {
                  const isFirstOfCategory = !seenCategories.has(f.category);
                  if (isFirstOfCategory) seenCategories.add(f.category);
                  return (
                    <li
                      key={`${f.id}-${i}`}
                      id={
                        isFirstOfCategory
                          ? `anomalies-${f.category}`
                          : undefined
                      }
                    >
                      <AnimateInView
                        className="landing-reveal-finding"
                        as="div"
                      >
                        <FindingCard finding={f} />
                        {i < sortedFindings.length - 1 && (
                          <div
                            className="my-4 mx-auto w-[90%] border-t border-[var(--color-border)] opacity-50"
                            aria-hidden
                          />
                        )}
                      </AnimateInView>
                    </li>
                  );
                });
              })()}
            </ul>
          )}
        </Card>
      </AnimateInView>

      {typeof document !== "undefined" &&
        createPortal(
          <div
            className="fixed right-6 z-[9998] flex items-center gap-2 shadow-lg transition-all duration-200"
            style={{ position: "fixed", bottom: exportButtonBottom }}
            aria-label={t("scanner.export")}
          >
            <GenericButton
              label={t("scanner.newScan")}
              variant="outline"
              onClick={onNewScan}
            />
            <GenericButton
              label={t("scanner.export")}
              variant="primary"
              icon={<Download className="w-4 h-4" />}
              iconPosition="left"
              onClick={() => setExportModalOpen(true)}
            />
          </div>,
          document.body,
        )}

      <Modal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        title={t("scanner.export")}
        maxWidth="420px"
      >
        <p className="text-sm text-muted-theme mb-4">
          {t("scanner.exportDesc")}
        </p>
        <div className="flex flex-col gap-2">
          {EXPORT_FORMATS.map(({ value, labelKey, icon }) => {
            const isPdf = value === "pdf";
            const disabled = (isPdf && !scanId) || (isPdf && pdfLoading);
            return (
              <button
                key={value}
                type="button"
                onClick={() => !disabled && handleExport(value)}
                disabled={disabled}
                title={disabled ? t("scanner.exportPdfUnavailable") : undefined}
                className="flex items-center gap-3 w-full p-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] hover:bg-[var(--color-surface-hover)] transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[var(--color-surface-input)]"
              >
                {icon}
                <span className="font-medium">{t(labelKey)}</span>
                {disabled && (
                  <span className="text-xs text-muted-theme ml-auto">
                    {t("scanner.exportPdfUnavailable")}
                  </span>
                )}
                {isPdf && scanId && pdfLoading && (
                  <span className="text-xs text-muted-theme ml-auto">...</span>
                )}
              </button>
            );
          })}
        </div>
      </Modal>
    </div>
  );
}
