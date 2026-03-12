/**
 * Service d'administration pour la gestion des emails (Newsletter & Notifications).
 */

import { fetchJsonWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";

export interface EmailRecord {
  id: number;
  subject: string;
  content: string;
  status?: string;
  created_at?: string;
  sent_at?: string;
  scheduled_at?: string;
  [key: string]: unknown;
}

export interface SubscriberRecord {
  email: string;
  subscribed_at?: string;
  [key: string]: unknown;
}

// ========== Newsletter ==========

export async function getNewsletterEmails(
  limit: number = 50,
  offset: number = 0,
): Promise<EmailRecord[]> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/newsletter`);
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));

    const result = await fetchJsonWithAuth<
      EmailRecord[] | { data?: EmailRecord[] }
    >(
      url.toString(),
      { method: "GET" },
      "Erreur lors de la récupération des emails newsletter",
    );
    return Array.isArray(result) ? result : (result?.data ?? []);
  } catch (err: unknown) {
    logError(
      "[AdminEmailsService] Erreur récupération emails newsletter:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadNewsletterEmails"));
    throw err;
  }
}

export async function createNewsletterEmail(emailData: {
  subject: string;
  content: string;
  template_name?: string;
}): Promise<EmailRecord> {
  try {
    return await fetchJsonWithAuth<EmailRecord>(
      `${getApiBaseUrl()}/admin/api/newsletter`,
      { method: "POST", body: JSON.stringify(emailData) },
      "Erreur lors de la création de l'email newsletter",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur création email newsletter:", err);
    showErrorToast(getToastT()("admin.toast.createNewsletterEmail"));
    throw err;
  }
}

export async function updateNewsletterEmail(
  emailId: number,
  emailData: { subject: string; content: string; template_name?: string },
): Promise<EmailRecord> {
  try {
    return await fetchJsonWithAuth<EmailRecord>(
      `${getApiBaseUrl()}/admin/api/newsletter/${emailId}`,
      { method: "PUT", body: JSON.stringify(emailData) },
      "Erreur lors de la mise à jour de l'email newsletter",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur mise à jour email newsletter:", err);
    showErrorToast(getToastT()("admin.toast.updateNewsletterEmail"));
    throw err;
  }
}

export async function deleteNewsletterEmail(
  emailId: number,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/newsletter/${emailId}`,
      { method: "DELETE" },
      "Erreur lors de la suppression de l'email newsletter",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur suppression email newsletter:", err);
    showErrorToast(getToastT()("admin.toast.deleteNewsletterEmail"));
    throw err;
  }
}

export async function sendNewsletterEmail(
  emailId: number,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/newsletter/send`,
      { method: "POST", body: JSON.stringify({ email_id: emailId }) },
      "Erreur lors de l'envoi de l'email newsletter",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur envoi email newsletter:", err);
    showErrorToast(getToastT()("admin.toast.sendNewsletterEmail"));
    throw err;
  }
}

export async function scheduleNewsletterEmail(
  emailId: number,
  scheduledDate: Date,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/newsletter/schedule`,
      {
        method: "POST",
        body: JSON.stringify({
          email_id: emailId,
          scheduled_at: scheduledDate.toISOString(),
        }),
      },
      "Erreur lors de la programmation de l'email newsletter",
    );
  } catch (err: unknown) {
    logError(
      "[AdminEmailsService] Erreur programmation email newsletter:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.scheduleNewsletterEmail"));
    throw err;
  }
}

export async function cancelScheduledEmail(
  emailId: number,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/newsletter/cancel-schedule/${emailId}`,
      { method: "POST" },
      "Erreur lors de l'annulation de l'email programmé",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur annulation email programmé:", err);
    showErrorToast(getToastT()("admin.toast.cancelScheduleEmail"));
    throw err;
  }
}

export async function getMailingList(): Promise<SubscriberRecord[]> {
  try {
    const data = await fetchJsonWithAuth<
      { entries?: SubscriberRecord[] } | SubscriberRecord[]
    >(
      `${getApiBaseUrl()}/admin/api/mailing-list`,
      { method: "GET" },
      "Erreur lors de la récupération de la liste de diffusion",
    );
    const withEntries = data as { entries?: SubscriberRecord[] };
    return Array.isArray(withEntries.entries)
      ? withEntries.entries
      : Array.isArray(data)
        ? (data as SubscriberRecord[])
        : [];
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur récupération mailing list:", err);
    showErrorToast(getToastT()("admin.toast.loadSubscribers"));
    throw err;
  }
}

export async function deleteSubscriber(
  email: string,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/mailing-list/${encodeURIComponent(email)}`,
      { method: "DELETE" },
      "Erreur lors de la suppression de l'abonné",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur suppression abonné:", err);
    showErrorToast(getToastT()("admin.toast.deleteSubscriber"));
    throw err;
  }
}

