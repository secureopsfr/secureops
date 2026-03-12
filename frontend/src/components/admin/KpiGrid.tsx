"use client";

import React from "react";
import Card from "../ui/cards/Card";

/* ─────────────────────── Types ─────────────────────── */

export interface KpiItem {
  /** Libellé affiché sous l'icône */
  label: string;
  /** Valeur principale (déjà formatée) */
  value: React.ReactNode;
  /** Icône Lucide (ex: <Users className="w-4 h-4 text-[rgb(var(--primary))]" />) */
  icon: React.ReactNode;
  /** Couleur de fond de la pastille icône (ex: "rgba(var(--primary),0.15)") */
  bgColor: string;
}

export interface KpiGridProps {
  /** Liste des KPI à afficher */
  items: KpiItem[];
  /** Nombre de colonnes sur grand écran (défaut : nombre d'items, max 6) */
  columns?: 2 | 3 | 4 | 5 | 6;
}

/* ────────────── Mapping colonnes → classe Tailwind ────────────── */

const lgColsClass: Record<number, string> = {
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-4",
  5: "lg:grid-cols-5",
  6: "lg:grid-cols-6",
};

/* ──────────────── Composant KPI individuel (memoïsé) ──────────────── */

const KpiCard = React.memo<KpiItem>(({ label, value, icon, bgColor }) => (
  <Card disableHover style={{ padding: "1rem 0.5rem" }}>
    <div className="flex items-center justify-center gap-3 mb-2">
      <div className="rounded-lg" style={{ backgroundColor: bgColor }}>
        {icon}
      </div>
      <span className="text-xs text-[var(--muted)] uppercase tracking-wider">
        {label}
      </span>
    </div>
    <p className="text-xl font-bold text-[var(--text)] text-center">{value}</p>
  </Card>
));

KpiCard.displayName = "KpiCard";

/* ─────────────────────── Composant ─────────────────────── */

/**
 * Grille de KPI réutilisable pour les sections admin.
 *
 * Chaque KPI est rendu dans une `KpiCard` memoïsée avec une pastille
 * icône colorée, un libellé en uppercase et une valeur en gras.
 */
const KpiGrid = React.memo(function KpiGrid({ items, columns }: KpiGridProps) {
  const cols = columns ?? (Math.min(items.length, 6) as 2 | 3 | 4 | 5 | 6);

  return (
    <div
      className={`grid grid-cols-2 ${lgColsClass[cols] ?? "lg:grid-cols-5"} gap-4`}
    >
      {items.map((kpi) => (
        <KpiCard key={kpi.label} {...kpi} />
      ))}
    </div>
  );
});

export default KpiGrid;
