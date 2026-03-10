"use client";

import { DatePicker } from "../../inputs";
import { ScheduleFormPanel } from "../../schedule";
import FormSelect from "../../forms/FormSelect";

export type ExpiryMode = "preset" | "date";

export interface ExpiryFormSectionProps {
  mode: ExpiryMode;
  onModeChange: (mode: ExpiryMode) => void;
  ttlDays: string;
  onTtlDaysChange: (v: string) => void;
  expiryDate: string;
  onExpiryDateChange: (v: string) => void;
  t: (key: string) => string;
}

const TTL_OPTIONS = [
  { value: "30", labelKey: "scanner.clesApi.ttl1Month" },
  { value: "90", labelKey: "scanner.clesApi.ttl3Months" },
  { value: "180", labelKey: "scanner.clesApi.ttl6Months" },
  { value: "365", labelKey: "scanner.clesApi.ttl1Year" },
  { value: "0", labelKey: "scanner.clesApi.ttlNever" },
];

export default function ExpiryFormSection({
  mode,
  onModeChange,
  ttlDays,
  onTtlDaysChange,
  expiryDate,
  onExpiryDateChange,
  t,
}: ExpiryFormSectionProps) {
  return (
    <div className="space-y-3">
      <div className="space-y-3">
        <label className="radio-option-card flex items-center gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)] hover:bg-[var(--color-surface-input)] cursor-pointer">
          <input
            type="radio"
            name="expiryMode"
            value="preset"
            checked={mode === "preset"}
            onChange={() => onModeChange("preset")}
            className="flex-shrink-0"
          />
          <span className="text-sm font-medium text-[var(--text)]">
            {t("scanner.clesApi.expiryModePreset")}
          </span>
        </label>
        <label className="radio-option-card flex items-center gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)] hover:bg-[var(--color-surface-input)] cursor-pointer">
          <input
            type="radio"
            name="expiryMode"
            value="date"
            checked={mode === "date"}
            onChange={() => onModeChange("date")}
            className="flex-shrink-0"
          />
          <span className="text-sm font-medium text-[var(--text)]">
            {t("scanner.clesApi.expiryModeDate")}
          </span>
        </label>
      </div>
      {mode === "preset" ? (
        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2">
            {t("scanner.clesApi.createTtlLabel")}
          </label>
          <FormSelect
            value={ttlDays}
            onChange={onTtlDaysChange}
            options={TTL_OPTIONS.map((o) => ({
              value: o.value,
              label: t(o.labelKey),
            }))}
            clickOnly
          />
        </div>
      ) : (
        <ScheduleFormPanel>
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              {t("scanner.clesApi.expiryDateLabel")}
            </label>
            <DatePicker
              value={expiryDate}
              onChange={onExpiryDateChange}
              min={new Date().toISOString().split("T")[0]}
              className="w-full min-w-0"
              compact
            />
          </div>
        </ScheduleFormPanel>
      )}
    </div>
  );
}
