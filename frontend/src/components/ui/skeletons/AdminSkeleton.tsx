"use client";

import React from "react";
import Card from "../cards/Card";
import Skeleton, { SkeletonButton } from "./Skeleton";

/**
 * Skeleton pour une liste de type admin (contacts, newsletters, etc.)
 * Affiche un header + plusieurs lignes de contenu
 */
export const AdminListSkeleton: React.FC<{
  rows?: number;
  className?: string;
}> = ({ rows = 4, className = "" }) => (
  <Card disableHover style={{ padding: "2rem" }} className={className}>
    {/* Header: titre + bouton */}
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Skeleton width="w-5" height="h-5" rounded="md" />
          <Skeleton width="w-48" height="h-6" />
        </div>
        <Skeleton width="w-16" height="h-4" />
      </div>
      <SkeletonButton width="w-28" />
    </div>

    {/* Items */}
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)]"
        >
          {/* Top row: date + actions */}
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <Skeleton width="w-4" height="h-4" rounded="sm" />
                <Skeleton width="w-36" height="h-3.5" />
              </div>
              <div className="flex items-center gap-2">
                <Skeleton width="w-4" height="h-4" rounded="sm" />
                <Skeleton width="w-44" height="h-3.5" />
              </div>
            </div>
            <SkeletonButton width="w-24" />
          </div>
          {/* Content block */}
          <div className="mt-3 p-3 rounded-lg bg-[var(--color-surface-input)] border border-[var(--border)]">
            <Skeleton width="w-full" height="h-3" className="mb-1.5" />
            <Skeleton width="w-3/4" height="h-3" />
          </div>
        </div>
      ))}
    </div>
  </Card>
);

/**
 * Skeleton pour les métriques admin
 * Les largeurs de colonnes utilisent des classes statiques (Tailwind JIT
 * ne détecte pas les template literals dynamiques comme `w-[${v}px]`).
 */
const metricColWidths = [
  "w-[120px]",
  "w-[80px]",
  "w-[100px]",
  "w-[80px]",
  "w-[100px]",
  "w-[80px]",
] as const;

export const AdminMetricsSkeleton: React.FC<{ className?: string }> = ({
  className = "",
}) => (
  <Card disableHover className={className}>
    {/* Header */}
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div className="flex items-center gap-3">
        <Skeleton width="w-5" height="h-5" rounded="md" />
        <Skeleton width="w-64" height="h-6" />
      </div>
      <div className="flex items-center gap-2">
        <Skeleton width="w-32" height="h-9" rounded="lg" />
        <SkeletonButton width="w-28" />
      </div>
    </div>

    {/* Table header */}
    <div className="flex items-center gap-4 p-3 border-b border-[var(--border)]">
      {metricColWidths.map((w, i) => (
        <Skeleton key={i} width={w} height="h-4" className="flex-shrink-0" />
      ))}
    </div>

    {/* Table rows */}
    {Array.from({ length: 5 }).map((_, i) => (
      <div
        key={i}
        className="flex items-center gap-4 p-3 border-b border-[var(--border)] last:border-b-0"
      >
        {metricColWidths.map((w, j) => (
          <Skeleton
            key={j}
            width={w}
            height="h-3.5"
            className="flex-shrink-0"
          />
        ))}
      </div>
    ))}
  </Card>
);

/**
 * Skeleton pour le Kanban (vue contact)
 */
export const AdminKanbanSkeleton: React.FC<{ className?: string }> = ({
  className = "",
}) => (
  <Card disableHover className={className}>
    {/* Header */}
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Skeleton width="w-5" height="h-5" rounded="md" />
          <Skeleton width="w-44" height="h-6" />
        </div>
        <Skeleton width="w-16" height="h-4" />
      </div>
      <div className="flex items-center gap-2">
        <Skeleton width="w-40" height="h-9" rounded="lg" />
        <SkeletonButton width="w-28" />
      </div>
    </div>

    {/* Kanban columns */}
    <div className="flex gap-4 p-6">
      {Array.from({ length: 3 }).map((_, col) => (
        <div key={col} className="flex-1 min-w-[250px]">
          {/* Column header */}
          <div className="flex items-center gap-2 mb-4">
            <Skeleton width="w-3" height="h-3" rounded="full" />
            <Skeleton width="w-20" height="h-4" />
            <Skeleton width="w-6" height="h-5" rounded="full" />
          </div>
          {/* Cards */}
          <div className="space-y-3">
            {Array.from({ length: col === 0 ? 3 : col === 1 ? 2 : 1 }).map(
              (_, card) => (
                <div
                  key={card}
                  className="p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)]"
                >
                  <Skeleton width="w-24" height="h-3" className="mb-3" />
                  <Skeleton width="w-3/4" height="h-4" className="mb-2" />
                  <Skeleton width="w-full" height="h-3" className="mb-1" />
                  <Skeleton width="w-2/3" height="h-3" />
                </div>
              ),
            )}
          </div>
        </div>
      ))}
    </div>
  </Card>
);

/**
 * Skeleton pour la page d'authentification (connexion/inscription)
 * Reproduit fidèlement la structure de auth-card / auth-header / auth-footer.
 * Marge négative pour compenser le padding-top du body pendant le chargement (pas de header sur les pages auth).
 */
export const AuthFormSkeleton: React.FC = () => (
  <div style={{ marginTop: "calc(-1 * var(--header-height))" }}>
    <div className="auth-container">
      <div className="auth-card">
        {/* auth-header (CSS fournit mb-1rem, flex-col center) */}
        <div className="auth-header">
          {/* Logo — auth-logo = 80×80px = w-20 h-20 */}
          <div className="flex justify-center mb-4">
            <Skeleton width="w-20" height="h-20" rounded="lg" />
          </div>
          {/* Title — auth-title = 1.25rem bold, line-height ~1.75rem */}
          <div className="flex justify-center mb-1">
            <Skeleton width="w-40" height="h-7" />
          </div>
          {/* Subtitle — auth-subtitle = 0.75rem */}
          <div className="flex justify-center">
            <Skeleton width="w-56" height="h-3" />
          </div>
        </div>

        {/* Content — espace identique au vrai : space-y-4, flex-1 */}
        <div className="space-y-4 flex-1 overflow-y-auto">
          {/* Form fields — space-y-3 comme le vrai formulaire */}
          <div className="space-y-3">
            {/* Email — label-form (0.75rem, mb-0.25rem) + auth-input */}
            <div>
              <Skeleton width="w-12" height="h-3" className="mb-1" />
              <Skeleton width="w-full" height="h-10" rounded="lg" />
            </div>
            {/* Password — label + input + forgot-password link */}
            <div>
              <Skeleton width="w-24" height="h-3" className="mb-1" />
              <Skeleton width="w-full" height="h-10" rounded="lg" />
              <div className="flex justify-end mt-1">
                <Skeleton width="w-32" height="h-3" />
              </div>
            </div>
            {/* Submit — .btn padding ≈ h-10, rounded-full */}
            <Skeleton width="w-full" height="h-10" rounded="full" />
          </div>
        </div>

        {/* auth-footer — mt-1rem, pt-0.75rem, border-top */}
        <div className="auth-footer">
          <div className="flex justify-center">
            <Skeleton width="w-48" height="h-3" />
          </div>
        </div>
      </div>
    </div>
  </div>
);
