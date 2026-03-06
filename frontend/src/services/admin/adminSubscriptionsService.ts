/**
 * Service d'administration pour la gestion des abonnements.
 */

import { fetchJsonWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";

export interface SubscriptionRecord {
  id: string;
  user_id: string;
  email: string | null;
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  current_period_end: string | null;
  newsletter_enabled: boolean;
  notifications_enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
  [key: string]: unknown;
}

export interface SubscriptionStatsResponse {
  total_subscriptions: number;
  plans: Record<string, number>;
  statuses: Record<string, number>;
  premium_count: number;
  stripe_count: number;
  recent_subscriptions_7d: number;
  expiring_soon_30d: number;
  conversion_rate: number;
  churn_rate: number;
  monthly_history: Array<{ month: string; free: number; premium: number }>;
}

export async function getSubscriptions({
  plan,
  status,
  search,
  hasStripe,
  limit = 50,
  offset = 0,
}: {
  plan?: string | null;
  status?: string | null;
  search?: string | null;
  hasStripe?: boolean | null;
  limit?: number;
  offset?: number;
} = {}): Promise<{ subscriptions: SubscriptionRecord[]; total: number }> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/subscriptions`);
    if (plan) url.searchParams.set("plan", plan);
    if (status) url.searchParams.set("status", status);
    if (search) url.searchParams.set("search", search);
    if (hasStripe !== null && hasStripe !== undefined)
      url.searchParams.set("has_stripe", String(hasStripe));
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));

    return await fetchJsonWithAuth<{
      subscriptions: SubscriptionRecord[];
      total: number;
    }>(
      url.toString(),
      { method: "GET" },
      "Erreur lors de la récupération des abonnements",
    );
  } catch (err: unknown) {
    logError(
      "[AdminSubscriptionsService] Erreur récupération abonnements:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadSubscriptions"));
    throw err;
  }
}

export async function getSubscriptionStats(): Promise<SubscriptionStatsResponse> {
  try {
    return await fetchJsonWithAuth<SubscriptionStatsResponse>(
      `${getApiBaseUrl()}/admin/api/subscriptions/stats`,
      { method: "GET" },
      "Erreur lors de la récupération des stats abonnements",
    );
  } catch (err: unknown) {
    logError(
      "[AdminSubscriptionsService] Erreur récupération stats abonnements:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadSubStats"));
    throw err;
  }
}

export async function getSubscriptionHistory({
  limit = 50,
  offset = 0,
}: {
  limit?: number;
  offset?: number;
} = {}): Promise<{ history: SubscriptionRecord[]; total: number }> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/subscriptions/history`);
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));

    return await fetchJsonWithAuth<{
      history: SubscriptionRecord[];
      total: number;
    }>(
      url.toString(),
      { method: "GET" },
      "Erreur lors de la récupération de l'historique",
    );
  } catch (err: unknown) {
    logError(
      "[AdminSubscriptionsService] Erreur récupération historique abonnements:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadSubHistory"));
    throw err;
  }
}

export async function updateSubscription(
  subscriptionId: string,
  updates: { plan?: string; status?: string; current_period_end?: string },
): Promise<SubscriptionRecord> {
  try {
    return await fetchJsonWithAuth<SubscriptionRecord>(
      `${getApiBaseUrl()}/admin/api/subscriptions/${subscriptionId}`,
      { method: "PUT", body: JSON.stringify(updates) },
      "Erreur lors de la mise à jour de l'abonnement",
    );
  } catch (err: unknown) {
    logError("[AdminSubscriptionsService] Erreur mise à jour abonnement:", err);
    showErrorToast(getToastT()("admin.toast.subUpdate"));
    throw err;
  }
}
