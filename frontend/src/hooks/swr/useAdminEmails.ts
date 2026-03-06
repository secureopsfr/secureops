"use client";

import useSWR from "swr";
import * as adminEmailsService from "../../services/admin/adminEmailsService";
import type {
  EmailRecord,
  SubscriberRecord,
} from "../../services/admin/adminEmailsService";
import { adminEmailsKey, adminSubscribersKey } from "./keys";

export type AdminEmailType = "newsletter" | "notification";

/**
 * Hook SWR pour la liste des emails admin (newsletter ou notifications).
 */
export function useAdminEmails(type: AdminEmailType, limit = 50, offset = 0) {
  const key = adminEmailsKey(type);
  const fetcher =
    type === "newsletter"
      ? () => adminEmailsService.getNewsletterEmails(limit, offset)
      : () => adminEmailsService.getNotificationEmails(limit, offset);
  const { data, isLoading, error, mutate } = useSWR(key, fetcher);
  const emails: EmailRecord[] = Array.isArray(data) ? data : [];
  return {
    data: emails,
    emails,
    isLoading,
    error,
    mutate,
  };
}

/**
 * Hook SWR pour la liste des abonnés (newsletter ou notifications).
 */
export function useAdminSubscribers(type: AdminEmailType) {
  const key = adminSubscribersKey(type);
  const fetcher =
    type === "newsletter"
      ? () => adminEmailsService.getMailingList()
      : () => adminEmailsService.getNotificationSubscribers();
  const { data, isLoading, error, mutate } = useSWR(key, fetcher);
  const subscribers: SubscriberRecord[] = Array.isArray(data) ? data : [];
  return {
    data: subscribers,
    subscribers,
    isLoading,
    error,
    mutate,
  };
}
