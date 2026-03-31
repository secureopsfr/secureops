/**
 * Hook pour la gestion du formulaire de scan planifié.
 * Centralise les 5 champs de planification + l'état de sauvegarde.
 */

import { useState, useCallback } from "react";
import {
  createScheduledScan,
  getUserTimezone,
  type Frequency,
  type CreateScheduledScanInput,
} from "../services/scheduledScanService";
import { showErrorToast, showSuccessToast } from "../utils/toastNotifications";

export const FREQUENCY_OPTIONS = [
  { value: "daily" as const, labelKey: "scheduledScans.frequencyDaily" },
  { value: "weekly" as const, labelKey: "scheduledScans.frequencyWeekly" },
  { value: "monthly" as const, labelKey: "scheduledScans.frequencyMonthly" },
];

export const DAYS_OF_WEEK = [
  { value: 0, labelKey: "scheduledScans.dayMonday" },
  { value: 1, labelKey: "scheduledScans.dayTuesday" },
  { value: 2, labelKey: "scheduledScans.dayWednesday" },
  { value: 3, labelKey: "scheduledScans.dayThursday" },
  { value: 4, labelKey: "scheduledScans.dayFriday" },
  { value: 5, labelKey: "scheduledScans.daySaturday" },
  { value: 6, labelKey: "scheduledScans.daySunday" },
];

export function parseTimeToHourMinute(time: string): {
  hour: number;
  minute: number;
} {
  const [h, m] = (time || "00:00").split(":").map(Number);
  return { hour: h ?? 0, minute: m ?? 0 };
}

export interface ScheduleFormState {
  frequency: Frequency;
  time: string;
  dayOfWeek: number;
  dayOfMonth: number;
  scanAlertsEnabled: boolean;
  alertOnRegression: boolean;
  alertOnCriticalFinding: boolean;
  alertScoreThreshold: number | null;
}

export interface ScheduleFormActions {
  setFrequency: (v: Frequency) => void;
  setTime: (v: string) => void;
  setDayOfWeek: (v: number) => void;
  setDayOfMonth: (v: number) => void;
  setScanAlertsEnabled: (v: boolean) => void;
  setAlertOnRegression: (v: boolean) => void;
  setAlertOnCriticalFinding: (v: boolean) => void;
  setAlertScoreThreshold: (v: number | null) => void;
}

export function useScheduleForm(t: (key: string) => string): {
  form: ScheduleFormState;
  actions: ScheduleFormActions;
  saving: boolean;
  submitSchedule: (
    payload: Omit<
      CreateScheduledScanInput,
      | "frequency"
      | "schedule_hour"
      | "schedule_minute"
      | "schedule_day_of_week"
      | "schedule_day_of_month"
      | "timezone"
      | "scan_alerts_enabled"
      | "alert_on_regression"
      | "alert_on_critical_finding"
      | "alert_score_threshold"
    >,
  ) => Promise<boolean>;
} {
  const [frequency, setFrequency] = useState<Frequency>("daily");
  const [time, setTime] = useState("02:00");
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [dayOfMonth, setDayOfMonth] = useState(15);
  const [scanAlertsEnabled, setScanAlertsEnabled] = useState(true);
  const [alertOnRegression, setAlertOnRegression] = useState(true);
  const [alertOnCriticalFinding, setAlertOnCriticalFinding] = useState(true);
  const [alertScoreThreshold, setAlertScoreThreshold] = useState<number | null>(
    null,
  );
  const [saving, setSaving] = useState(false);

  const submitSchedule = useCallback(
    async (
      basePayload: Omit<
        CreateScheduledScanInput,
        | "frequency"
        | "schedule_hour"
        | "schedule_minute"
        | "schedule_day_of_week"
        | "schedule_day_of_month"
        | "timezone"
        | "scan_alerts_enabled"
        | "alert_on_regression"
        | "alert_on_critical_finding"
        | "alert_score_threshold"
      >,
    ): Promise<boolean> => {
      const { hour, minute } = parseTimeToHourMinute(time);
      setSaving(true);
      try {
        await createScheduledScan({
          ...basePayload,
          frequency,
          schedule_hour: hour,
          schedule_minute: minute,
          schedule_day_of_week: frequency === "weekly" ? dayOfWeek : undefined,
          schedule_day_of_month:
            frequency === "monthly" ? dayOfMonth : undefined,
          timezone: getUserTimezone(),
          scan_alerts_enabled: scanAlertsEnabled,
          alert_on_regression: alertOnRegression,
          alert_on_critical_finding: alertOnCriticalFinding,
          alert_score_threshold: alertScoreThreshold,
        });
        showSuccessToast(t("scheduledScans.createSuccess"));
        return true;
      } catch (err) {
        showErrorToast(
          err instanceof Error ? err.message : t("scheduledScans.createError"),
        );
        return false;
      } finally {
        setSaving(false);
      }
    },
    [
      frequency,
      time,
      dayOfWeek,
      dayOfMonth,
      scanAlertsEnabled,
      alertOnRegression,
      alertOnCriticalFinding,
      alertScoreThreshold,
      t,
    ],
  );

  return {
    form: {
      frequency,
      time,
      dayOfWeek,
      dayOfMonth,
      scanAlertsEnabled,
      alertOnRegression,
      alertOnCriticalFinding,
      alertScoreThreshold,
    },
    actions: {
      setFrequency,
      setTime,
      setDayOfWeek,
      setDayOfMonth,
      setScanAlertsEnabled,
      setAlertOnRegression,
      setAlertOnCriticalFinding,
      setAlertScoreThreshold,
    },
    saving,
    submitSchedule,
  };
}
