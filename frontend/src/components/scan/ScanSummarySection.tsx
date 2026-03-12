"use client";

/**
 * Section résumé d'un scan : table des tests effectués, résumés par catégorie
 * (avec descriptions, posture TLS, anomalies) et liste des findings détaillés.
 *
 * Utilisé par ScanResults (scan page simple) et MultiScanResults (par page
 * dans le scan multi-URL) pour garantir un affichage identique dans les deux modes.
 */

import AnimateInView from "../AnimateInView";
import Card from "../ui/cards/Card";
import FindingCard from "./FindingCard";
import { useLanguage } from "../LanguageProvider";
import { renderWithBold } from "../../utils/renderWithBold";
import type { ScanFinding, CategorySummary } from "../../services/scanService";
import {
  getCategoryKey,
  getCategorySummaryOkKey,
  severitySort,
  CHECKED_CATEGORIES_ORDER,
  CHECKS_COUNT_FALLBACK,
} from "./scanConstants";

interface ScanSummarySectionProps {
  findings: ScanFinding[];
  category_summaries?: CategorySummary[];
  total_tests_count?: number;
  /**
   * Préfixe unique pour les ancres HTML (évite les collisions entre pages
   * dans le mode multi-URL). Défaut : chaîne vide.
   */
  anchorPrefix?: string;
  /** Si true, entoure chaque bloc dans une AnimateInView. Défaut : true. */
  animate?: boolean;
}

/** Construit des résumés de fallback quand category_summaries est absent. */
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

export default function ScanSummarySection({
  findings,
  category_summaries,
  total_tests_count,
  anchorPrefix = "",
  animate = true,
}: ScanSummarySectionProps) {
  const { t, language } = useLanguage();

  const sortedFindings = [...findings].sort(severitySort);

  const byCategory = sortedFindings.reduce<Record<string, number>>((acc, f) => {
    acc[f.category] = (acc[f.category] ?? 0) + 1;
    return acc;
  }, {});

  const summaries = category_summaries ?? buildFallbackSummaries(byCategory);

  const checksCountByCategory = summaries.reduce<Record<string, number>>(
    (acc, entry) => {
      acc[entry.category] =
        entry.checks_count ??
        (language === "en" ? entry.checks_en : entry.checks_fr)?.length ??
        CHECKS_COUNT_FALLBACK[entry.category] ??
        0;
      return acc;
    },
    {},
  );

  const totalTestsCount =
    total_tests_count ??
    CHECKED_CATEGORIES_ORDER.reduce(
      (sum, cat) => sum + (checksCountByCategory[cat] ?? 0),
      0,
    );

  const Wrap = animate ? AnimateInView : "div";
  const wrapProps = animate
    ? {
        className: "landing-section landing-reveal-scanner",
        as: "div" as const,
      }
    : { className: "" };

  return (
    <>
      {/* ── Table des tests effectués ── */}
      <Wrap {...(wrapProps as object)}>
        <Card disableHover className="scanner-block p-4 overflow-x-auto">
          <h3 className="mb-4 text-center text-sm font-semibold uppercase tracking-wider text-[var(--text)]">
            {t("scanner.testsPerformed")}{" "}
            <span className="font-normal normal-case">
              ({totalTestsCount} {t("scanner.auTotal")})
            </span>
          </h3>
          <table className="w-full min-w-[280px] text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="py-3 px-4 text-left font-semibold text-[var(--text)]">
                  {t("scanner.test")}
                </th>
                <th className="py-3 px-4 text-center font-semibold text-[var(--text)]">
                  {t("scanner.testsCount")}
                </th>
                <th className="py-3 px-4 text-right font-semibold text-[var(--text)]">
                  {t("scanner.status")}
                </th>
              </tr>
            </thead>
            <tbody>
              {CHECKED_CATEGORIES_ORDER.map((cat) => {
                const count = byCategory[cat] ?? 0;
                const nbChecks = checksCountByCategory[cat] ?? 0;
                const anchorId = `${anchorPrefix}anomalies-${cat}`;
                return (
                  <tr
                    key={cat}
                    className="border-b border-[var(--color-border)] last:border-b-0"
                  >
                    <td className="py-3 px-4 text-[var(--text)]">
                      {t(getCategoryKey(cat))}
                    </td>
                    <td className="py-3 px-4 text-center text-[var(--muted)]">
                      {nbChecks}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {count === 0 ? (
                        <span className="font-medium text-[rgb(var(--success))]">
                          {t("scanner.statusOk")}
                        </span>
                      ) : (
                        <a
                          href={`#${anchorId}`}
                          onClick={(e) => {
                            e.preventDefault();
                            document
                              .getElementById(anchorId)
                              ?.scrollIntoView({ behavior: "smooth" });
                          }}
                          className="font-medium text-[rgb(var(--warning))] hover:underline cursor-pointer"
                        >
                          {count}{" "}
                          {t(
                            count === 1
                              ? "scanner.anomalies_one"
                              : "scanner.anomalies",
                          )}
                        </a>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      </Wrap>

      {/* ── Résumés par catégorie ── */}
      <Wrap {...(wrapProps as object)}>
        <Card disableHover className="scanner-block p-4 sm:p-6">
          <h3 className="mb-6 text-center text-sm font-semibold uppercase tracking-wider text-[var(--text)]">
            {t("scanner.summarySectionTitle")}
          </h3>
          <div className="space-y-6">
            {summaries.map((entry) => {
              const desc =
                language === "en" ? entry.description_en : entry.description_fr;
              const label =
                (language === "en" ? entry.label_en : entry.label_fr) ||
                t(getCategoryKey(entry.category));
              const shortSummary =
                desc || t(getCategorySummaryOkKey(entry.category));
              const hasAnomalies = entry.anomaly_count > 0;
              const anchorId = `${anchorPrefix}anomalies-${entry.category}`;

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
                          href={`#${anchorId}`}
                          onClick={(e) => {
                            e.preventDefault();
                            document
                              .getElementById(anchorId)
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
                            href={`#${anchorId}`}
                            onClick={(e) => {
                              e.preventDefault();
                              document
                                .getElementById(anchorId)
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
                        const categoryFindings = sortedFindings.filter(
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
      </Wrap>

      {/* ── Findings détaillés ── */}
      <Wrap {...(wrapProps as object)}>
        <Card
          disableHover
          className="scanner-block p-4"
          id={
            anchorPrefix
              ? `${anchorPrefix}anomalies-section`
              : "anomalies-section"
          }
        >
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
                  const anchorId = `${anchorPrefix}anomalies-${f.category}`;
                  return (
                    <li
                      key={`${f.id}-${i}`}
                      id={isFirstOfCategory ? anchorId : undefined}
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
      </Wrap>
    </>
  );
}
