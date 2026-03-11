"use client";

import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { fetchAuthSession } from "aws-amplify/auth";
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
  type ScanStepDisplay,
} from "../../services/scanService";
import { runCrawl, type CrawlUrlEntry } from "../../services/crawlService";
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
import { saveScan } from "../../services/scanHistoryService";
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
  const [url, setUrl] = useState("");
  const [state, setState] = useState<ScanState>("idle");
  const [steps, setSteps] = useState<ScanStepDisplay[]>([]);
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
  const [crawlMode, setCrawlMode] = useState<"html" | "playwright" | "both">(
    "html",
  );
  const [crawlMaxUrls, setCrawlMaxUrls] = useState(50);
  const [crawledUrls, setCrawledUrls] = useState<CrawlUrlEntry[]>([]);
  const [crawlTimeoutReached, setCrawlTimeoutReached] = useState(false);
  const [crawlAntiBotSuspected, setCrawlAntiBotSuspected] = useState(false);
  const [crawlRequestsBlocked, setCrawlRequestsBlocked] = useState(false);
  const [crawlDisallowPaths, setCrawlDisallowPaths] = useState<string[]>([]);
  const [crawlSteps, setCrawlSteps] = useState<ScanStepDisplay[]>([]);

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
      setSteps([]);
      setResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      const getToken = isAuthenticated
        ? async () => {
            try {
              const session = await fetchAuthSession();
              return session.tokens?.accessToken?.toString() ?? null;
            } catch {
              return null;
            }
          }
        : undefined;

      runScan(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            const done = ev.data.step.endsWith("_done");
            setSteps((prev) => {
              if (done && prev.length > 0) {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: true,
                  anomaly_count: ev.data.anomaly_count,
                };
                return updated;
              }
              return [
                ...prev,
                {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: false,
                  anomaly_count: ev.data.anomaly_count,
                },
              ];
            });
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
    [t, isAuthenticated],
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
      setCrawlSteps([]);
      runCrawl(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            const step = ev.data.step;
            const done = step.endsWith("_done");
            const isCrawlMerging = step === "crawl_merging";
            const isCrawlStoppingOther = step === "crawl_stopping_other";
            const isCrawlProgress =
              step === "crawl_progress" ||
              step === "html_crawl_progress" ||
              step === "playwright_crawl_progress";
            setCrawlSteps((prev) => {
              if (isCrawlStoppingOther && prev.length > 0) {
                const lastDone = prev.findLastIndex((s) =>
                  ["crawl_html_done", "crawl_playwright_done"].includes(s.step),
                );
                const branchToReplace =
                  lastDone >= 0 && prev[lastDone]?.step === "crawl_html_done"
                    ? "playwright"
                    : "html";
                const targetStep =
                  branchToReplace === "playwright"
                    ? "playwright_crawl_progress"
                    : "html_crawl_progress";
                const idx = prev.findLastIndex((s) => s.step === targetStep);
                if (idx >= 0) {
                  const updated = [...prev];
                  updated[idx] = {
                    step: "crawl_stopping_other",
                    message: ev.data.message,
                    done: false,
                  };
                  return updated;
                }
              }
              if (isCrawlMerging && prev.length > 0) {
                const updated = [...prev];
                const stopIdx = updated.findLastIndex(
                  (s) => s.step === "crawl_stopping_other",
                );
                if (stopIdx >= 0) {
                  updated[stopIdx] = {
                    step: updated[stopIdx].step,
                    message: updated[stopIdx].message,
                    done: true,
                  };
                }
                return [
                  ...updated,
                  {
                    step: ev.data.step,
                    message: ev.data.message,
                    done: false,
                  },
                ];
              }
              if (done && prev.length > 0) {
                const updated = [...prev];
                const checkStep = step.replace("_done", "_check");
                const idx = updated.findLastIndex((s) => s.step === checkStep);
                if (idx >= 0) {
                  updated[idx] = {
                    step: updated[idx].step,
                    message: ev.data.message,
                    done: true,
                  };
                } else {
                  updated[updated.length - 1] = {
                    step: prev[prev.length - 1].step,
                    message: ev.data.message,
                    done: true,
                  };
                }
                return updated;
              }
              if (isCrawlProgress && prev.length > 0) {
                const lastIdx = prev.findLastIndex((s) => s.step === step);
                if (lastIdx >= 0) {
                  const updated = [...prev];
                  updated[lastIdx] = {
                    step: ev.data.step,
                    message: ev.data.message,
                    done: false,
                  };
                  return updated;
                }
              }
              return [
                ...prev,
                {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: false,
                },
              ];
            });
          } else if (ev.type === "result") {
            const urls =
              ev.data.urls.length > 0
                ? ev.data.urls
                : [{ url: urlToScan, type: "page", depth: 0 }];
            setCrawledUrls(urls);
            setCrawlTimeoutReached(ev.data.timeout_reached ?? false);
            setCrawlAntiBotSuspected(ev.data.anti_bot_suspected ?? false);
            setCrawlRequestsBlocked(ev.data.requests_blocked ?? false);
            setCrawlDisallowPaths(ev.data.disallow_paths ?? []);
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
        crawlMaxUrls,
        crawlMode,
      ).catch((err) => {
        setError({
          message: err instanceof Error ? err.message : t("scanner.crawlError"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [url, scanOnlyThisPage, crawlMaxUrls, crawlMode, runScanOnUrl, t],
  );

  const runMultiScanOnUrls = useCallback(
    (urlsToScan: string[]) => {
      setState("loading");
      setSteps([]);
      setResult(null);
      setMultiResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      const getToken = async () => {
        try {
          const session = await fetchAuthSession();
          return session.tokens?.accessToken?.toString() ?? null;
        } catch {
          return null;
        }
      };

      runMultiScan(
        urlsToScan,
        (ev) => {
          if (ev.type === "step") {
            const done = ev.data.step.endsWith("_done");
            setSteps((prev) => {
              if (done && prev.length > 0) {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: true,
                };
                return updated;
              }
              return [
                ...prev,
                { step: ev.data.step, message: ev.data.message, done: false },
              ];
            });
          } else if (ev.type === "result") {
            setMultiResult(ev.data);
            setState("success");
          } else if (ev.type === "error") {
            setError(ev.data);
            setState("error");
            setErrorModalOpen(true);
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
    [t],
  );

  const handleLaunchScanFromValidation = useCallback(() => {
    const urlStrings = crawledUrls.map((u) => u.url).filter(Boolean);
    if (urlStrings.length > 1) {
      runMultiScanOnUrls(urlStrings);
    } else {
      runScanOnUrl(normalizeScanUrl(url.trim()));
    }
  }, [url, crawledUrls, runScanOnUrl, runMultiScanOnUrls]);

  const handleBackFromValidation = useCallback(() => {
    setState("idle");
    setCrawledUrls([]);
    setCrawlTimeoutReached(false);
    setCrawlAntiBotSuspected(false);
    setCrawlRequestsBlocked(false);
    setCrawlDisallowPaths([]);
    setCrawlSteps([]);
  }, []);

  const handleSelectScan = useCallback((r: ScanResult, id?: string) => {
    setResult(r);
    setScanId(id ?? null);
    setState("success");
  }, []);

  const handleNewScan = useCallback(() => {
    setState("idle");
    setSteps([]);
    setResult(null);
    setMultiResult(null);
    setScanId(null);
    setError(null);
    setCrawledUrls([]);
    setCrawlTimeoutReached(false);
    setCrawlAntiBotSuspected(false);
    setCrawlRequestsBlocked(false);
    setCrawlDisallowPaths([]);
  }, []);

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

  const showHeader =
    state === "idle" || state === "error" || state === "validation";

  return (
    <div className="space-y-4 w-full">
      {showHeader && (
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
          {(state === "idle" || state === "error") && (
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
                            selectedValue={crawlMode}
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
                            value={crawlMaxUrls}
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
                        {scheduleEnabled && isAuthenticated && !authLoading ? (
                          <GenericButton
                            type="button"
                            label={t("scheduledScans.scheduleBtn")}
                            variant="primary"
                            onClick={handleAddScheduledScan}
                            loading={saving}
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
                      crawlMode={crawlMode}
                      onAnimationComplete={
                        crawledUrls.length > 0
                          ? () => setState("validation")
                          : undefined
                      }
                    />
                  </div>,
                  document.body,
                )
              : null)}

          {state === "validation" && (
            <CrawlValidationStep
              urls={crawledUrls}
              startUrl={url.trim()}
              timeoutReached={crawlTimeoutReached}
              antiBotSuspected={crawlAntiBotSuspected}
              requestsBlocked={crawlRequestsBlocked}
              disallowPaths={crawlDisallowPaths}
              onUrlsChange={setCrawledUrls}
              onLaunchScan={handleLaunchScanFromValidation}
              onBack={handleBackFromValidation}
            />
          )}

          {state === "loading" &&
            (typeof document !== "undefined"
              ? createPortal(
                  <div className="scan-loading-overlay fixed inset-0 z-[60]">
                    <ScanLoader
                      steps={steps}
                      crawlMode={scanOnlyThisPage ? undefined : crawlMode}
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
