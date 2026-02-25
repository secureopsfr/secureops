/**
 * Service d'administration pour les journaux d'audit.
 */

import { fetchWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";

export interface AuditLogEntry {
  id: string;
  admin_email: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string | null;
  [key: string]: unknown;
}

export interface AuditStatsResponse {
  total_actions: number;
  by_action: Record<string, number>;
  by_entity: Record<string, number>;
  top_admins: Array<{ email: string; count: number }>;
}

export async function getAuditLogs({
  entityType,
  action,
  adminEmail,
  entityId,
  windowMinutes,
  limit = 100,
  offset = 0,
}: {
  entityType?: string | null;
  action?: string | null;
  adminEmail?: string | null;
  entityId?: string | null;
  windowMinutes?: number | null;
  limit?: number;
  offset?: number;
} = {}): Promise<{ logs: AuditLogEntry[]; total: number }> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/audit`);
    if (entityType) url.searchParams.set("entity_type", entityType);
    if (action) url.searchParams.set("action", action);
    if (adminEmail) url.searchParams.set("admin_email", adminEmail);
    if (entityId) url.searchParams.set("entity_id", entityId);
    if (windowMinutes)
      url.searchParams.set("window_minutes", String(windowMinutes));
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));

    const response = await fetchWithAuth(url.toString(), { method: "GET" });
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la récupération du journal",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminAuditService] Erreur récupération audit logs:", err);
    showErrorToast(getToastT()("admin.toast.loadAuditLog"));
    throw err;
  }
}

export async function getAuditStats({
  windowMinutes,
}: {
  windowMinutes?: number | null;
} = {}): Promise<AuditStatsResponse> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/audit/stats`);
    if (windowMinutes)
      url.searchParams.set("window_minutes", String(windowMinutes));

    const response = await fetchWithAuth(url.toString(), { method: "GET" });
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la récupération des stats audit",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminAuditService] Erreur récupération audit stats:", err);
    showErrorToast(getToastT()("admin.toast.loadAuditStats"));
    throw err;
  }
}
