/**
 * Service d'administration pour la gestion des messages de contact.
 */

import { fetchWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError, log } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";

export interface ContactMessageRecord {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  subject: string;
  message: string;
  status: string;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export async function getContactMessages(
  status: string | null = null,
  limit: number = 50,
  offset: number = 0,
): Promise<PaginatedResponse<ContactMessageRecord>> {
  try {
    let url = `${getApiBaseUrl()}/admin/api/contact?limit=${limit}&offset=${offset}`;
    if (status) {
      url += `&status=${status}`;
    }
    log("[AdminContactService] Récupération messages contact:", url);

    const response = await fetchWithAuth(url, {
      method: "GET",
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      logError(
        "[AdminContactService] Erreur récupération messages:",
        errorData,
      );
      throw new Error(
        errorData.detail ||
          "Erreur lors de la récupération des messages de contact",
      );
    }

    const result = await response.json();
    log("[AdminContactService] Messages de contact récupérés");
    return result;
  } catch (err: unknown) {
    logError(
      "[AdminContactService] Erreur lors de la récupération des messages de contact:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadContacts"));
    throw err;
  }
}

export async function updateContactMessageStatus(
  messageId: number,
  status: string,
): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/contact/${messageId}`,
      {
        method: "PUT",
        body: JSON.stringify({ status }),
      },
    );

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail ||
          "Erreur lors de la mise à jour du statut du message",
      );
    }

    return await response.json();
  } catch (err: unknown) {
    logError("[AdminContactService] Erreur mise à jour statut message:", err);
    showErrorToast(getToastT()("admin.toast.updateContactStatus"));
    throw err;
  }
}

export async function deleteContactMessage(
  messageId: number,
): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/contact/${messageId}`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la suppression du message",
      );
    }

    return await response.json();
  } catch (err: unknown) {
    logError("[AdminContactService] Erreur suppression message contact:", err);
    showErrorToast(getToastT()("admin.toast.deleteContact"));
    throw err;
  }
}

export async function replyToContactMessage(
  messageId: number,
  body: string,
): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/contact/${messageId}/reply`,
      {
        method: "POST",
        body: JSON.stringify({ body }),
      },
    );

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de l'envoi de la réponse",
      );
    }

    return await response.json();
  } catch (err: unknown) {
    logError("[AdminContactService] Erreur envoi réponse contact:", err);
    showErrorToast(getToastT()("admin.toast.sendContactReply"));
    throw err;
  }
}
