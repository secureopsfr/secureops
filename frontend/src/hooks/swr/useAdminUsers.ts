"use client";

import useSWR from "swr";
import * as adminUsersService from "../../services/admin/adminUsersService";
import type {
  UsersResponse,
  UsersStatsResponse,
} from "../../services/admin/adminUsersService";
import { adminUsersKey, ADMIN_USER_STATS_KEY } from "./keys";

/**
 * Hook SWR pour la liste des utilisateurs admin.
 *
 * Returns:
 *   data (UsersResponse), isLoading, mutate.
 */
export function useAdminUsers(params: {
  search: string | null;
  plan: string | null;
  status: string | null;
  limit: number;
  offset: number;
}) {
  const key = adminUsersKey(params);
  const { data, isLoading, mutate } = useSWR(key, () =>
    adminUsersService.getUsers(params),
  );
  return {
    data: data as UsersResponse | undefined,
    users: data?.users ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}

/**
 * Hook SWR pour les stats utilisateurs admin.
 */
export function useAdminUsersStats() {
  const { data, isLoading, mutate } = useSWR(
    ADMIN_USER_STATS_KEY,
    () => adminUsersService.getUsersStats(),
    { dedupingInterval: 60_000 },
  );
  return {
    data: data as UsersStatsResponse | undefined,
    isLoading,
    mutate,
  };
}
