"use client";

import { RecurrenceScheduleFields } from "../schedule";
import { Checkbox, NumericInput } from "../inputs";
import type {
  ScheduleFormState,
  ScheduleFormActions,
} from "../../hooks/useScheduleForm";
import { FREQUENCY_OPTIONS, DAYS_OF_WEEK } from "../../hooks/useScheduleForm";

interface ScheduleFormSectionProps {
  form: ScheduleFormState;
  actions: ScheduleFormActions;
  t: (key: string) => string;
}

/**
 * Champs de récurrence pour les scans planifiés.
 * Wraps RecurrenceScheduleFields avec le state et les options.
 */
export default function ScheduleFormSection({
  form,
  actions,
  t,
}: ScheduleFormSectionProps) {
  return (
    <RecurrenceScheduleFields
      frequencyLabelKey="scheduledScans.frequencyLabel"
      timeLabelKey="scheduledScans.timeLabel"
      dayOfWeekLabelKey="scheduledScans.dayOfWeekLabel"
      dayOfMonthLabelKey="scheduledScans.dayOfMonthLabel"
      frequencyOptions={FREQUENCY_OPTIONS}
      daysOfWeek={DAYS_OF_WEEK}
      frequency={form.frequency}
      timeValue={form.time}
      dayOfWeek={form.dayOfWeek}
      dayOfMonth={form.dayOfMonth}
      onFrequencyChange={actions.setFrequency}
      onTimeChange={actions.setTime}
      onDayOfWeekChange={actions.setDayOfWeek}
      onDayOfMonthChange={actions.setDayOfMonth}
      afterTimeSlot={
        <div className="flex flex-col gap-3">
          {/* Activation globale des alertes */}
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
            checked={form.scanAlertsEnabled}
            onChange={actions.setScanAlertsEnabled}
          />

          {/* Options détaillées — visibles seulement si les alertes sont activées */}
          {form.scanAlertsEnabled && (
            <div className="ml-6 flex flex-col gap-3 border-l-2 border-[var(--border)] pl-4">
              <Checkbox
                label={
                  <>
                    <span className="block font-medium text-[var(--text)]">
                      {t("scheduledScans.alertOnRegression")}
                    </span>
                    <span className="text-xs text-[var(--muted)]">
                      {t("scheduledScans.alertOnRegressionDesc")}
                    </span>
                  </>
                }
                checked={form.alertOnRegression}
                onChange={actions.setAlertOnRegression}
              />

              {/* Seuil de régression — visible seulement si alertOnRegression est coché */}
              {form.alertOnRegression && (
                <div className="ml-6">
                  <label className="mb-1 block text-sm font-medium text-[var(--text)]">
                    {t("scheduledScans.alertScoreThreshold")}
                  </label>
                  <p className="mb-2 text-xs text-[var(--muted)]">
                    {t("scheduledScans.alertScoreThresholdDesc")}
                  </p>
                  <NumericInput
                    value={form.alertScoreThreshold ?? ""}
                    onNumberChange={(v) => actions.setAlertScoreThreshold(v)}
                    min={1}
                    max={100}
                    placeholder={t(
                      "scheduledScans.alertScoreThresholdPlaceholder",
                    )}
                    className="w-24"
                  />
                </div>
              )}

              <Checkbox
                label={
                  <>
                    <span className="block font-medium text-[var(--text)]">
                      {t("scheduledScans.alertOnCriticalFinding")}
                    </span>
                    <span className="text-xs text-[var(--muted)]">
                      {t("scheduledScans.alertOnCriticalFindingDesc")}
                    </span>
                  </>
                }
                checked={form.alertOnCriticalFinding}
                onChange={actions.setAlertOnCriticalFinding}
              />
            </div>
          )}
        </div>
      }
    />
  );
}
