"use client";

import { RecurrenceScheduleFields } from "../schedule";
import { Checkbox } from "../inputs";
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
      }
    />
  );
}
