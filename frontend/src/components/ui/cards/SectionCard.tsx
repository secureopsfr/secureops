"use client";

import React from "react";
import Card from "./Card";

interface SectionCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  compact?: boolean;
  headerAction?: React.ReactNode;
}

/**
 * Carte de section avec en-tête (icône + titre).
 * Structure commune aux sections admin, user et scan.
 */
export default function SectionCard({
  icon: Icon,
  title,
  children,
  className = "",
  compact = false,
  headerAction,
}: SectionCardProps) {
  return (
    <Card disableHover className={className}>
      <div
        className={`flex items-center justify-between gap-3 ${compact ? "mb-1" : "mb-4"}`}
      >
        <div className="flex items-center gap-3 min-w-0">
          <Icon className="w-6 h-6 text-[rgb(var(--primary))] shrink-0" />
          <h2 className="text-xl font-bold text-[var(--text)]">{title}</h2>
        </div>
        {headerAction != null ? (
          <div className="shrink-0">{headerAction}</div>
        ) : null}
      </div>
      {children}
    </Card>
  );
}
