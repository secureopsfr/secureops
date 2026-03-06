"use client";

import useSWR from "swr";
import * as adminAuditService from "../../services/admin/adminAuditService";
import type {
  AuditLogEntry,
  AuditStatsResponse,
} from "../../services/admin/adminAuditService";
import { adminAuditLogsKey, adminAuditStatsKey } from "./keys";

/**
 * Hook SWR pour les logs d'audit admin.
 * Mappe entity (clé) vers entityType (service).
 */
export function useAdminAuditLogs(params: {
  entity: string | null;
  action: string | null;
  limit: number;
  offset: number;
}) {
  const key = adminAuditLogsKey(params);
  const { data, isLoading, mutate } = useSWR(key, () =>
    adminAuditService.getAuditLogs({
      entityType: params.entity,
      action: params.action,
      limit: params.limit,
      offset: params.offset,
    }),
  );
  return {
    data,
    logs: (data?.logs as AuditLogEntry[]) ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}

/**
 * Hook SWR pour les stats d'audit admin.
 */
export function useAdminAuditStats() {
  const { data, isLoading, mutate } = useSWR(
    adminAuditStatsKey(),
    () => adminAuditService.getAuditStats(),
    { dedupingInterval: 60_000 },
  );
  return {
    data: data as AuditStatsResponse | undefined,
    isLoading,
    mutate,
  };
}
