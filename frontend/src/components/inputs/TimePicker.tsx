"use client";

import React from "react";

interface TimePickerProps {
  value: string;
  onChange: (time: string) => void;
  className?: string;
  /** Format HH:mm (ex. "14:30"). Défaut: "00:00" */
  min?: string;
  max?: string;
  disabled?: boolean;
  "aria-label"?: string;
}

/**
 * Sélecteur d'heure (HH:mm) réutilisable.
 * Utilisé pour la planification (emails admin, scans planifiés).
 */
export default function TimePicker({
  value,
  onChange,
  className = "",
  min,
  max,
  disabled = false,
  "aria-label": ariaLabel = "Heure",
}: TimePickerProps) {
  return (
    <input
      type="time"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      min={min}
      max={max}
      disabled={disabled}
      className={`auth-input w-full min-w-0 ${className}`.trim()}
      aria-label={ariaLabel}
    />
  );
}
