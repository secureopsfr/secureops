"use client";

import { useCallback, useMemo, useState } from "react";
import {
  Download,
  FileSpreadsheet,
  FileJson,
  FileText,
  FileOutput,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import AnimateInView from "../AnimateInView";
import ScanResultHeroCard from "./ScanResultHeroCard";
import ScanSummarySection from "./ScanSummarySection";
import FloatingActionDock from "./FloatingActionDock";
import ExportModal from "./ExportModal";
import type { ScanResult } from "../../services/scanService";
import { severitySort } from "./scanConstants";
import { exportScanResult, type ExportFormat } from "../../utils/exportScan";
import { downloadScanPdf } from "../../services/scanHistoryService";
import { showErrorToast } from "../../utils/toastNotifications";

interface ScanResultsProps {
  result: ScanResult;
  scanId: string | null;
  onNewScan: () => void;
}

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
    async (format: string) => {
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
        exportScanResult(result, format as ExportFormat);
        setExportModalOpen(false);
      }
    },
    [result, scanId, language, t],
  );

  const exportFormats = useMemo(
    () => [
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
        disabled: !scanId || pdfLoading,
        disabledHintKey: "scanner.exportPdfUnavailable" as const,
        isLoading: pdfLoading,
        loadingLabelKey: "scanner.exportPdfGenerating" as const,
      },
    ],
    [scanId, pdfLoading],
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

      <ExportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        formats={exportFormats}
        onExport={handleExport}
        t={t}
      />
    </div>
  );
}
