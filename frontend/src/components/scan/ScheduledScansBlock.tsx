"use client";

import React, { useCallback, useEffect, useState } from "react";
import { CalendarClock, Plus, Pause, Play, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
import LoadingScreen from "../LoadingScreen";
import { GenericButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  createScheduledScan,
  getScheduledScans,
  updateScheduledScan,
  deleteScheduledScan,
  getUserTimezone,
  type ScheduledScan,
  type Frequency,
} from "../../services/scheduledScanService";
import { ScheduleFormPanel, RecurrenceScheduleFields } from "../schedule";
import { formatDateTimeShort } from "../../utils/dateFormat";
import { normalizeScanUrl } from "../../utils/scanUrl";
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

export default function ScheduledScansBlock() {
  const { t } = useLanguage();
  const [items, setItems] = useState<ScheduledScan[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formUrl, setFormUrl] = useState("");
  const [formFrequency, setFormFrequency] = useState<Frequency>("daily");
  const [formTime, setFormTime] = useState("02:00");
  const [formDayOfWeek, setFormDayOfWeek] = useState(0);
  const [formDayOfMonth, setFormDayOfMonth] = useState(15);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await getScheduledScans();
      setItems(list);
    } catch {
      showErrorToast(t("scheduledScans.loadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!formUrl.trim()) {
      showErrorToast(t("scheduledScans.urlRequired"));
      return;
    }
    const normalizedUrl = normalizeScanUrl(formUrl);
    const { hour, minute } = parseTimeToHourMinute(formTime);
    setSaving(true);
    try {
      const created = await createScheduledScan({
        url: normalizedUrl,
        frequency: formFrequency,
        schedule_hour: hour,
        schedule_minute: minute,
        schedule_day_of_week:
          formFrequency === "weekly" ? formDayOfWeek : undefined,
        schedule_day_of_month:
          formFrequency === "monthly" ? formDayOfMonth : undefined,
        timezone: getUserTimezone(),
      });
      setItems((prev) => [...prev, created]);
      setShowForm(false);
      setFormUrl("");
      showSuccessToast(t("scheduledScans.createSuccess"));
    } catch (err) {
      showErrorToast(
        err instanceof Error ? err.message : t("scheduledScans.createError"),
      );
    } finally {
      setSaving(false);
    }
  };

  const handleToggleEnabled = async (item: ScheduledScan) => {
    try {
      const updated = await updateScheduledScan(item.id, {
        enabled: !item.enabled,
      });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
      showSuccessToast(
        updated.enabled
          ? t("scheduledScans.resumed")
          : t("scheduledScans.paused"),
      );
    } catch {
      showErrorToast(t("scheduledScans.updateError"));
    }
  };

  const handleDeleteConfirm = async () => {
    const id = deleteTargetId;
    if (!id) return;
    setDeleteTargetId(null);
    try {
      await deleteScheduledScan(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      showSuccessToast(t("scheduledScans.deleteSuccess"));
    } catch {
      showErrorToast(t("scheduledScans.deleteError"));
    }
  };

  const getFrequencyLabel = (freq: string) => {
    const opt = FREQUENCY_OPTIONS.find((o) => o.value === freq);
    return opt ? t(opt.labelKey) : freq;
  };

  return (
    <>
      <Card disableHover className="mt-6">
        <div className="flex items-center gap-3 mb-4">
          <CalendarClock className="w-6 h-6 text-[rgb(var(--primary))]" />
          <h2 className="text-xl font-bold text-[var(--text)]">
            {t("scheduledScans.title")}
          </h2>
        </div>
        <p className="text-sm text-[var(--muted)] mb-4">
          {t("scheduledScans.description")}
        </p>

        {loading ? (
          <LoadingScreen
            variant="section"
            message={t("scheduledScans.loading")}
          />
        ) : (
          <div className="space-y-4">
            {items.length === 0 && !showForm ? (
              <p className="text-muted-theme">{t("scheduledScans.empty")}</p>
            ) : (
              <ul className="divide-y divide-[var(--color-border)]">
                {items.map((item) => (
                  <li
                    key={item.id}
                    className="py-3 flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-[var(--text)] truncate">
                        {item.url
                          .replace(/^https?:\/\//, "")
                          .replace(/\/$/, "") || item.url}
                      </p>
                      <p className="text-xs text-[var(--muted)] mt-0.5">
                        {getFrequencyLabel(item.frequency)}
                        {item.enabled && (
                          <>
                            {" · "}
                            {t("scheduledScans.nextRun")}{" "}
                            {formatDateTimeShort(item.next_run_at)}
                          </>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleToggleEnabled(item)}
                        className="p-2 text-[var(--muted)] hover:text-[rgb(var(--primary))] shrink-0 cursor-pointer"
                        aria-label={
                          item.enabled
                            ? t("scheduledScans.pause")
                            : t("scheduledScans.resume")
                        }
                      >
                        {item.enabled ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteTargetId(item.id)}
                        className="p-2 text-[var(--muted)] hover:text-[rgb(var(--danger))] shrink-0 cursor-pointer"
                        aria-label={t("scheduledScans.delete")}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {showForm ? (
              <ScheduleFormPanel className="mt-4">
                <label className="block text-sm font-medium text-[var(--text)]">
                  {t("scheduledScans.urlLabel")}
                </label>
                <input
                  type="text"
                  inputMode="url"
                  value={formUrl}
                  onChange={(e) => setFormUrl(e.target.value)}
                  placeholder={t("scheduledScans.urlPlaceholder")}
                  className="auth-input w-full"
                />
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
                />
                <div className="flex gap-2 pt-2">
                  <GenericButton
                    label={t("scheduledScans.addBtn")}
                    onClick={handleCreate}
                    loading={saving}
                  />
                  <GenericButton
                    label={t("scheduledScans.cancelBtn")}
                    variant="outline"
                    onClick={() => {
                      setShowForm(false);
                      setFormUrl("");
                    }}
                  />
                </div>
              </ScheduleFormPanel>
            ) : (
              <GenericButton
                label={t("scheduledScans.addNew")}
                variant="outline"
                size="sm"
                icon={<Plus className="w-4 h-4" />}
                iconPosition="left"
                onClick={() => setShowForm(true)}
                className="mt-2"
              />
            )}
          </div>
        )}

        <ConfirmModal
          isOpen={deleteTargetId !== null}
          onClose={() => setDeleteTargetId(null)}
          onConfirm={handleDeleteConfirm}
          title={t("scheduledScans.deleteConfirmTitle")}
          message={t("scheduledScans.deleteConfirmMessage")}
          confirmText={t("scheduledScans.deleteConfirmBtn")}
        />
      </Card>
    </>
  );
}
