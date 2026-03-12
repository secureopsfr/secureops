/**
 * Service d'administration pour la gestion des alertes.
 */

import { fetchJsonWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";

export interface AlertRuleRecord {
  id: string;
  name: string;
  metric: string;
  condition: string;
  threshold: number;
  window_minutes: number;
  service_filter: string | null;
  notify_email: boolean;
  enabled: boolean;
  cooldown_minutes: number;
  created_at: string | null;
  updated_at: string | null;
  [key: string]: unknown;
}

export interface AlertEventRecord {
  id: string;
  rule_id: string | null;
  rule_name: string;
  metric: string;
  current_value: number;
  threshold: number;
  severity: string;
  message: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  created_at: string | null;
  [key: string]: unknown;
}

export interface AlertSummaryResponse {
  unacknowledged: number;
  recent_24h: number;
  critical: number;
  active_rules: number;
}

export async function getAlertRules(): Promise<AlertRuleRecord[]> {
  try {
    return await fetchJsonWithAuth<AlertRuleRecord[]>(
      `${getApiBaseUrl()}/admin/api/alerts/rules`,
      { method: "GET" },
      "Erreur lors de la récupération des règles d'alertes",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur récupération règles alertes:", err);
    showErrorToast(getToastT()("admin.toast.loadAlertRules"));
    throw err;
  }
}

export async function createAlertRule(
  data: Omit<AlertRuleRecord, "id" | "created_at" | "updated_at">,
): Promise<AlertRuleRecord> {
  try {
    return await fetchJsonWithAuth<AlertRuleRecord>(
      `${getApiBaseUrl()}/admin/api/alerts/rules`,
      { method: "POST", body: JSON.stringify(data) },
      "Erreur création règle",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur création règle alerte:", err);
    showErrorToast(getToastT()("admin.toast.createAlertRule"));
    throw err;
  }
}

export async function updateAlertRule(
  ruleId: string,
  data: Partial<AlertRuleRecord>,
): Promise<AlertRuleRecord> {
  try {
    return await fetchJsonWithAuth<AlertRuleRecord>(
      `${getApiBaseUrl()}/admin/api/alerts/rules/${ruleId}`,
      { method: "PUT", body: JSON.stringify(data) },
      "Erreur mise à jour règle",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur mise à jour règle alerte:", err);
    showErrorToast(getToastT()("admin.toast.updateAlertRule"));
    throw err;
  }
}

export async function deleteAlertRule(
  ruleId: string,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/alerts/rules/${ruleId}`,
      { method: "DELETE" },
      "Erreur suppression règle",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur suppression règle alerte:", err);
    showErrorToast(getToastT()("admin.toast.deleteAlertRule"));
    throw err;
  }
}

export async function toggleAlertRule(
  ruleId: string,
): Promise<AlertRuleRecord> {
  try {
    return await fetchJsonWithAuth<AlertRuleRecord>(
      `${getApiBaseUrl()}/admin/api/alerts/rules/${ruleId}/toggle`,
      { method: "POST" },
      "Erreur lors du basculement de la règle",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur toggle règle alerte:", err);
    showErrorToast(getToastT()("admin.toast.toggleAlertRule"));
    throw err;
  }
}

export async function getAlertEvents({
  severity,
  acknowledged,
  limit = 50,
  offset = 0,
}: {
  severity?: string | null;
  acknowledged?: boolean | null;
  limit?: number;
  offset?: number;
} = {}): Promise<{ events: AlertEventRecord[]; total: number }> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/alerts/events`);
    if (severity) url.searchParams.set("severity", severity);
    if (acknowledged !== null && acknowledged !== undefined)
      url.searchParams.set("acknowledged", String(acknowledged));
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));

    return await fetchJsonWithAuth<{
      events: AlertEventRecord[];
      total: number;
    }>(
      url.toString(),
      { method: "GET" },
      "Erreur lors de la récupération des événements d'alerte",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur récupération alertes:", err);
    showErrorToast(getToastT()("admin.toast.loadAlerts"));
    throw err;
  }
}

export async function acknowledgeAlert(
  eventId: string,
  adminEmail: string,
): Promise<AlertEventRecord> {
  try {
    return await fetchJsonWithAuth<AlertEventRecord>(
      `${getApiBaseUrl()}/admin/api/alerts/events/${eventId}/acknowledge`,
      {
        method: "POST",
        body: JSON.stringify({ admin_email: adminEmail }),
      },
      "Erreur lors de l'acquittement de l'alerte",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur acquittement alerte:", err);
    showErrorToast(getToastT()("admin.toast.acknowledgeAlert"));
    throw err;
  }
}

export async function acknowledgeAllAlerts(
  adminEmail: string,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/alerts/events/acknowledge-all`,
      {
        method: "POST",
        body: JSON.stringify({ admin_email: adminEmail }),
      },
      "Erreur lors de l'acquittement de toutes les alertes",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur acquittement toutes alertes:", err);
    showErrorToast(getToastT()("admin.toast.acknowledgeAllAlerts"));
    throw err;
  }
}

export async function checkAlerts(): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/alerts/check`,
      { method: "POST" },
      "Erreur lors de la vérification des alertes",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur vérification alertes:", err);
    showErrorToast(getToastT()("admin.toast.checkAlerts"));
    throw err;
  }
}

export async function getAlertSummary(): Promise<AlertSummaryResponse> {
  try {
    return await fetchJsonWithAuth<AlertSummaryResponse>(
      `${getApiBaseUrl()}/admin/api/alerts/summary`,
      { method: "GET" },
      "Erreur lors de la récupération du résumé des alertes",
    );
  } catch (err: unknown) {
    logError("[AdminAlertsService] Erreur récupération résumé alertes:", err);
    showErrorToast(getToastT()("admin.toast.loadAlertSummary"));
    throw err;
  }
}
