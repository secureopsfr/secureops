"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileText } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import ScannerHistoryAlertsSection from "./ScannerHistoryAlertsSection";
import ScanResults from "./ScanResults";
import type { ScanResult } from "../../services/scanService";

interface ScanTypePageContentProps {
  /** Clé i18n pour le titre (ex. scanner.backend.title). */
  titleKey: string;
  /** Clé i18n pour le placeholder/description. */
  placeholderKey: string;
  /** Slug du document (ex. scan-backend, scans-personnalises). */
  docSlug: string;
  /** Type de scan pour filtrer les blocs (backend ou custom). */
  filterScanType: "backend" | "custom";
}

export default function ScanTypePageContent({
  titleKey,
  placeholderKey,
  docSlug,
  filterScanType,
}: ScanTypePageContentProps) {
  const { t, lp } = useLanguage();
  const router = useRouter();
  const [selectedResult, setSelectedResult] = useState<ScanResult | null>(null);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);

  const handleSelectScan = (result: ScanResult, id?: string) => {
    setSelectedResult(result);
    setSelectedScanId(id ?? null);
  };

  const handleNewScan = () => {
    setSelectedResult(null);
    setSelectedScanId(null);
    router.push(lp("/scanner/analyses"));
  };

  if (selectedResult) {
    return (
      <ScanResults
        result={selectedResult}
        scanId={selectedScanId}
        onNewScan={handleNewScan}
        onSelectScan={handleSelectScan}
        filterScanType={filterScanType}
      />
    );
  }

  return (
    <>
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center mb-6">
        <h1 className="page-title mb-4">{t(titleKey)}</h1>
        <p className="text-[var(--color-text-muted)] max-w-xl mx-auto">
          {t(placeholderKey)}
        </p>
        <Link
          href={lp(`/scanner/docs/${docSlug}`)}
          className="group mt-4 inline-flex text-sm text-[rgb(var(--primary))] no-underline"
        >
          <span className="inline-flex items-center gap-1.5 border-b-2 border-transparent group-hover:border-[rgb(var(--primary))]">
            <FileText className="w-4 h-4" />
            {t("scanner.docsLink")}
          </span>
        </Link>
      </div>

      <ScannerHistoryAlertsSection
        onSelectScan={handleSelectScan}
        filterScanType={filterScanType}
      />
    </>
  );
}
