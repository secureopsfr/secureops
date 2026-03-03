"use client";

import React from "react";

interface ScheduleFormPanelProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Panneau de formulaire de planification (style commun admin + scans).
 * Bordure, padding, fond. Pas une modal — affichage inline.
 */
export default function ScheduleFormPanel({
  children,
  className = "",
}: ScheduleFormPanelProps) {
  return (
    <div
      className={`p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)] min-w-0 space-y-4 ${className}`.trim()}
    >
      {children}
    </div>
  );
}
