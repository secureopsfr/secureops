/**
 * Client API centralisé pour gérer les appels authentifiés avec gestion automatique du rafraîchissement du token.
 */

import { fetchAuthSession, signOut } from "aws-amplify/auth";
import { log, error, warn } from "./logger";

const DEFAULT_GATEWAY = "http://localhost:8000";

const getApiBaseUrl = (): string => {
  const raw =
    typeof window === "undefined"
      ? (process.env.GATEWAY_URL ?? process.env.NEXT_PUBLIC_GATEWAY_URL)
      : process.env.NEXT_PUBLIC_GATEWAY_URL;
  return (raw && raw.trim()) || DEFAULT_GATEWAY;
};

export { getApiBaseUrl };

async function getBearerToken(forceRefresh = false): Promise<string | null> {
  const session = await fetchAuthSession({ forceRefresh });
  return (
    session.tokens?.accessToken?.toString() ??
    session.tokens?.idToken?.toString() ??
    null
  );
}

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
  let token: string | null = null;
  try {
    token = await getBearerToken(false);
    if (!token) {
      log("[ApiClient] Aucun token initial, tentative de refresh...");
      token = await getBearerToken(true);
    }
  } catch (err) {
    error("[ApiClient] Impossible de récupérer le token:", err);
    throw new Error("Authentification requise");
  }

  if (!token) {
    warn("[ApiClient] Aucun token disponible après refresh, déconnexion");
    try {
      await signOut();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("auth:signOut"));
      }
    } catch (signOutErr) {
      error("[ApiClient] Erreur lors de la déconnexion:", signOutErr);
    }
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
      const refreshedToken = await getBearerToken(true);

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
          warn(
            "[ApiClient] 401 après retry — peut être un refus d'accès (autorisation) ou session expirée",
          );
          // Ne pas déconnecter : un 401 peut signifier "accès refusé" (ex. endpoint
          // admin pour un user non-admin), pas forcément "session expirée"
        }
      } else {
        warn(
          "[ApiClient] Impossible d'obtenir un token rafraîchi, session expirée",
        );
        try {
          await signOut();
          if (typeof window !== "undefined") {
            window.dispatchEvent(new CustomEvent("auth:signOut"));
          }
        } catch (signOutErr) {
          error("[ApiClient] Erreur lors de la déconnexion:", signOutErr);
        }
      }
    } catch (refreshErr) {
      error("[ApiClient] Impossible de rafraîchir le token:", refreshErr);
    }
  }

  return response;
}

/**
 * Vérifie si la réponse est ok ; sinon parse le JSON d'erreur et lance une Error.
 * Ne retourne jamais si response.ok est false (type never).
 *
 * @param response - Réponse fetch à vérifier
 * @param fallbackMessage - Message utilisé si le body n'a pas de détail
 * @throws Error avec le message d'erreur de l'API ou le fallback
 */
export async function handleFetchError(
  response: Response,
  fallbackMessage: string,
): Promise<never> {
  const err = await response.json().catch(() => ({}));
  const raw = (err as { detail?: string | string[] }).detail;
  const detail = Array.isArray(raw) ? raw.join(", ") : (raw ?? fallbackMessage);
  throw new Error(typeof detail === "string" ? detail : fallbackMessage);
}

/**
 * Appel fetch sans auth : vérifie response.ok, sinon parse le JSON d'erreur et lance Error.
 *
 * @param url - URL à appeler
 * @param options - Options fetch (method, body, headers, etc.)
 * @param fallbackError - Message d'erreur par défaut si le body n'a pas de détail
 * @returns Promise<T> - Données JSON parsées
 */
export async function fetchJson<T>(
  url: string,
  options: RequestInit = {},
  fallbackError: string,
): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    await handleFetchError(response, fallbackError);
  }
  return response.json() as Promise<T>;
}

/**
 * Effectue un appel API authentifié, parse le JSON et gère les erreurs.
 *
 * @param url - URL de l'endpoint
 * @param options - Options fetch (method, body, etc.)
 * @param fallbackError - Message d'erreur par défaut si !response.ok
 * @returns Promise<T> - Données JSON parsées
 */
export async function fetchJsonWithAuth<T>(
  url: string,
  options: RequestInit = {},
  fallbackError: string,
): Promise<T> {
  const response = await fetchWithAuth(url, options);
  if (!response.ok) {
    await handleFetchError(response, fallbackError);
  }
  return response.json() as Promise<T>;
}
