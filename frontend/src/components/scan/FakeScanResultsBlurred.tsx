"use client";

/**
 * Affiche des résultats de scan factices floutés en arrière-plan du gate.
 * Donne envie à l'utilisateur de se connecter pour voir ses vrais résultats.
 */

import { useLanguage } from "../LanguageProvider";
import Card from "../ui/cards/Card";
import Badge from "../ui/Badge";
import { getCategoryKey, getSeverityKey } from "./scanConstants";
import type { BadgeVariant } from "../ui/Badge";

/** Données factices pour simuler un aperçu de résultats. */
const FAKE_SCORE = 72;
const FAKE_CATEGORIES = [
  { category: "headers", count: 2 },
  { category: "tls", count: 1 },
  { category: "cookies", count: 1 },
];
const FAKE_FINDINGS = [
  { severity: "high", category: "headers", title: "X-Frame-Options missing" },
  { severity: "medium", category: "tls", title: "TLS 1.0 enabled" },
  { severity: "low", category: "cookies", title: "Cookie without Secure flag" },
];

const SEVERITY_VARIANT: Record<string, BadgeVariant> = {
  critical: "error",
  high: "warning",
  medium: "warning",
  low: "info",
  info: "info",
};

export default function FakeScanResultsBlurred() {
  const { t } = useLanguage();

  return (
    <div
      className="space-y-6 select-none pointer-events-none"
      style={{
        filter: "blur(8px)",
        opacity: 0.8,
        userSelect: "none",
      }}
      aria-hidden
    >
      <Card
        disableHover
        className="scanner-block p-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-3xl" aria-hidden>
              🟡
            </span>
            <div>
              <p className="text-2xl font-bold text-[var(--text)]">
                {FAKE_SCORE}/100
              </p>
              <p className="text-sm text-[var(--muted)]">
                {t("scanner.scoreMedium")}
              </p>
            </div>
          </div>
          <div className="text-sm text-muted-theme">
            {t("scanner.duration")} : 12.3
            {t("scanner.seconds")}
          </div>
        </div>
      </Card>

      <Card disableHover className="scanner-block p-4">
        <h3 className="section-title !text-left !text-sm mb-3">
          {t("scanner.findingsByCategory")}
        </h3>
        <div className="flex flex-wrap gap-2">
          {FAKE_CATEGORIES.map(({ category, count }) => (
            <Badge key={category} variant="default">
              {t(getCategoryKey(category))}: {count}
            </Badge>
          ))}
        </div>
      </Card>

      <Card disableHover className="scanner-block p-4">
        <h3 className="section-title !text-left mb-3">
          {t("scanner.findings")}
        </h3>
        <ul className="space-y-4">
          {FAKE_FINDINGS.map((f, i) => (
            <li key={i}>
              <Card disableHover className="p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge variant={SEVERITY_VARIANT[f.severity] ?? "info"}>
                    {t(getSeverityKey(f.severity))}
                  </Badge>
                  <span className="text-xs text-muted-theme">
                    {t(getCategoryKey(f.category))}
                  </span>
                </div>
                <h4 className="font-medium">{f.title}</h4>
                <div className="mt-2 rounded-lg bg-[var(--color-surface-hover)] p-3">
                  <p className="text-sm text-muted-theme">
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                  </p>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
