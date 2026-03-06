"use client";

import useSWR from "swr";
import * as adminContactService from "../../services/admin/adminContactService";
import type {
  PaginatedResponse,
  ContactMessageRecord,
} from "../../services/admin/adminContactService";
import { adminContactsKey } from "./keys";

/**
 * Hook SWR pour la liste des messages de contact admin.
 *
 * Returns:
 *   data (PaginatedResponse), isLoading, mutate.
 */
export function useAdminContacts(params: {
  status: string | null;
  limit: number;
  offset: number;
}) {
  const key = adminContactsKey(params);
  const { data, isLoading, mutate } = useSWR(key, () =>
    adminContactService.getContactMessages(
      params.status,
      params.limit,
      params.offset,
    ),
  );
  return {
    data: data as PaginatedResponse<ContactMessageRecord> | undefined,
    messages: data?.data ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}
