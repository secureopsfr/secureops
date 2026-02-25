"use client";

import React from "react";
import type { BadgeVariant } from "../components/Badge";

/* ─────────────── Badge variants ─────────────── */

/**
 * Renvoie la variante de Badge pour un plan d'abonnement.
 */
export function getPlanBadgeVariant(plan: string): BadgeVariant {
  return plan === "premium" ? "success" : "default";
}

/**
 * Renvoie la variante de Badge pour un statut d'abonnement.
 */
export function getStatusBadgeVariant(status: string): BadgeVariant {
  switch (status) {
    case "active":
      return "success";
    case "trial":
      return "info";
    case "canceled":
      return "warning";
    case "suspended":
      return "error";
    default:
      return "default";
  }
}

/**
 * Renvoie le label français pour un statut d'abonnement.
 */
export function getStatusLabel(status: string): string {
  switch (status) {
    case "active":
      return "Actif";
    case "trial":
      return "Essai";
    case "canceled":
      return "Annulé";
    case "suspended":
      return "Suspendu";
    default:
      return status;
  }
}

/* ─────────────── Composants partagés ─────────────── */

/**
 * Icône booléenne avec tooltip (checkbox-like pour les colonnes de tableau).
 */
export function BooleanIcon({
  icon: Icon,
  enabled,
  titleOn,
  titleOff,
}: {
  icon: React.ComponentType<{ className?: string }>;
  enabled: boolean;
  titleOn: string;
  titleOff: string;
}) {
  return (
    <span title={enabled ? titleOn : titleOff}>
      <Icon
        className={`w-4 h-4 mx-auto ${enabled ? "text-[rgb(var(--success))]" : "text-[var(--muted)] opacity-30"}`}
      />
    </span>
  );
}
