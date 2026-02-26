"use client";

import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../cards/Card";
import Badge from "../Badge";
import FindingCard from "./FindingCard";
import type { ScanResult } from "../../services/scanService";
import { getScoreBadge, getCategoryKey, severitySort } from "./scanConstants";

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
        <Card
          disableHover
          className="scanner-block p-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
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
            <div className="text-sm text-muted-theme">
              {t("scanner.duration")} : {result.duration.toFixed(1)}
              {t("scanner.seconds")}
            </div>
          </div>
          <GenericButton
            label={t("scanner.newScan")}
            variant="outline"
            onClick={onNewScan}
          />
        </Card>
      </AnimateInView>

      {Object.keys(byCategory).length > 0 && (
        <AnimateInView
          className="landing-section landing-reveal-scanner"
          as="div"
        >
          <Card disableHover className="scanner-block p-4">
            <h3 className="section-title !text-left !text-sm mb-3">
              {t("scanner.findingsByCategory")}
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(byCategory).map(([cat, count]) => (
                <Badge key={cat} variant="default">
                  {t(getCategoryKey(cat))}: {count}
                </Badge>
              ))}
            </div>
          </Card>
        </AnimateInView>
      )}

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <Card disableHover className="scanner-block p-4">
          <h3 className="section-title !text-left mb-3">
            {t("scanner.findings")} ({sortedFindings.length})
          </h3>
          {sortedFindings.length === 0 ? (
            <p className="text-muted-theme">{t("scanner.noFindings")}</p>
          ) : (
            <ul className="space-y-4">
              {sortedFindings.map((f, i) => (
                <AnimateInView
                  key={`${f.id}-${i}`}
                  className="landing-reveal-finding"
                  as="li"
                >
                  <FindingCard finding={f} />
                </AnimateInView>
              ))}
            </ul>
          )}
        </Card>
      </AnimateInView>
    </div>
  );
}
