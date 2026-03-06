"use client";

import React from "react";
import Card from "./Card";

interface SectionCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: React.ReactNode;
  children: React.ReactNode;
  className?: string;
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
}: SectionCardProps) {
  return (
    <Card disableHover className={className}>
      <div className="flex items-center gap-3 mb-4">
        <Icon className="w-6 h-6 text-[rgb(var(--primary))]" />
        <h2 className="text-xl font-bold text-[var(--text)]">{title}</h2>
      </div>
      {children}
    </Card>
  );
}
