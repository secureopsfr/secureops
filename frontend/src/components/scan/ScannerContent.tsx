"use client";

import { useState, useCallback, useEffect } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import { AlertTriangle, Globe } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../ui/cards/Card";
import Modal from "../ui/Modal";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import ScanResultsGate from "./ScanResultsGate";
import FakeScanResultsBlurred from "./FakeScanResultsBlurred";
import ScanHistoryBlock from "./ScanHistoryBlock";
import ScheduledScansBlock from "./ScheduledScansBlock";
import AlertHistoryBlock from "./AlertHistoryBlock";
import { RecurrenceScheduleFields } from "../schedule";
import { Checkbox } from "../inputs";
import {
  runScan,
  type ScanResult,
  type ScanError,
  type ScanStepDisplay,
} from "../../services/scanService";
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

type ScanState = "idle" | "loading" | "success" | "error";

export default function ScannerContent() {
  const { t, lp } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuthUser({
    listenToAuthEvents: true,
  });
  const [url, setUrl] = useState("");
  const [state, setState] = useState<ScanState>("idle");
  const [steps, setSteps] = useState<ScanStepDisplay[]>([]);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [error, setError] = useState<ScanError | null>(null);
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [scheduleRefreshTrigger, setScheduleRefreshTrigger] = useState(0);
  const [formFrequency, setFormFrequency] = useState<Frequency>("daily");
  const [formTime, setFormTime] = useState("02:00");
  const [formDayOfWeek, setFormDayOfWeek] = useState(0);
  const [formDayOfMonth, setFormDayOfMonth] = useState(15);
  const [formScanAlertsEnabled, setFormScanAlertsEnabled] = useState(true);
  const [saving, setSaving] = useState(false);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);

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

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;
      const urlToScan = normalizeScanUrl(trimmed);
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

      try {
        await runScan(
          urlToScan,
          (ev) => {
            if (ev.type === "step") {
              const done = ev.data.step.endsWith("_done");
              setSteps((prev) => {
                if (done && prev.length > 0) {
                  // Remplace la dernière ligne (en chargement) par la version terminée
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
                  {
                    step: ev.data.step,
                    message: ev.data.message,
                    done: false,
                  },
                ];
              });
            } else if (ev.type === "result") {
              if (isAuthenticated) {
                setResult(ev.data);
                setState("success");
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
        );
      } catch (err) {
        setError({
          message:
            err instanceof Error ? err.message : t("scanner.errorGeneric"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      }
    },
    [url, t, isAuthenticated],
  );

  const handleNewScan = useCallback(() => {
    setState("idle");
    setSteps([]);
    setResult(null);
    setScanId(null);
    setError(null);
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
      setScheduleRefreshTrigger((n) => n + 1);
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
              {isAuthenticated && !authLoading && (
                <>
                  <ScheduledScansBlock
                    refreshTrigger={scheduleRefreshTrigger}
                  />
                  <div className="flex flex-col lg:flex-row gap-6 mt-6">
                    <div className="flex-1 min-w-0">
                      <ScanHistoryBlock
                        onSelectScan={(r, id) => {
                          setResult(r);
                          setScanId(id ?? null);
                          setState("success");
                        }}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <AlertHistoryBlock />
                    </div>
                  </div>
                </>
              )}
            </>
          )}

          {state === "loading" && <ScanLoader steps={steps} />}

          {state === "success" &&
            result &&
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
                {error.message}
              </p>
            </Modal>
          )}
        </div>
      </AnimateInView>
    </div>
  );
}
