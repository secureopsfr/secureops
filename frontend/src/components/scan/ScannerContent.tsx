"use client";

import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, FileText, Globe } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";
import { useAuthToken } from "../../hooks/useAuthToken";
import { useScanFlow } from "../../hooks/useScanFlow";
import { useScheduleForm } from "../../hooks/useScheduleForm";
import AnimateInView from "../AnimateInView";
import { DropdownSelector, GenericButton } from "../buttons";
import Card from "../ui/cards/Card";
import Modal from "../ui/Modal";
import CrawlValidationStep from "./CrawlValidationStep";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import MultiScanResults from "./MultiScanResults";
import ScanResultsGate from "./ScanResultsGate";
import ScannerHistoryAlertsSection from "./ScannerHistoryAlertsSection";
import FakeScanResultsBlurred from "./FakeScanResultsBlurred";
import ScheduleFormSection from "./ScheduleFormSection";
import ScanTypeSelector from "./ScanTypeSelector";
import { normalizeScanUrl } from "../../utils/scanUrl";
import { resolveCrawlUrlsToScanUrls } from "../../utils/urlPathParams";
import { Checkbox } from "../inputs";

export default function ScannerContent() {
  const { t, lp } = useLanguage();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuthUser({
    listenToAuthEvents: true,
  });
  const getToken = useAuthToken(isAuthenticated);

  const {
    url,
    setUrl,
    scanTarget,
    setScanTarget,
    scanMode,
    setScanMode,
    scanOnlyThisPage,
    setScanOnlyThisPage,
    state,
    setState,
    steps,
    crawlSteps,
    result,
    multiResult,
    scanId,
    error,
    errorModalOpen,
    setErrorModalOpen,
    crawl,
    setCrawlMode,
    setCrawlMaxUrls,
    setCrawlUrls,
    resetCrawlState,
    handleSubmit,
    handleLaunchScanFromValidation,
    handleBackFromValidation,
    handleSelectScan,
    handleNewScan,
  } = useScanFlow({ isAuthenticated, authLoading, getToken, t });

  const { form, actions, saving, submitSchedule } = useScheduleForm(t);

  const [scheduleEnabled, setScheduleEnabled] = useState(false);

  useEffect(() => {
    const mode = searchParams.get("mode");
    if (!mode) return;
    if (
      mode === "passive" ||
      mode === "intrusive" ||
      mode === "destructive" ||
      mode === "custom"
    ) {
      setScanMode(mode);
    }
  }, [searchParams, setScanMode]);

  const handleAddScheduledScan = useCallback(async () => {
    if (!url.trim()) {
      return;
    }
    await submitSchedule({
      url: normalizeScanUrl(url),
      scan_type: scanTarget,
      scan_mode: scanMode,
    });
  }, [url, submitSchedule, scanTarget, scanMode]);

  const handleScheduleFromValidation = useCallback(async () => {
    if (!isAuthenticated || authLoading) return;
    const urlStrings = resolveCrawlUrlsToScanUrls(crawl.urls).filter(Boolean);
    if (urlStrings.length === 0) return;

    const normalizedBaseUrl = normalizeScanUrl(url.trim() || urlStrings[0]);
    const success = await submitSchedule({
      url: normalizedBaseUrl,
      scan_type: scanTarget,
      scan_mode: scanMode,
      result_mode: urlStrings.length > 1 ? "multi" : "single",
      urls: urlStrings.length > 1 ? urlStrings : undefined,
    });
    if (success) {
      setState("idle");
      resetCrawlState();
    }
  }, [
    authLoading,
    crawl.urls,
    isAuthenticated,
    resetCrawlState,
    setState,
    submitSchedule,
    scanTarget,
    scanMode,
    url,
  ]);

  const showHeader = state === "idle" || state === "error";
  const showScheduleValidationPopup = state === "validation" && scheduleEnabled;
  const showScannerForm =
    state === "idle" || state === "error" || showScheduleValidationPopup;

  const showScheduleBtn =
    scheduleEnabled && isAuthenticated && !authLoading && scanOnlyThisPage;

  return (
    <div className="space-y-4 w-full">
      {(showHeader || showScheduleValidationPopup) && (
        <AnimateInView
          initialOnly
          delay={80}
          className="page-section landing-reveal-page"
          as="section"
          aria-label={t("scanner.ariaHeader")}
        >
          <div className="page-container">
            <div className="page-header text-center mb-4">
              <h1 className="page-title mb-2">{t("scanner.title")}</h1>
              <p className="page-subtitle mt-0">{t("scanner.subtitle")}</p>
              <Link
                href={lp("/scanner/docs/scan-frontend")}
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
      )}

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="section"
        aria-label="Scanner content"
      >
        <div className="scanner-content">
          {showScannerForm && (
            <div className="w-full">
              <Card disableHover>
                <div className="flex items-center gap-3 mb-4 -mt-2">
                  <Globe className="w-6 h-6 text-[rgb(var(--primary))]" />
                  <h2 className="section-title !text-left !mb-0">
                    {t("scheduledScans.newScheduledScanTitle")}
                  </h2>
                </div>
                <div className="space-y-4">
                  <form
                    onSubmit={handleSubmit}
                    aria-label={t("scanner.ariaForm")}
                    className="space-y-4"
                  >
                    <label
                      htmlFor="scan-url"
                      className="block text-sm font-medium text-[var(--text)]"
                    >
                      {t("scheduledScans.urlLabel")}
                    </label>
                    <input
                      id="scan-url"
                      type="text"
                      inputMode="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder={t("scheduledScans.urlPlaceholder")}
                      required
                      className="auth-input w-full"
                    />
                    <div>
                      <label className="block text-sm font-medium text-[var(--text)] mb-2">
                        {t("scanner.targetLabel")}
                      </label>
                      <DropdownSelector
                        selectedValue={scanTarget}
                        onChange={(value) =>
                          setScanTarget(value as "frontend" | "backend")
                        }
                        options={[
                          {
                            value: "frontend",
                            label: t("scanner.targetFrontend"),
                          },
                          {
                            value: "backend",
                            label: t("scanner.targetBackend"),
                          },
                        ]}
                        width="100%"
                      />
                    </div>
                    <ScanTypeSelector
                      scanOnlyThisPage={scanOnlyThisPage}
                      onScanOnlyThisPageChange={(checked) => {
                        setScanOnlyThisPage(checked);
                        if (checked) resetCrawlState();
                      }}
                      scanTarget={scanTarget}
                      crawlMode={crawl.mode}
                      crawlMaxUrls={crawl.maxUrls}
                      onCrawlModeChange={setCrawlMode}
                      onCrawlMaxUrlsChange={setCrawlMaxUrls}
                      baseUrl={url.trim()}
                      apiDocUrls={crawl.urls}
                      onApiDocUrlsChange={setCrawlUrls}
                      t={t}
                    />
                    {isAuthenticated && !authLoading && (
                      <Checkbox
                        label={t("scheduledScans.scheduleScanCheckbox")}
                        checked={scheduleEnabled}
                        onChange={(checked) => setScheduleEnabled(checked)}
                      />
                    )}
                    {scheduleEnabled && (
                      <ScheduleFormSection
                        form={form}
                        actions={actions}
                        t={t}
                      />
                    )}
                    <div className="flex gap-2 flex-wrap">
                      {showScheduleBtn ? (
                        <GenericButton
                          type="button"
                          label={t("scheduledScans.scheduleBtn")}
                          variant="primary"
                          onClick={handleAddScheduledScan}
                          loading={saving}
                          disabled={!url.trim()}
                        />
                      ) : scanTarget === "backend" &&
                        !scanOnlyThisPage &&
                        crawl.urls.length > 0 ? (
                        <GenericButton
                          type="button"
                          label={t("scanner.cta")}
                          variant="primary"
                          onClick={handleLaunchScanFromValidation}
                          disabled={crawl.urls.length > 200}
                        />
                      ) : (
                        <GenericButton
                          type="submit"
                          label={t("scanner.cta")}
                          variant="primary"
                          disabled={
                            !url.trim() ||
                            (scanTarget === "backend" && !scanOnlyThisPage)
                          }
                        />
                      )}
                    </div>
                  </form>
                </div>
              </Card>
            </div>
          )}

          {state === "crawling" &&
            (typeof document !== "undefined"
              ? createPortal(
                  <div className="scan-loading-overlay fixed inset-0 z-[60]">
                    <ScanLoader
                      steps={crawlSteps}
                      titleKey="scanner.crawlLoading"
                      crawlMode={crawl.mode}
                      onAnimationComplete={
                        crawl.urls.length > 0
                          ? () => setState("validation")
                          : undefined
                      }
                    />
                  </div>,
                  document.body,
                )
              : null)}

          {(state === "validation" || showScheduleValidationPopup) &&
            (() => {
              const validationProps = {
                urls: crawl.urls,
                identifiedCount: crawl.identifiedCount,
                startUrl: url.trim(),
                allowFullUrlAdd: scanTarget === "backend",
                timeoutReached: crawl.timeoutReached,
                timeoutHtml: crawl.timeoutHtml,
                timeoutPlaywright: crawl.timeoutPlaywright,
                antiBotSignatureDetected: crawl.antiBotSignatureDetected,
                antiBotLowUrlSuspected: crawl.antiBotLowUrlSuspected,
                requestsBlocked: crawl.requestsBlocked,
                requestsBlockedHtml: crawl.requestsBlockedHtml,
                requestsBlockedPlaywright: crawl.requestsBlockedPlaywright,
                maxConsecutive403: crawl.maxConsecutive403,
                disallowPaths: crawl.disallowPaths,
                onUrlsChange: setCrawlUrls,
                onBack: handleBackFromValidation,
              };

              const inner =
                state === "validation" && !scheduleEnabled ? (
                  <CrawlValidationStep
                    {...validationProps}
                    onLaunchScan={handleLaunchScanFromValidation}
                    launchButtonLabelKey="scanner.launchScanFromList"
                    showFloatingBackAction={false}
                  />
                ) : showScheduleValidationPopup ? (
                  <CrawlValidationStep
                    {...validationProps}
                    onLaunchScan={handleScheduleFromValidation}
                    launchButtonLabelKey="scheduledScans.scheduleBtn"
                    showFloatingBackAction={false}
                    compact
                  />
                ) : null;

              if (!inner) return null;

              if (
                showScheduleValidationPopup &&
                typeof document !== "undefined"
              ) {
                return createPortal(
                  <div
                    className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
                    style={{
                      backgroundColor: "var(--color-overlay)",
                      backdropFilter: "blur(4px)",
                      WebkitBackdropFilter: "blur(4px)",
                    }}
                    onClick={handleBackFromValidation}
                  >
                    <div
                      className="w-full max-w-4xl"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {inner}
                    </div>
                  </div>,
                  document.body,
                );
              }
              return inner;
            })()}

          {state === "loading" &&
            (typeof document !== "undefined"
              ? createPortal(
                  <div className="scan-loading-overlay fixed inset-0 z-[60]">
                    <ScanLoader
                      steps={steps}
                      crawlMode={scanOnlyThisPage ? undefined : crawl.mode}
                      onAnimationComplete={
                        result ? () => setState("success") : undefined
                      }
                    />
                  </div>,
                  document.body,
                )
              : null)}

          {(state === "idle" || state === "error") &&
            isAuthenticated &&
            !authLoading && (
              <ScannerHistoryAlertsSection
                className="mt-6"
                onSelectScan={handleSelectScan}
                filterScanType={scanTarget}
                filterScanMode={scanMode}
              />
            )}

          {state === "success" &&
            multiResult &&
            isAuthenticated &&
            !authLoading && (
              <MultiScanResults
                result={multiResult}
                scanId={scanId}
                onNewScan={handleNewScan}
              />
            )}

          {state === "success" &&
            result &&
            !multiResult &&
            !authLoading &&
            (isAuthenticated ? (
              <ScanResults
                result={result}
                scanId={scanId}
                onNewScan={handleNewScan}
              />
            ) : (
              <>
                <FakeScanResultsBlurred />
                <Modal
                  isOpen
                  onClose={() => {}}
                  title={t("scanner.gateTitle")}
                  maxWidth="420px"
                  showCloseButton={false}
                  closeOnBackdropClick={false}
                >
                  <ScanResultsGate
                    signInHref={`${lp("/connexion")}?returnTo=${encodeURIComponent(lp("/scanner"))}`}
                  />
                </Modal>
              </>
            ))}

          {state === "error" && error && (
            <Modal
              isOpen={errorModalOpen}
              onClose={() => setErrorModalOpen(false)}
              onExited={() => {
                setState("idle");
              }}
              title={
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-[rgb(var(--danger))]" />
                  <span>{t("scanner.errorTitle")}</span>
                </div>
              }
              maxWidth="500px"
            >
              <p className="text-[var(--text)] leading-relaxed">
                {error.i18nKey ? t(error.i18nKey) : error.message}
              </p>
            </Modal>
          )}
        </div>
      </AnimateInView>
    </div>
  );
}
