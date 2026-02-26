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

/** Icône globe SVG vectorielle pour fallback favicon (évite la pixellisation). */
const DefaultFavicon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-8 w-8 text-[var(--muted)]"
    aria-hidden
  >
    <circle cx="12" cy="12" r="10" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    <path d="M2 12h20" />
  </svg>
);

const EXPORT_BUTTON_BOTTOM_DEFAULT = 20;
/** Hauteur fixe au-dessus du footer quand il est visible (footer ~200px + marge). */
const EXPORT_BUTTON_BOTTOM_ABOVE_FOOTER = 220;

export default function ScanResults({ result, onNewScan }: ScanResultsProps) {
  const { t } = useLanguage();
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [faviconError, setFaviconError] = useState(false);

  useEffect(() => {
    setFaviconError(false);
  }, [result.url]);
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

  const displayUrl =
    result.url.replace(/^https?:\/\//, "").replace(/\/$/, "") || result.url;

  const domain = (() => {
    try {
      return new URL(result.url).hostname;
    } catch {
      return displayUrl.split("/")[0] || displayUrl;
    }
  })();

  const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;

  return (
    <div className="space-y-6">
      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="div"
      >
        <Card
          disableHover
          className="scanner-block overflow-hidden border-2 border-[var(--color-border)]"
        >
          <div className="p-6 sm:p-8 text-center">
            <div className="mb-4 flex justify-center">
              {faviconError ? (
                <div
                  className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-surface-hover)]"
                  aria-hidden
                >
                  <DefaultFavicon />
                </div>
              ) : (
                <img
                  src={faviconUrl}
                  alt=""
                  className="h-14 w-14 rounded-xl object-cover"
                  onError={() => setFaviconError(true)}
                />
              )}
            </div>
            <h2
              className="text-xl sm:text-2xl lg:text-3xl font-bold text-[var(--text)] break-all"
              title={result.url}
            >
              {displayUrl}
            </h2>
            <p className="text-xs sm:text-sm text-muted-theme mt-2">
              {t("scanner.duration")} {result.duration.toFixed(1)}
              {t("scanner.seconds")}
            </p>
            <div className="mt-6 flex flex-col items-center gap-2">
              <div
                className="relative flex h-20 w-20 flex-shrink-0 sm:h-24 sm:w-24"
                aria-hidden
              >
                <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke="var(--color-surface-hover)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke={badge.ringColor}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 42}
                    strokeDashoffset={
                      2 * Math.PI * 42 * (1 - result.score / 100)
                    }
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-[var(--text)] sm:text-3xl">
                  {result.score}
                </span>
              </div>
              <p className="text-base font-medium text-[var(--muted)]">
                {t(badge.labelKey)}
              </p>
            </div>
            <p className="mt-4 text-sm text-muted-theme">
              {t("scanner.findings")} ({sortedFindings.length})
            </p>
            {Object.keys(byCategory).length > 0 && (
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {Object.entries(byCategory).map(([cat, count]) => (
                  <Badge key={cat} variant="default" className="text-sm">
                    {t(getCategoryKey(cat))}: {count}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </Card>
      </AnimateInView>

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
            className="fixed right-6 z-[9998] flex items-center gap-2 shadow-lg transition-all duration-200"
            style={{ position: "fixed", bottom: exportButtonBottom }}
            aria-label={t("scanner.export")}
          >
            <GenericButton
              label={t("scanner.newScan")}
              variant="outline"
              onClick={onNewScan}
            />
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
