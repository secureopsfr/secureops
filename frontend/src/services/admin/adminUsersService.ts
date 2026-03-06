/**
 * Service d'administration pour la gestion des utilisateurs.
 */

import { fetchJsonWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";

export interface UserRecord {
  id: string;
  cognito_sub: string;
  email: string;
  created_at: string | null;
  subscription_id: string | null;
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  newsletter_enabled: boolean;
  notifications_enabled: boolean;
  current_period_end: string | null;
  updated_at: string | null;
  cognito_groups?: string[];
  cognito_status?: string | null;
  cognito_enabled?: boolean;
  [key: string]: unknown;
}

export interface UsersResponse {
  users: UserRecord[];
  total: number;
}

export interface UsersStatsResponse {
  total_users: number;
  recent_users_7d: number;
  plans: Record<string, number>;
  statuses: Record<string, number>;
  newsletter_subscribers: number;
  notification_subscribers: number;
}

export async function getUsers({
  search,
  plan,
  status,
  limit = 50,
  offset = 0,
}: {
  search?: string | null;
  plan?: string | null;
  status?: string | null;
  limit?: number;
  offset?: number;
} = {}): Promise<UsersResponse> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/users`);
    if (search) url.searchParams.set("search", search);
    if (plan) url.searchParams.set("plan", plan);
    if (status) url.searchParams.set("status", status);
    url.searchParams.set("limit", limit.toString());
    url.searchParams.set("offset", offset.toString());

    return await fetchJsonWithAuth<UsersResponse>(
      url.toString(),
      { method: "GET" },
      "Erreur lors de la récupération des utilisateurs",
    );
  } catch (err: unknown) {
    logError("[AdminUsersService] Erreur récupération utilisateurs:", err);
    showErrorToast(getToastT()("admin.toast.loadUsers"));
    throw err;
  }
}

export async function getUserDetail(userId: string): Promise<UserRecord> {
  try {
    return await fetchJsonWithAuth<UserRecord>(
      `${getApiBaseUrl()}/admin/api/users/${userId}`,
      { method: "GET" },
      "Erreur lors de la récupération du détail utilisateur",
    );
  } catch (err: unknown) {
    logError(
      "[AdminUsersService] Erreur récupération détail utilisateur:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadUserDetail"));
    throw err;
  }
}

export async function getUsersStats(): Promise<UsersStatsResponse> {
  try {
    return await fetchJsonWithAuth<UsersStatsResponse>(
      `${getApiBaseUrl()}/admin/api/users/stats`,
      { method: "GET" },
      "Erreur lors de la récupération des stats",
    );
  } catch (err: unknown) {
    logError(
      "[AdminUsersService] Erreur récupération stats utilisateurs:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadStats"));
    throw err;
  }
}

export async function updateUserGroup(
  userId: string,
  group: string,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/users/${userId}/group`,
      { method: "PUT", body: JSON.stringify({ group }) },
      "Erreur lors du changement de groupe",
    );
  } catch (err: unknown) {
    logError("[AdminUsersService] Erreur changement groupe utilisateur:", err);
    showErrorToast(getToastT()("admin.toast.groupChange"));
    throw err;
  }
}

export async function toggleUserStatus(
  userId: string,
  action: "disable" | "enable",
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/users/${userId}/status`,
      { method: "PUT", body: JSON.stringify({ action }) },
      "Erreur lors du changement de statut",
    );
  } catch (err: unknown) {
    logError("[AdminUsersService] Erreur changement statut utilisateur:", err);
    showErrorToast(getToastT()("admin.toast.statusChange"));
    throw err;
  }
}
