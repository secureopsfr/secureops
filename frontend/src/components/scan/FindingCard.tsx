"use client";

import { useLanguage } from "../LanguageProvider";
import Badge from "../ui/Badge";
import { ExternalLink } from "lucide-react";
import type { ScanFinding } from "../../services/scanService";
import { getCategoryKey, getSeverityKey } from "./scanConstants";
import type { BadgeVariant } from "../ui/Badge";

const SEVERITY_BADGE_VARIANT: Record<string, BadgeVariant> = {
  critical: "error",
  high: "warning",
  medium: "warning",
  low: "info",
  info: "primary", // Bleu pour les infos
};

interface FindingCardProps {
  finding: ScanFinding;
}

export default function FindingCard({ finding }: FindingCardProps) {
  const { t } = useLanguage();
  const severityVariant = SEVERITY_BADGE_VARIANT[finding.severity] ?? "info";

  return (
    <div className="py-4">
      <div className="mb-2 space-y-2">
        <h4 className="font-medium">{finding.title}</h4>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={severityVariant}>
            {t(getSeverityKey(finding.severity))}
          </Badge>
          {finding.owasp_categories?.map((code) => (
            <Badge key={code} variant="default" className="font-mono text-xs">
              {code}
            </Badge>
          ))}
          <span className="text-xs text-muted-theme">
            {t(getCategoryKey(finding.category))}
          </span>
        </div>
      </div>
      {finding.evidence && (
        <p className="mb-2 text-sm text-muted-theme">
          <span className="font-medium">{t("scanner.evidence")}:</span>{" "}
          {finding.evidence}
        </p>
      )}
      <div className="rounded-lg bg-[var(--color-surface-hover)] p-3">
        <p className="text-sm font-medium">{t("scanner.howToFix")}</p>
        <p className="mt-1 text-sm text-muted-theme">
          {finding.recommendation}
        </p>
        {finding.references.length > 0 && (
          <ul className="mt-2 space-y-1">
            {finding.references.map((ref) => (
              <li key={ref}>
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
