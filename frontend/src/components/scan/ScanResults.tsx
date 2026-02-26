"use client";

import { useCallback, useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Download, FileSpreadsheet, FileJson, FileText } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../cards/Card";
import Badge from "../Badge";
import Modal from "../Modal";
import FindingCard from "./FindingCard";
import type { ScanResult } from "../../services/scanService";
import { getScoreBadge, getCategoryKey, severitySort } from "./scanConstants";
import { exportScanResult, type ExportFormat } from "../../utils/exportScan";

interface ScanResultsProps {
  result: ScanResult;
  onNewScan: () => void;
}

const EXPORT_FORMATS: {
  value: ExportFormat;
  labelKey: string;
  icon: React.ReactNode;
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
];

const EXPORT_BUTTON_BOTTOM_DEFAULT = 24;
/** Hauteur fixe au-dessus du footer quand il est visible (footer ~200px + marge). */
const EXPORT_BUTTON_BOTTOM_ABOVE_FOOTER = 240;

export default function ScanResults({ result, onNewScan }: ScanResultsProps) {
  const { t } = useLanguage();
  const [exportModalOpen, setExportModalOpen] = useState(false);
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
    (format: ExportFormat) => {
      exportScanResult(result, format);
      setExportModalOpen(false);
    },
    [result],
  );

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

      {typeof document !== "undefined" &&
        createPortal(
          <div
            className="fixed right-6 z-[9998] shadow-lg transition-all duration-200"
            style={{ position: "fixed", bottom: exportButtonBottom }}
            aria-label={t("scanner.export")}
          >
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
          {EXPORT_FORMATS.map(({ value, labelKey, icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => handleExport(value)}
              className="flex items-center gap-3 w-full p-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] hover:bg-[var(--color-surface-hover)] transition-colors text-left"
            >
              {icon}
              <span className="font-medium">{t(labelKey)}</span>
            </button>
          ))}
        </div>
      </Modal>
    </div>
  );
}
