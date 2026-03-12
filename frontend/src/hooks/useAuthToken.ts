/**
 * Hook pour obtenir le token d'accès de l'utilisateur connecté.
 * Retourne une fonction `getToken` à passer aux services de scan/crawl.
 */

import { useCallback } from "react";
import { fetchAuthSession } from "aws-amplify/auth";

/**
 * Retourne une fonction `getToken` qui résout le token JWT de l'utilisateur,
 * ou `undefined` si l'utilisateur n'est pas authentifié.
 */
export function useAuthToken(
  isAuthenticated: boolean,
): (() => Promise<string | null>) | undefined {
  const getToken = useCallback(async (): Promise<string | null> => {
    try {
      const session = await fetchAuthSession();
      return session.tokens?.accessToken?.toString() ?? null;
    } catch {
      return null;
    }
  }, []);

  return isAuthenticated ? getToken : undefined;
}
