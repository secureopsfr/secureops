"use client";

import React from "react";
import { DatePicker, TimePicker } from "../inputs";
import { useLanguage } from "../LanguageProvider";

interface ScheduleDateFieldsProps {
  dateLabelKey: string;
  timeLabelKey: string;
  timeHintKey?: string;
  scheduledDate: string;
  scheduledTime: string;
  onDateChange: (date: string) => void;
  onTimeChange: (time: string) => void;
  minDate?: string;
}

/**
 * Champs date + heure pour planification ponctuelle (ex. envoi email).
 * Réutilisé dans l'admin (emails) et ailleurs.
 */
export default function ScheduleDateFields({
  dateLabelKey,
  timeLabelKey,
  timeHintKey,
  scheduledDate,
  scheduledTime,
  onDateChange,
  onTimeChange,
  minDate,
}: ScheduleDateFieldsProps) {
  const { t } = useLanguage();
  return (
    <>
      <div>
        <label className="block text-sm font-medium text-[var(--text)] mb-2">
          {t(dateLabelKey)}
        </label>
        <DatePicker
          value={scheduledDate}
          onChange={onDateChange}
          min={minDate}
          className="w-full min-w-0"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-[var(--text)] mb-2">
          {timeHintKey ? (
            <>
              {t(timeLabelKey)} ({t(timeHintKey)})
            </>
          ) : (
            t(timeLabelKey)
          )}
        </label>
        <TimePicker
          value={scheduledTime}
          onChange={onTimeChange}
          aria-label={t(timeLabelKey)}
        />
      </div>
    </>
  );
}
