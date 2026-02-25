"use client";

/**
 * Provider React qui active le tracking analytics sur toutes les pages.
 *
 * Wrappe les children et appelle le hook usePageView() qui :
 * - Initialise le tracker (buffer + flush périodique)
 * - Émet session_start au premier chargement
 * - Émet page_view à chaque changement de route
 * - Émet page_exit avec la durée quand l'utilisateur quitte une page
 */

import React from "react";
import { usePageView } from "../hooks/usePageView";

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  usePageView();
  return <>{children}</>;
}
