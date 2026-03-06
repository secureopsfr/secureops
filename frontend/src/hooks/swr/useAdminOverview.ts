"use client";

import useSWR from "swr";
import adminService from "../../services/admin";
import type {
  UsersStatsResponse,
  SubscriptionStatsResponse,
  AlertSummaryResponse,
  AuditStatsResponse,
  ImageGalleryStats,
  PageViewsSummaryResponse,
} from "../../services/admin";
import { computeApiKpis } from "../../utils/metricsHelpers";
import type { ApiKpis } from "../../utils/metricsHelpers";
import { ADMIN_OVERVIEW_KEY } from "./keys";

/**
 * Données agrégées de la page Admin Overview (stats utilisateurs, abonnements, alertes, etc.).
 */
export interface OverviewData {
  userStats: UsersStatsResponse | null;
  subStats: SubscriptionStatsResponse | null;
  alertSummary: AlertSummaryResponse | null;
  auditStats: AuditStatsResponse | null;
  imageStats: ImageGalleryStats | null;
  siteStats: PageViewsSummaryResponse | null;
  contactPending: number;
  contactTotal: number;
  apiMetrics: ApiKpis | null;
}

async function overviewFetcher(): Promise<OverviewData> {
  const [
    userStats,
    subStats,
    alertSummary,
    auditStats,
    imageStats,
    siteStatsRes,
    contacts,
    apiRes,
  ] = await Promise.allSettled([
    adminService.getUsersStats(),
    adminService.getSubscriptionStats(),
    adminService.getAlertSummary(),
    adminService.getAuditStats({}),
    adminService.getImageStats(),
    adminService.getPageViewsSummary({}),
    adminService.getContactMessages(null, 1000, 0),
    adminService.getPerformance({ windowMinutes: 1440, limit: 50 }),
  ]);

  let siteStats: PageViewsSummaryResponse | null = null;
  if (
    siteStatsRes.status === "fulfilled" &&
    siteStatsRes.value?.success &&
    siteStatsRes.value?.data
  ) {
    siteStats = siteStatsRes.value.data;
  }

  let contactPending = 0;
  let contactTotal = 0;
  if (contacts.status === "fulfilled" && contacts.value) {
    const contactData = contacts.value.data || [];
    contactTotal = contacts.value.total || contactData.length;
    contactPending = contactData.filter(
      (c: { status: string }) => c.status === "pending",
    ).length;
  }

  let apiMetrics: ApiKpis | null = null;
  if (apiRes.status === "fulfilled" && apiRes.value?.success) {
    const metrics = apiRes.value.metrics as Record<string, unknown>[];
    apiMetrics = computeApiKpis(metrics);
  }

  return {
    userStats: userStats.status === "fulfilled" ? userStats.value : null,
    subStats: subStats.status === "fulfilled" ? subStats.value : null,
    alertSummary:
      alertSummary.status === "fulfilled" ? alertSummary.value : null,
    auditStats: auditStats.status === "fulfilled" ? auditStats.value : null,
    imageStats: imageStats.status === "fulfilled" ? imageStats.value : null,
    siteStats,
    contactPending,
    contactTotal,
    apiMetrics,
  };
}

/**
 * Hook SWR pour les données de la page Admin Overview.
 */
export function useAdminOverview() {
  const { data, isLoading, error, mutate } = useSWR<OverviewData>(
    ADMIN_OVERVIEW_KEY,
    overviewFetcher,
    { dedupingInterval: 60_000 },
  );
  return {
    data,
    isLoading,
    error,
    mutate,
  };
}
