"use client";

import { AlertTriangle } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import Card from "../ui/cards/Card";
import ScanResultHeroCard from "./ScanResultHeroCard";
import ScanSummarySection from "./ScanSummarySection";
import type { PageScanResult } from "../../services/scanService";

interface PageDetailProps {
  page: PageScanResult;
}

/** Vue détaillée d'une page : hero card, résumés de catégories et findings. */
export default function PageDetail({ page }: PageDetailProps) {
  const { t } = useLanguage();

  if (page.error) {
    return (
      <Card disableHover>
        <div className="flex items-center gap-2 rounded-lg border border-[rgb(var(--danger))]/30 bg-[rgb(var(--danger))]/5 px-4 py-3 text-sm text-[rgb(var(--danger))]">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>
            {t("scanner.multiPageError")} : {page.error}
          </span>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <ScanResultHeroCard
        url={page.url}
        score={page.score}
        findings={page.findings ?? []}
      />
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
