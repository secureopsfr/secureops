"use client";

import useSWR from "swr";
import * as adminAlertsService from "../../services/admin/adminAlertsService";
import type {
  AlertRuleRecord,
  AlertEventRecord,
  AlertSummaryResponse,
} from "../../services/admin/adminAlertsService";
import {
  adminAlertEventsKey,
  ADMIN_ALERT_RULES_KEY,
  ADMIN_ALERT_SUMMARY_KEY,
} from "./keys";

/**
 * Hook SWR pour les règles d'alerte admin.
 */
export function useAdminAlertRules() {
  const { data, isLoading, mutate } = useSWR(ADMIN_ALERT_RULES_KEY, () =>
    adminAlertsService.getAlertRules(),
  );
  return {
    data: (data ?? []) as AlertRuleRecord[],
    rules: (data ?? []) as AlertRuleRecord[],
    isLoading,
    mutate,
  };
}

/**
 * Hook SWR pour les événements d'alerte (liste paginée).
 */
export function useAdminAlertEvents(params: { limit: number; offset: number }) {
  const key = adminAlertEventsKey(params);
  const { data, isLoading, mutate } = useSWR(key, () =>
    adminAlertsService.getAlertEvents(params),
  );
  return {
    data,
    events: (data?.events as AlertEventRecord[]) ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}

/**
 * Hook SWR pour le résumé des alertes.
 */
export function useAdminAlertSummary() {
  const { data, isLoading, mutate } = useSWR(
    ADMIN_ALERT_SUMMARY_KEY,
    () => adminAlertsService.getAlertSummary(),
    { dedupingInterval: 60_000 },
  );
  return {
    data: data as AlertSummaryResponse | undefined,
    summary: data ?? null,
    isLoading,
    mutate,
  };
}
