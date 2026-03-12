"use client";

import { useState, useCallback, useEffect } from "react";
import { useStepQueue } from "../../hooks/useStepQueue";
import { createPortal } from "react-dom";
import Link from "next/link";
import { AlertTriangle, FileText, Globe } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";
import { DropdownSelector, GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../ui/cards/Card";
import Modal from "../ui/Modal";
import CrawlValidationStep from "./CrawlValidationStep";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import MultiScanResults from "./MultiScanResults";
import ScanResultsGate from "./ScanResultsGate";
import ScannerHistoryAlertsSection from "./ScannerHistoryAlertsSection";
import FakeScanResultsBlurred from "./FakeScanResultsBlurred";
import { RecurrenceScheduleFields } from "../schedule";
import { Checkbox } from "../inputs";
import {
  runScan,
  runMultiScan,
  type ScanResult,
  type MultiScanResult,
  type ScanError,
} from "../../services/scanService";
import { runCrawl } from "../../services/crawlService";
import { useCrawlState } from "../../hooks/useCrawlState";
import { useAuthToken } from "../../hooks/useAuthToken";
import {
  createScheduledScan,
  getUserTimezone,
  type Frequency,
} from "../../services/scheduledScanService";
import { normalizeScanUrl } from "../../utils/scanUrl";
import {
  savePendingScanResult,
  consumePendingScanResult,
} from "../../utils/scanStorage";
import {
  saveMultiScan,
  saveScan,
  type ScanHistorySelection,
} from "../../services/scanHistoryService";
import {
  showErrorToast,
  showSuccessToast,
} from "../../utils/toastNotifications";

const FREQUENCY_OPTIONS = [
  { value: "daily" as const, labelKey: "scheduledScans.frequencyDaily" },
  { value: "weekly" as const, labelKey: "scheduledScans.frequencyWeekly" },
  { value: "monthly" as const, labelKey: "scheduledScans.frequencyMonthly" },
];

const DAYS_OF_WEEK = [
  { value: 0, labelKey: "scheduledScans.dayMonday" },
  { value: 1, labelKey: "scheduledScans.dayTuesday" },
  { value: 2, labelKey: "scheduledScans.dayWednesday" },
  { value: 3, labelKey: "scheduledScans.dayThursday" },
  { value: 4, labelKey: "scheduledScans.dayFriday" },
  { value: 5, labelKey: "scheduledScans.daySaturday" },
  { value: 6, labelKey: "scheduledScans.daySunday" },
];

function parseTimeToHourMinute(time: string): { hour: number; minute: number } {
  const [h, m] = (time || "00:00").split(":").map(Number);
  return { hour: h ?? 0, minute: m ?? 0 };
}

type ScanState =
  | "idle"
  | "crawling"
  | "validation"
  | "loading"
  | "success"
  | "error";

export default function ScannerContent() {
  const { t, lp } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuthUser({
    listenToAuthEvents: true,
  });
  const getToken = useAuthToken(isAuthenticated);
  const [url, setUrl] = useState("");
  const [state, setState] = useState<ScanState>("idle");
  const { steps, enqueueStep, resetSteps } = useStepQueue();
  const {
    steps: crawlSteps,
    enqueueStep: enqueueCrawlStep,
    resetSteps: resetCrawlSteps,
  } = useStepQueue();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [multiResult, setMultiResult] = useState<MultiScanResult | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [error, setError] = useState<ScanError | null>(null);
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [formFrequency, setFormFrequency] = useState<Frequency>("daily");
  const [formTime, setFormTime] = useState("02:00");
  const [formDayOfWeek, setFormDayOfWeek] = useState(0);
  const [formDayOfMonth, setFormDayOfMonth] = useState(15);
  const [formScanAlertsEnabled, setFormScanAlertsEnabled] = useState(true);
  const [saving, setSaving] = useState(false);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scanOnlyThisPage, setScanOnlyThisPage] = useState(true);
  const {
    crawl,
    setCrawlMode,
    setCrawlMaxUrls,
    setCrawlUrls,
    setCrawlResult,
    resetCrawlState,
  } = useCrawlState();

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const pending = consumePendingScanResult();
      if (pending) {
        setResult(pending);
        setState("success");
        // Sauvegarder dans l'historique (scan fait sans être connecté, puis connexion)
        saveScan(pending)
          .then((id) => {
            if (id) setScanId(id);
          })
          .catch(() => showErrorToast(t("scanner.saveFailed")));
      }
    }
  }, [authLoading, isAuthenticated, t]);

  const runScanOnUrl = useCallback(
    (urlToScan: string) => {
      setState("loading");
      resetSteps();
      setResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      runScan(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueStep(ev.data);
          } else if (ev.type === "result") {
            if (isAuthenticated) {
              setResult(ev.data);
              saveScan(ev.data)
                .then((id) => {
                  if (id) setScanId(id);
                })
                .catch(() => showErrorToast(t("scanner.saveFailed")));
              // Rester en loading : ScanLoader appelle onAnimationComplete à la fin
            } else {
              savePendingScanResult(ev.data);
              setResult(ev.data);
              setState("success");
            }
          } else if (ev.type === "save_done") {
            setScanId(ev.data.scan_id);
          } else if (ev.type === "error") {
            setError(ev.data);
            setState("error");
            setErrorModalOpen(true);
          } else if (ev.type === "save_failed") {
            showErrorToast(ev.data || t("scanner.saveFailed"));
          }
        },
        getToken,
      ).catch((err) => {
        setError({
          message:
            err instanceof Error ? err.message : t("scanner.errorGeneric"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [t, isAuthenticated, getToken, resetSteps, enqueueStep],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;
      const urlToScan = normalizeScanUrl(trimmed);
      setError(null);
      setErrorModalOpen(false);

      if (scanOnlyThisPage) {
        runScanOnUrl(urlToScan);
        return;
      }

      setState("crawling");
      resetCrawlSteps();
      runCrawl(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueCrawlStep(ev.data);
          } else if (ev.type === "result") {
            const urls =
              ev.data.urls.length > 0
                ? ev.data.urls
                : [{ url: urlToScan, depth: 0 }];
            setCrawlResult({ ...ev.data, urls }, crawl.mode);
            // Rester en crawling : ScanLoader appelle onAnimationComplete à la fin
          } else if (ev.type === "error") {
            setError({
              message: ev.data.message,
              status_code: ev.data.status_code,
              i18nKey: ev.data.i18nKey,
            });
            setState("error");
            setErrorModalOpen(true);
          }
        },
        crawl.maxUrls,
        crawl.mode,
      ).catch((err) => {
        setError({
          message: err instanceof Error ? err.message : t("scanner.crawlError"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [
      url,
      scanOnlyThisPage,
      runScanOnUrl,
      t,
      enqueueCrawlStep,
      resetCrawlSteps,
      setCrawlResult,
      crawl,
    ],
  );

  const runMultiScanOnUrls = useCallback(
    (urlsToScan: string[]) => {
      setState("loading");
      resetSteps();
      setResult(null);
      setMultiResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      runMultiScan(
        urlsToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueStep(ev.data);
          } else if (ev.type === "result") {
            setMultiResult(ev.data);
            if (isAuthenticated) {
              saveMultiScan(ev.data)
                .then((id) => {
                  if (id) setScanId(id);
                })
                .catch(() => showErrorToast(t("scanner.saveFailed")));
            }
            setState("success");
          } else if (ev.type === "error") {
            setError(ev.data);
            setState("error");
            setErrorModalOpen(true);
          }
        },
        getToken ?? (async () => null),
      ).catch((err) => {
        setError({
          message:
            err instanceof Error ? err.message : t("scanner.errorGeneric"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [isAuthenticated, t, getToken, resetSteps, enqueueStep],
  );

  const handleLaunchScanFromValidation = useCallback(() => {
    const urlStrings = crawl.urls.map((u) => u.url).filter(Boolean);
    if (urlStrings.length > 1) {
      runMultiScanOnUrls(urlStrings);
    } else {
      runScanOnUrl(normalizeScanUrl(url.trim()));
    }
  }, [url, crawl.urls, runScanOnUrl, runMultiScanOnUrls]);

  const handleScheduleFromValidation = useCallback(async () => {
    if (!isAuthenticated || authLoading) return;
    const urlStrings = crawl.urls.map((u) => u.url).filter(Boolean);
    if (urlStrings.length === 0) {
      showErrorToast(t("scheduledScans.urlRequired"));
      return;
    }

    const { hour, minute } = parseTimeToHourMinute(formTime);
    setSaving(true);
    try {
      const normalizedBaseUrl = normalizeScanUrl(url.trim() || urlStrings[0]);
      await createScheduledScan({
        url: normalizedBaseUrl,
        scan_type: "frontend",
        result_mode: urlStrings.length > 1 ? "multi" : "single",
        urls: urlStrings.length > 1 ? urlStrings : undefined,
        frequency: formFrequency,
        schedule_hour: hour,
        schedule_minute: minute,
        schedule_day_of_week:
          formFrequency === "weekly" ? formDayOfWeek : undefined,
        schedule_day_of_month:
          formFrequency === "monthly" ? formDayOfMonth : undefined,
        timezone: getUserTimezone(),
        scan_alerts_enabled: formScanAlertsEnabled,
      });
      showSuccessToast(t("scheduledScans.createSuccess"));
      setState("idle");
      resetCrawlState();
    } catch (err) {
      showErrorToast(
        err instanceof Error ? err.message : t("scheduledScans.createError"),
      );
    } finally {
      setSaving(false);
    }
  }, [
    authLoading,
    crawl.urls,
    formDayOfMonth,
    formDayOfWeek,
    formFrequency,
    formScanAlertsEnabled,
    formTime,
    isAuthenticated,
    resetCrawlState,
    t,
    url,
  ]);

  const handleBackFromValidation = useCallback(() => {
    setState("idle");
    resetCrawlState();
  }, [resetCrawlState]);

  const handleSelectScan = useCallback((selection: ScanHistorySelection) => {
    setScanId(selection.scan_id ?? null);
    if (selection.result_mode === "multi") {
      setMultiResult(selection.result);
      setResult(null);
    } else {
      setResult(selection.result);
      setMultiResult(null);
    }
    setState("success");
  }, []);

  const handleNewScan = useCallback(() => {
    setState("idle");
    resetSteps();
    resetCrawlSteps();
    setResult(null);
    setMultiResult(null);
    setScanId(null);
    setError(null);
    resetCrawlState();
  }, [resetCrawlState, resetSteps, resetCrawlSteps]);

  const handleAddScheduledScan = useCallback(async () => {
    if (!url.trim()) {
      showErrorToast(t("scheduledScans.urlRequired"));
      return;
    }
    const normalizedUrl = normalizeScanUrl(url);
    const { hour, minute } = parseTimeToHourMinute(formTime);
    setSaving(true);
    try {
      await createScheduledScan({
        url: normalizedUrl,
        scan_type: "frontend",
        frequency: formFrequency,
        schedule_hour: hour,
        schedule_minute: minute,
        schedule_day_of_week:
          formFrequency === "weekly" ? formDayOfWeek : undefined,
        schedule_day_of_month:
          formFrequency === "monthly" ? formDayOfMonth : undefined,
        timezone: getUserTimezone(),
        scan_alerts_enabled: formScanAlertsEnabled,
      });
      showSuccessToast(t("scheduledScans.createSuccess"));
    } catch (err) {
      showErrorToast(
        err instanceof Error ? err.message : t("scheduledScans.createError"),
      );
    } finally {
      setSaving(false);
    }
  }, [
    url,
    formFrequency,
    formTime,
    formDayOfWeek,
    formDayOfMonth,
    formScanAlertsEnabled,
    t,
  ]);

  const showHeader = state === "idle" || state === "error";
  const showScheduleValidationPopup = state === "validation" && scheduleEnabled;
  const showScannerForm =
    state === "idle" || state === "error" || showScheduleValidationPopup;

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
            <>
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
                      <Checkbox
                        label={t("scanner.scanOnlyThisPage")}
                        checked={scanOnlyThisPage}
                        onChange={(checked) => setScanOnlyThisPage(checked)}
                      />
                      {!scanOnlyThisPage && (
                        <div>
                          <label className="block text-sm font-medium text-[var(--text)] mb-2">
                            {t("scanner.crawlModeLabel")}
                          </label>
                          <DropdownSelector
                            selectedValue={crawl.mode}
                            onChange={(v) =>
                              setCrawlMode(v as "html" | "playwright" | "both")
                            }
                            options={[
                              {
                                value: "html",
                                label: t("scanner.crawlModeHtml"),
                              },
                              {
                                value: "playwright",
                                label: t("scanner.crawlModePlaywright"),
                              },
                              {
                                value: "both",
                                label: t("scanner.crawlModeBoth"),
                              },
                            ]}
                            width="100%"
                          />
                        </div>
                      )}
                      {!scanOnlyThisPage && (
                        <div>
                          <label
                            htmlFor="crawl-max-urls"
                            className="block text-sm font-medium text-[var(--text)] mb-1"
                          >
                            {t("scanner.crawlMaxUrlsLabel")}
                          </label>
                          <input
                            id="crawl-max-urls"
                            type="number"
                            min={5}
                            max={200}
                            value={crawl.maxUrls}
                            onChange={(e) => {
                              const v = parseInt(e.target.value, 10);
                              setCrawlMaxUrls(
                                Number.isNaN(v)
                                  ? 50
                                  : Math.min(200, Math.max(5, v)),
                              );
                            }}
                            className="auth-input w-24"
                            aria-describedby="crawl-max-urls-desc"
                          />
                          <span
                            id="crawl-max-urls-desc"
                            className="ml-2 text-sm text-[var(--muted)]"
                          >
                            {t("scanner.crawlMaxUrlsDesc")}
                          </span>
                        </div>
                      )}
                      {isAuthenticated && !authLoading && (
                        <Checkbox
                          label={t("scheduledScans.scheduleScanCheckbox")}
                          checked={scheduleEnabled}
                          onChange={(checked) => setScheduleEnabled(checked)}
                        />
                      )}
                      {scheduleEnabled && (
                        <>
                          <RecurrenceScheduleFields
                            frequencyLabelKey="scheduledScans.frequencyLabel"
                            timeLabelKey="scheduledScans.timeLabel"
                            dayOfWeekLabelKey="scheduledScans.dayOfWeekLabel"
                            dayOfMonthLabelKey="scheduledScans.dayOfMonthLabel"
                            frequencyOptions={FREQUENCY_OPTIONS}
                            daysOfWeek={DAYS_OF_WEEK}
                            frequency={formFrequency}
                            timeValue={formTime}
                            dayOfWeek={formDayOfWeek}
                            dayOfMonth={formDayOfMonth}
                            onFrequencyChange={setFormFrequency}
                            onTimeChange={setFormTime}
                            onDayOfWeekChange={setFormDayOfWeek}
                            onDayOfMonthChange={setFormDayOfMonth}
                            afterTimeSlot={
                              <Checkbox
                                label={
                                  <>
                                    <span className="block font-medium text-[var(--text)]">
                                      {t("scheduledScans.scanAlerts")}
                                    </span>
                                    <span className="text-xs text-[var(--muted)]">
                                      {t("scheduledScans.scanAlertsDesc")}
                                    </span>
                                  </>
                                }
                                checked={formScanAlertsEnabled}
                                onChange={(checked) =>
                                  setFormScanAlertsEnabled(checked)
                                }
                              />
                            }
                          />
                        </>
                      )}
                      <div className="flex gap-2 flex-wrap">
                        {scheduleEnabled &&
                        isAuthenticated &&
                        !authLoading &&
                        scanOnlyThisPage ? (
                          <GenericButton
                            type="button"
                            label={t("scheduledScans.scheduleBtn")}
                            variant="primary"
                            onClick={handleAddScheduledScan}
                            loading={saving}
                            disabled={!url.trim()}
                          />
                        ) : scheduleEnabled &&
                          isAuthenticated &&
                          !authLoading &&
                          !scanOnlyThisPage ? (
                          <GenericButton
                            type="submit"
                            label={t("scanner.cta")}
                            variant="primary"
                            disabled={!url.trim()}
                          />
                        ) : (
                          <GenericButton
                            type="submit"
                            label={t("scanner.cta")}
                            variant="primary"
                            disabled={!url.trim()}
                          />
                        )}
                      </div>
                    </form>
                  </div>
                </Card>
              </div>
            </>
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
                filterScanType="frontend"
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
                setError(null);
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
