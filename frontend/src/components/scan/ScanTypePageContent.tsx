"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useStepQueue } from "../../hooks/useStepQueue";
import { createPortal } from "react-dom";
import Link from "next/link";
import { FileText } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import AnimateInView from "../AnimateInView";
import ScannerHistoryAlertsSection from "./ScannerHistoryAlertsSection";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import ScanLaunchBubble from "./ScanLaunchBubble";
import type { ScanHistorySelection } from "../../services/scanHistoryService";
import {
  runAsyncScan,
  type AsyncScanMode,
  type ScanResult,
} from "../../services/scanService";
import { normalizeScanUrl } from "../../utils/scanUrl";
import { useAuthToken } from "../../hooks/useAuthToken";

interface ScanTypePageContentProps {
  /** Clé i18n pour le titre (ex. scanner.backend.title). */
  titleKey: string;
  /** Clé i18n pour le placeholder/description. */
  placeholderKey: string;
  /** Slug du document (ex. scan-backend, scans-personnalises). */
  docSlug: string;
  /** Type de scan pour filtrer les blocs. */
  filterScanType: "frontend" | "backend";
}

export default function ScanTypePageContent({
  titleKey,
  placeholderKey,
  docSlug,
  filterScanType,
}: ScanTypePageContentProps) {
  const { t, lp } = useLanguage();
  const getToken = useAuthToken(true);
  const [url, setUrl] = useState("");
  const scanTarget = filterScanType;
  const scanMode: AsyncScanMode = "passive";
  const [selectedResult, setSelectedResult] = useState<ScanResult | null>(null);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const { steps, enqueueStep, resetSteps } = useStepQueue();
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleSelectScan = (selection: ScanHistorySelection) => {
    if (selection.result_mode !== "single") return;
    setSelectedResult(selection.result);
    setSelectedScanId(selection.scan_id ?? null);
  };

  const handleNewScan = () => {
    setSelectedResult(null);
    setSelectedScanId(null);
    resetSteps();
    setFormError(null);
    setIsLoading(false);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim() || isLoading) return;

    setFormError(null);
    resetSteps();
    setIsLoading(true);
    const urlToScan = normalizeScanUrl(url.trim());

    try {
      await runAsyncScan(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueStep(ev.data);
            return;
          }

          if (ev.type === "result") {
            setSelectedResult(ev.data);
            setIsLoading(false);
            return;
          }

          if (ev.type === "error") {
            setIsLoading(false);
            setFormError(ev.data.message || t("scanner.errorGeneric"));
          }
        },
        {
          scanType: scanTarget,
          scanMode,
          input: {},
          logPrefix: `[scan-${scanTarget}-${scanMode}-polling]`,
        },
        getToken,
      );
    } catch (err) {
      setIsLoading(false);
      setFormError(
        err instanceof Error ? err.message : t("scanner.errorGeneric"),
      );
    }
  };

  if (selectedResult) {
    return (
      <ScanResults
        result={selectedResult}
        scanId={selectedScanId}
        onNewScan={handleNewScan}
      />
    );
  }

  return (
    <>
      <AnimateInView
        initialOnly
        delay={80}
        className="page-section landing-reveal-page"
        as="section"
        aria-label={t("scanner.ariaHeader")}
      >
        <div className="page-container">
          <div className="page-header text-center mb-4">
            <h1 className="page-title mb-2">{t(titleKey)}</h1>
            <p className="page-subtitle mt-0">{t(placeholderKey)}</p>
            <Link
              href={lp(`/scanner/docs/${docSlug}`)}
              target="_blank"
              rel="noopener noreferrer"
              className="group mt-2 inline-flex text-sm text-[rgb(var(--primary))] no-underline"
            >
              <span className="inline-flex items-center gap-1.5 border-b-2 border-transparent group-hover:border-[rgb(var(--primary))]">
                <FileText className="w-4 h-4" />
                {t("scanner.docsLink")}
              </span>
            </Link>
          </div>
        </div>
      </AnimateInView>

      <div className="mb-6">
        <ScanLaunchBubble
          url={url}
          onUrlChange={setUrl}
          scanTarget={scanTarget}
          onScanTargetChange={() => {}}
          showTargetSelector={false}
          onSubmit={handleSubmit}
          loading={isLoading}
        />
        {formError ? (
          <p className="mt-3 text-sm text-[rgb(var(--danger))] text-center">
            {formError}
          </p>
        ) : null}
      </div>

      <ScannerHistoryAlertsSection
        onSelectScan={handleSelectScan}
        filterScanType={filterScanType}
        filterScanMode={scanMode}
      />

      {isLoading &&
        typeof window !== "undefined" &&
        createPortal(
          <div className="scan-loading-overlay fixed inset-0 z-[60]">
            <ScanLoader steps={steps} />
          </div>,
          document.body,
        )}
    </>
  );
}