// ========== Notifications ==========

export async function getNotificationEmails(
  limit: number = 50,
  offset: number = 0,
): Promise<EmailRecord[]> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/notifications`);
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));

    const result = await fetchJsonWithAuth<
      EmailRecord[] | { data?: EmailRecord[] }
    >(
      url.toString(),
      { method: "GET" },
      "Erreur lors de la récupération des emails de notification",
    );
    return Array.isArray(result) ? result : (result?.data ?? []);
  } catch (err: unknown) {
    logError(
      "[AdminEmailsService] Erreur récupération emails notifications:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadNotificationEmails"));
    throw err;
  }
}

export async function createNotificationEmail(emailData: {
  subject: string;
  content: string;
  template_name?: string;
}): Promise<EmailRecord> {
  try {
    return await fetchJsonWithAuth<EmailRecord>(
      `${getApiBaseUrl()}/admin/api/notifications`,
      { method: "POST", body: JSON.stringify(emailData) },
      "Erreur lors de la création de l'email de notification",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur création email notification:", err);
    showErrorToast(getToastT()("admin.toast.createNotificationEmail"));
    throw err;
  }
}

export async function updateNotificationEmail(
  emailId: number,
  emailData: { subject: string; content: string; template_name?: string },
): Promise<EmailRecord> {
  try {
    return await fetchJsonWithAuth<EmailRecord>(
      `${getApiBaseUrl()}/admin/api/notifications/${emailId}`,
      { method: "PUT", body: JSON.stringify(emailData) },
      "Erreur lors de la mise à jour de l'email de notification",
    );
  } catch (err: unknown) {
    logError(
      "[AdminEmailsService] Erreur mise à jour email notification:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.updateNotificationEmail"));
    throw err;
  }
}

export async function deleteNotificationEmail(
  emailId: number,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/notifications/${emailId}`,
      { method: "DELETE" },
      "Erreur lors de la suppression de l'email de notification",
    );
  } catch (err: unknown) {
    logError(
      "[AdminEmailsService] Erreur suppression email notification:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.deleteNotificationEmail"));
    throw err;
  }
}

export async function sendNotificationEmail(
  emailId: number,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/notifications/send`,
      { method: "POST", body: JSON.stringify({ email_id: emailId }) },
      "Erreur lors de l'envoi de l'email de notification",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur envoi email notification:", err);
    showErrorToast(getToastT()("admin.toast.sendNotificationEmail"));
    throw err;
  }
}

export async function scheduleNotificationEmail(
  emailId: number,
  scheduledDate: Date,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/notifications/schedule`,
      {
        method: "POST",
        body: JSON.stringify({
          email_id: emailId,
          scheduled_at: scheduledDate.toISOString(),
        }),
      },
      "Erreur lors de la programmation de l'email de notification",
    );
  } catch (err: unknown) {
    logError(
      "[AdminEmailsService] Erreur programmation email notification:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.scheduleNotificationEmail"));
    throw err;
  }
}

export async function cancelScheduledNotification(
  emailId: number,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/notifications/cancel-schedule/${emailId}`,
      { method: "POST" },
      "Erreur lors de l'annulation de l'email programmé",
    );
  } catch (err: unknown) {
    logError("[AdminEmailsService] Erreur annulation email programmé:", err);
    showErrorToast(getToastT()("admin.toast.cancelScheduleNotification"));
    throw err;
  }
}

export async function getNotificationSubscribers(): Promise<
  SubscriberRecord[]
> {
  try {
    const data = await fetchJsonWithAuth<
      { entries?: SubscriberRecord[] } | SubscriberRecord[]
    >(
      `${getApiBaseUrl()}/admin/api/notifications/subscribers`,
      { method: "GET" },
      "Erreur lors de la récupération des abonnés aux notifications",
    );
    const withEntries = data as { entries?: SubscriberRecord[] };
    return Array.isArray(withEntries.entries)
      ? withEntries.entries
      : Array.isArray(data)
        ? (data as SubscriberRecord[])
        : [];
  } catch (err: unknown) {
    logError(
      "[AdminEmailsService] Erreur récupération abonnés notifications:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadNotificationSubscribers"));
    throw err;
  }
}
