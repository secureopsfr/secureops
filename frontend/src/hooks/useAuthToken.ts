/**
 * Hook pour obtenir le token JWT de l'utilisateur connecté.
 * Retourne une fonction `getToken` à passer aux services de scan/crawl async.
 *
 * Aligné sur `getBearerToken` dans `apiClient.ts` : access token puis id token,
 * puis un second essai avec `forceRefresh` si la session est vide (évite
 * « Authentification requise pour le scan multi-URL » juste après connexion).
 */

import { useCallback } from "react";
import { fetchAuthSession } from "aws-amplify/auth";

function tokenFromSession(
  session: Awaited<ReturnType<typeof fetchAuthSession>>,
) {
  return (
    session.tokens?.accessToken?.toString() ??
    session.tokens?.idToken?.toString() ??
    null
  );
}

/**
 * Retourne une fonction `getToken` qui résout le token JWT de l'utilisateur,
 * ou `undefined` si l'utilisateur n'est pas authentifié.
 */
export function useAuthToken(
  isAuthenticated: boolean,
): (() => Promise<string | null>) | undefined {
  const getToken = useCallback(async (): Promise<string | null> => {
    try {
      let session = await fetchAuthSession();
      let token = tokenFromSession(session);
      if (!token) {
        session = await fetchAuthSession({ forceRefresh: true });
        token = tokenFromSession(session);
      }
      return token;
    } catch {
      return null;
    }
  }, []);

  return isAuthenticated ? getToken : undefined;
}
