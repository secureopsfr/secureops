"use client";

import { useCallback, useState, useEffect } from "react";
import {
  Download,
  FileSpreadsheet,
  FileJson,
  FileText,
  FileOutput,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import AnimateInView from "../AnimateInView";
import Card from "../ui/cards/Card";
import Modal from "../ui/Modal";
import ScanResultHeroCard from "./ScanResultHeroCard";
import ScanSummarySection from "./ScanSummarySection";
import FloatingActionDock from "./FloatingActionDock";
import type { ScanResult } from "../../services/scanService";
import { severitySort } from "./scanConstants";
import { exportScanResult, type ExportFormat } from "../../utils/exportScan";
import { formatUrlDisplay } from "../../utils/urlFormat";
import { downloadScanPdf } from "../../services/scanHistoryService";
import { showErrorToast } from "../../utils/toastNotifications";
import { LoadingSpinner } from "../LoadingScreen";

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

export default function ScanResults({
  result,
  scanId,
  onNewScan,
}: ScanResultsProps) {
  const { t, language } = useLanguage();
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
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

  return (
    <div className="space-y-6">
      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <ScanResultHeroCard
          url={result.url}
          score={result.score}
          findings={sortedFindings}
          durationSeconds={result.duration}
        />
      </AnimateInView>

      <ScanSummarySection
        findings={result.findings}
        category_summaries={result.category_summaries}
        total_tests_count={result.total_tests_count}
      />

      <FloatingActionDock
        ariaLabel={t("scanner.export")}
        actions={[
          {
            key: "new-scan",
            label: t("scanner.newScan"),
            variant: "outline",
            onClick: onNewScan,
          },
          {
            key: "export",
            label: t("scanner.export"),
            variant: "primary",
            icon: <Download className="w-4 h-4" />,
            iconPosition: "left",
            onClick: () => setExportModalOpen(true),
          },
        ]}
      />

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
                {isPdf && pdfLoading ? <LoadingSpinner size="sm" /> : icon}
                <span className="font-medium">
                  {isPdf && pdfLoading
                    ? t("scanner.exportPdfGenerating")
                    : t(labelKey)}
                </span>
                {disabled && !pdfLoading && (
                  <span className="text-xs text-muted-theme ml-auto">
                    {t("scanner.exportPdfUnavailable")}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </Modal>
    </div>
  );
}
