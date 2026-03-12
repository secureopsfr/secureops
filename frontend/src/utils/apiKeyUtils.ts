/**
 * Utilitaires pour la gestion des clés API (alignés avec le backend).
 */

import { ApiKeyError, type ApiKeyErrorCode } from "../services/apiKeysService";

/** Max 10 tags (backend). */
export const MAX_TAGS = 10;

/** Max 50 caractères par tag (backend). */
export const MAX_TAG_LENGTH = 50;

export type ApiKeyErrorContext = "create" | "update" | "revoke";

/** Mapping des codes d'erreur vers les clés i18n par contexte. */
const ERROR_KEYS: Record<
  ApiKeyErrorContext,
  Partial<Record<ApiKeyErrorCode, string>>
> = {
  create: {
    LIMIT_EXCEEDED: "scanner.clesApi.errorLimitExceeded",
    NAME_EXISTS: "scanner.clesApi.errorNameExists",
    UNKNOWN: "scanner.clesApi.createError",
  },
  update: {
    NOT_FOUND: "scanner.clesApi.errorKeyNotFound",
    NAME_EXISTS: "scanner.clesApi.errorNameExists",
    UNKNOWN: "scanner.clesApi.updateError",
  },
  revoke: {
    NOT_FOUND: "scanner.clesApi.errorKeyNotFound",
    UNKNOWN: "scanner.clesApi.revokeError",
  },
};

/**
 * Retourne le message d'erreur adapté pour une opération sur clé API.
 */
export function getApiKeyErrorMessage(
  e: unknown,
  t: (key: string) => string,
  context: ApiKeyErrorContext,
): string {
  const fallback = ERROR_KEYS[context].UNKNOWN ?? "scanner.clesApi.createError";
  if (e instanceof ApiKeyError) {
    const key = ERROR_KEYS[context][e.code];
    return t(key ?? fallback);
  }
  if (e instanceof Error) return e.message;
  return t(fallback);
}
