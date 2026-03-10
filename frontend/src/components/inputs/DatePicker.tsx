"use client";

import React, { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useLanguage } from "../LanguageProvider";

const WEEKDAY_LABELS = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"];
const MONTH_LABELS = [
  "Janvier",
  "Février",
  "Mars",
  "Avril",
  "Mai",
  "Juin",
  "Juillet",
  "Août",
  "Septembre",
  "Octobre",
  "Novembre",
  "Décembre",
];

const ISO_DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;

function isValidDateString(s: string): boolean {
  if (!ISO_DATE_REGEX.test(s)) return false;
  const d = new Date(s + "T12:00:00");
  return !Number.isNaN(d.getTime()) && d.toISOString().startsWith(s);
}

interface DatePickerProps {
  value: string;
  onChange: (date: string) => void;
  min?: string;
  className?: string;
  /** Afficher le champ de saisie manuelle (AAAA-MM-JJ). Défaut: true */
  showInput?: boolean;
  placeholder?: string;
  /** Variante compacte (taille réduite) */
  compact?: boolean;
}

/**
 * Calendrier de sélection de date aux couleurs du thème, avec saisie manuelle possible.
 */
export default function DatePicker({
  value,
  onChange,
  min,
  className = "",
  showInput = true,
  placeholder = "AAAA-MM-JJ",
  compact = false,
}: DatePickerProps) {
  const { t } = useLanguage();
  const minDate = useMemo(
    () => (min ? new Date(min + "T00:00:00") : null),
    [min],
  );

  const [inputValue, setInputValue] = useState(value);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setInputValue(v);
    if (!isValidDateString(v)) return;
    if (min && v < min) return;
    onChange(v);
  };

  const handleInputBlur = () => {
    if (!isValidDateString(inputValue) || (min && inputValue < min)) {
      setInputValue(value);
    }
  };

  const [viewDate, setViewDate] = useState(() => {
    if (value) {
      const d = new Date(value + "T12:00:00");
      if (!Number.isNaN(d.getTime())) return d;
    }
    const d = new Date();
    if (minDate && d < minDate) return new Date(minDate);
    return d;
  });

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  const toISO = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

  const isToday = (d: Date) => {
    const today = new Date();
    return (
      d.getDate() === today.getDate() &&
      d.getMonth() === today.getMonth() &&
      d.getFullYear() === today.getFullYear()
    );
  };

  const grid = useMemo(() => {
    const first = new Date(year, month, 1);
    const last = new Date(year, month + 1, 0);
    const start = first.getDay() === 0 ? 6 : first.getDay() - 1;
    const daysInMonth = last.getDate();
    const isDisabled = (d: Date) => {
      if (!minDate) return false;
      const dayStart = new Date(d);
      dayStart.setHours(0, 0, 0, 0);
      const minStart = new Date(minDate);
      minStart.setHours(0, 0, 0, 0);
      return dayStart < minStart;
    };

    const rows: Array<{
      date: Date;
      iso: string;
      currentMonth: boolean;
      disabled: boolean;
    }> = [];

    for (let i = 0; i < start; i++) {
      const d = new Date(year, month, -start + i + 1);
      rows.push({
        date: d,
        iso: toISO(d),
        currentMonth: false,
        disabled: isDisabled(d),
      });
    }
    for (let day = 1; day <= daysInMonth; day++) {
      const d = new Date(year, month, day);
      rows.push({
        date: d,
        iso: toISO(d),
        currentMonth: true,
        disabled: isDisabled(d),
      });
    }
    const rest = 42 - rows.length;
    for (let i = 0; i < rest; i++) {
      const d = new Date(year, month + 1, i + 1);
      rows.push({
        date: d,
        iso: toISO(d),
        currentMonth: false,
        disabled: isDisabled(d),
      });
    }
    return rows;
  }, [year, month, minDate]);

  const prevMonth = () => {
    setViewDate((d) => new Date(d.getFullYear(), d.getMonth() - 1));
  };

  const nextMonth = () => {
    setViewDate((d) => new Date(d.getFullYear(), d.getMonth() + 1));
  };

  const canPrev = minDate
    ? new Date(year, month, 1) >
      new Date(minDate.getFullYear(), minDate.getMonth(), 1)
    : true;
  const canNext = true;

  return (
    <div
      className={`theme-calendar ${compact ? "theme-calendar-compact" : ""} ${className}`.trim()}
    >
      {showInput && (
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          placeholder={placeholder}
          className="auth-input w-full mb-3 min-w-0"
          aria-label={t("datePicker.ariaDate")}
        />
      )}
      <div className="theme-calendar-header">
        <button
          type="button"
          onClick={prevMonth}
          disabled={!canPrev}
          className="theme-calendar-nav"
          aria-label="Mois précédent"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="theme-calendar-title">
          {MONTH_LABELS[month]} {year}
        </span>
        <button
          type="button"
          onClick={nextMonth}
          disabled={!canNext}
          className="theme-calendar-nav"
          aria-label={t("datePicker.ariaNextMonth")}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
      <div className="theme-calendar-weekdays">
        {WEEKDAY_LABELS.map((label) => (
          <span key={label} className="theme-calendar-weekday">
            {label}
          </span>
        ))}
      </div>
      <div className="theme-calendar-grid">
        {grid.map((cell) => {
          const selected = value === cell.iso;
          const today = isToday(cell.date);
          return (
            <button
              key={cell.iso + (cell.currentMonth ? "c" : "o")}
              type="button"
              disabled={cell.disabled}
              onClick={() => !cell.disabled && onChange(cell.iso)}
              className={[
                "theme-calendar-day",
                !cell.currentMonth && "theme-calendar-day-other",
                selected && "theme-calendar-day-selected",
                today && !selected && "theme-calendar-day-today",
                cell.disabled && "theme-calendar-day-disabled",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {cell.date.getDate()}
            </button>
          );
        })}
      </div>
    </div>
  );
}
