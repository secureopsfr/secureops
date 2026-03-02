"use client";

import React from "react";
import { TimePicker } from "../inputs";
import { DropdownSelector } from "../buttons";
import { useLanguage } from "../LanguageProvider";

export type RecurrenceFrequency = "daily" | "weekly" | "monthly";

interface FrequencyOption {
  value: RecurrenceFrequency;
  labelKey: string;
}

interface DayOfWeekOption {
  value: number;
  labelKey: string;
}

interface RecurrenceScheduleFieldsProps {
  frequencyLabelKey: string;
  timeLabelKey: string;
  dayOfWeekLabelKey: string;
  dayOfMonthLabelKey: string;
  frequencyOptions: FrequencyOption[];
  daysOfWeek: DayOfWeekOption[];
  frequency: RecurrenceFrequency;
  timeValue: string;
  dayOfWeek: number;
  dayOfMonth: number;
  onFrequencyChange: (f: RecurrenceFrequency) => void;
  onTimeChange: (time: string) => void;
  onDayOfWeekChange: (d: number) => void;
  onDayOfMonthChange: (d: number) => void;
}

/**
 * Champs pour planification récurrente (daily/weekly/monthly + heure).
 * Réutilisé pour les scans planifiés.
 */
export default function RecurrenceScheduleFields({
  frequencyLabelKey,
  timeLabelKey,
  dayOfWeekLabelKey,
  dayOfMonthLabelKey,
  frequencyOptions,
  daysOfWeek,
  frequency,
  timeValue,
  dayOfWeek,
  dayOfMonth,
  onFrequencyChange,
  onTimeChange,
  onDayOfWeekChange,
  onDayOfMonthChange,
}: RecurrenceScheduleFieldsProps) {
  const { t } = useLanguage();
  const parts = (timeValue || "00:00").split(":");
  const hour = Number.isNaN(Number(parts[0]))
    ? 0
    : Math.min(23, Math.max(0, Number(parts[0])));
  const minute = Number.isNaN(Number(parts[1]))
    ? 0
    : Math.min(59, Math.max(0, Number(parts[1])));
  const timeDisplay = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;

  const handleTimeChange = (v: string) => {
    onTimeChange(v || "00:00");
  };

  const frequencyOptionsFormatted = frequencyOptions.map((opt) => ({
    value: opt.value,
    label: t(opt.labelKey),
  }));

  const dayOfWeekOptionsFormatted = daysOfWeek.map((d) => ({
    value: String(d.value),
    label: t(d.labelKey),
  }));

  const dayOfMonthOptions = Array.from({ length: 31 }, (_, i) => ({
    value: String(i + 1),
    label: String(i + 1),
  }));

  return (
    <>
      <div>
        <label className="block text-sm font-medium text-[var(--text)] mb-2">
          {t(frequencyLabelKey)}
        </label>
        <DropdownSelector
          selectedValue={frequency}
          onChange={(v) => onFrequencyChange(v as RecurrenceFrequency)}
          options={frequencyOptionsFormatted}
          width="100%"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-[var(--text)] mb-2">
          {t(timeLabelKey)}
        </label>
        <TimePicker
          value={timeDisplay}
          onChange={handleTimeChange}
          aria-label={t(timeLabelKey)}
        />
      </div>
      {frequency === "weekly" && (
        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2">
            {t(dayOfWeekLabelKey)}
          </label>
          <DropdownSelector
            selectedValue={String(dayOfWeek)}
            onChange={(v) => onDayOfWeekChange(Number(v))}
            options={dayOfWeekOptionsFormatted}
            width="100%"
          />
        </div>
      )}
      {frequency === "monthly" && (
        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2">
            {t(dayOfMonthLabelKey)}
          </label>
          <DropdownSelector
            selectedValue={String(dayOfMonth)}
            onChange={(v) => onDayOfMonthChange(Number(v))}
            options={dayOfMonthOptions}
            width="100%"
          />
        </div>
      )}
    </>
  );
}
