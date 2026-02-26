"use client";

import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import type { ScanResult, ScanFinding } from "../../services/scanService";
import { ExternalLink } from "lucide-react";

const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"] as const;

function severitySort(a: ScanFinding, b: ScanFinding): number {
  const ia = SEVERITY_ORDER.indexOf(
    a.severity as (typeof SEVERITY_ORDER)[number],
  );
  const ib = SEVERITY_ORDER.indexOf(
    b.severity as (typeof SEVERITY_ORDER)[number],
  );
  const ai = ia === -1 ? 99 : ia;
  const bi = ib === -1 ? 99 : ib;
  return ai - bi;
}

function getScoreBadge(score: number): { emoji: string; labelKey: string } {
  if (score >= 80) return { emoji: "🟢", labelKey: "scanner.scoreGood" };
  if (score >= 50) return { emoji: "🟡", labelKey: "scanner.scoreMedium" };
  return { emoji: "🔴", labelKey: "scanner.scoreLow" };
}

function getCategoryKey(category: string): string {
  const map: Record<string, string> = {
    tls: "scanner.categoryTls",
    headers: "scanner.categoryHeaders",
    cookies: "scanner.categoryCookies",
    exposed_files: "scanner.categoryExposedFiles",
    directory_listing: "scanner.categoryDirectoryListing",
    robots_txt: "scanner.categoryRobotsTxt",
    tech_fingerprinting: "scanner.categoryTechFingerprinting",
  };
  return map[category] ?? category;
}

function getSeverityKey(severity: string): string {
  const map: Record<string, string> = {
    critical: "scanner.severityCritical",
    high: "scanner.severityHigh",
    medium: "scanner.severityMedium",
    low: "scanner.severityLow",
    info: "scanner.severityInfo",
  };
  return map[severity] ?? severity;
}

interface ScanResultsProps {
  result: ScanResult;
  onNewScan: () => void;
}

export default function ScanResults({ result, onNewScan }: ScanResultsProps) {
  const { t } = useLanguage();
  const badge = getScoreBadge(result.score);
  const sortedFindings = [...result.findings].sort(severitySort);

  const byCategory = sortedFindings.reduce<Record<string, number>>((acc, f) => {
    acc[f.category] = (acc[f.category] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <div className="scanner-block flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-3xl" aria-hidden>
                {badge.emoji}
              </span>
              <div>
                <p className="text-2xl font-bold text-[var(--text)]">
                  {result.score}/100
                </p>
                <p className="text-sm text-[var(--muted)]">
                  {t(badge.labelKey)}
                </p>
              </div>
            </div>
            <div className="text-sm text-[var(--muted)]">
              {t("scanner.duration")} : {result.duration.toFixed(1)}
              {t("scanner.seconds")}
            </div>
          </div>
          <GenericButton
            label={t("scanner.newScan")}
            variant="outline"
            onClick={onNewScan}
          />
        </div>
      </AnimateInView>

      {Object.keys(byCategory).length > 0 && (
        <AnimateInView
          className="landing-section landing-reveal-scanner"
          as="div"
        >
          <div className="scanner-block rounded-xl border border-[var(--border)] bg-[var(--color-surface-input)] p-4">
            <h3 className="mb-3 text-sm font-semibold text-[var(--text)]">
              {t("scanner.findingsByCategory")}
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(byCategory).map(([cat, count]) => (
                <span
                  key={cat}
                  className="rounded-full bg-[var(--color-surface-hover)] px-3 py-1 text-xs text-[var(--text)]"
                >
                  {t(getCategoryKey(cat))}: {count}
                </span>
              ))}
            </div>
          </div>
        </AnimateInView>
      )}

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <div className="scanner-block">
          <h3 className="mb-3 text-lg font-semibold text-[var(--text)]">
            {t("scanner.findings")} ({sortedFindings.length})
          </h3>
          {sortedFindings.length === 0 ? (
            <p className="text-[var(--muted)]">{t("scanner.noFindings")}</p>
          ) : (
            <ul className="space-y-4">
              {sortedFindings.map((f, i) => (
                <AnimateInView
                  key={`${f.id}-${i}`}
                  className="landing-reveal-finding"
                  as="li"
                >
                  <FindingCard
                    finding={f}
                    t={t}
                    getCategoryKey={getCategoryKey}
                    getSeverityKey={getSeverityKey}
                  />
                </AnimateInView>
              ))}
            </ul>
          )}
        </div>
      </AnimateInView>
    </div>
  );
}

function FindingCard({
  finding,
  t,
  getCategoryKey,
  getSeverityKey,
}: {
  finding: ScanFinding;
  t: (k: string) => string;
  getCategoryKey: (c: string) => string;
  getSeverityKey: (s: string) => string;
}) {
  const severityColors: Record<string, string> = {
    critical: "bg-red-500/20 text-red-700 dark:text-red-400",
    high: "bg-orange-500/20 text-orange-700 dark:text-orange-400",
    medium: "bg-amber-500/20 text-amber-700 dark:text-amber-400",
    low: "bg-blue-500/20 text-blue-700 dark:text-blue-400",
    info: "bg-slate-500/20 text-slate-600 dark:text-slate-400",
  };
  const color = severityColors[finding.severity] ?? severityColors.info;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--color-surface-input)] p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${color}`}>
          {t(getSeverityKey(finding.severity))}
        </span>
        <span className="text-xs text-[var(--muted)]">
          {t(getCategoryKey(finding.category))}
        </span>
      </div>
      <h4 className="mb-2 font-medium text-[var(--text)]">{finding.title}</h4>
      {finding.evidence && (
        <p className="mb-2 text-sm text-[var(--muted)]">
          <span className="font-medium">{t("scanner.evidence")}:</span>{" "}
          {finding.evidence}
        </p>
      )}
      <div className="rounded-lg bg-[var(--color-surface-hover)] p-3">
        <p className="text-sm font-medium text-[var(--text)]">
          {t("scanner.howToFix")}
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {finding.recommendation}
        </p>
        {finding.references.length > 0 && (
          <ul className="mt-2 space-y-1">
            {finding.references.map((ref, i) => (
              <li key={i}>
                <a
                  href={ref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-[rgb(var(--primary))] hover:underline"
                >
                  <ExternalLink className="h-3 w-3" />
                  {ref}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
