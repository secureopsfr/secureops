/**
 * Service pour envoyer les messages de contact.
 * Endpoint public (pas d'authentification requise).
 */

import { showErrorToast } from "../utils/toastNotifications";
import { log, error } from "../utils/logger";

import { getApiBaseUrl } from "../utils/apiClient";

export interface ContactMessageRequest {
  first_name: string;
  last_name: string;
  email: string;
  subject: string;
  message: string;
  turnstile_token: string;
}

export interface ContactMessageResponse {
  id: number;
  message: string;
}

/**
 * Envoie un message de contact.
 *
 * @param contactData - Données du message de contact incluant le token Turnstile
 * @returns Promise<ContactMessageResponse> - Réponse du serveur avec message de confirmation
 * @throws Error si l'envoi échoue
 */
export async function sendContactMessage(
  contactData: ContactMessageRequest,
): Promise<ContactMessageResponse> {
  try {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/api/contact`;
    log("[ContactService] Envoi message contact:", url);

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(contactData),
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      error("[ContactService] Erreur envoi contact:", errorData);
      throw new Error(errorData.detail || "Erreur lors de l'envoi du message");
    }

    const data = await response.json();
    log("[ContactService] Message contact envoyé");
    return data;
  } catch (err: unknown) {
    error("[ContactService] Erreur lors de l'envoi du message contact:", err);
    showErrorToast(
      err instanceof Error ? err.message : "Impossible d'envoyer le message.",
    );
    throw err;
  }
}
