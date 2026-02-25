/**
 * Client API centralisé pour gérer les appels authentifiés avec gestion automatique du rafraîchissement du token.
 */

import { fetchAuthSession } from "aws-amplify/auth";
import { log, error } from "./logger";

const DEFAULT_GATEWAY = "http://localhost:8000";

const getApiBaseUrl = (): string => {
  const raw =
    typeof window === "undefined"
      ? (process.env.GATEWAY_URL ?? process.env.NEXT_PUBLIC_GATEWAY_URL)
      : process.env.NEXT_PUBLIC_GATEWAY_URL;
  return (raw && raw.trim()) || DEFAULT_GATEWAY;
};

export { getApiBaseUrl };

/**
 * Effectue un appel API avec gestion automatique du rafraîchissement du token.
 * Cette fonction est utilisée par tous les services pour maintenir une cohérence.
 */
export async function fetchWithAuth(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const { headers = {}, ...rest } = options;

  // Récupérer le token depuis la session Amplify
  let token: string | undefined;
  try {
    const session = await fetchAuthSession();
    token = session.tokens?.accessToken?.toString();
  } catch (err) {
    error("[ApiClient] Impossible de récupérer le token:", err);
    throw new Error("Authentification requise");
  }

  const finalHeaders: HeadersInit = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...headers,
  };

  let response = await fetch(url, {
    ...rest,
    headers: finalHeaders,
  });

  // Si 401, essayer de rafraîchir le token et réessayer une seule fois
  if (response.status === 401) {
    log("[ApiClient] Token expiré (401), rafraîchissement et retry...");
    try {
      const session = await fetchAuthSession({ forceRefresh: true });
      const refreshedToken = session.tokens?.accessToken?.toString();

      if (refreshedToken) {
        const refreshedHeaders: HeadersInit = {
          ...finalHeaders,
          Authorization: `Bearer ${refreshedToken}`,
        };

        response = await fetch(url, {
          ...rest,
          headers: refreshedHeaders,
        });

        if (response.ok) {
          log("[ApiClient] Token rafraîchi avec succès, requête réussie");
        } else if (response.status === 401) {
          error("[ApiClient] Token toujours invalide après rafraîchissement");
        }
      }
    } catch (refreshErr) {
      error("[ApiClient] Impossible de rafraîchir le token:", refreshErr);
    }
  }

  return response;
}
