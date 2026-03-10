/**
 * Service pour la gestion des clés API (création, liste, révocation).
 */

import {
  fetchJsonWithAuth,
  fetchWithAuth,
  getApiBaseUrl,
} from "../utils/apiClient";

/** Codes d'erreur pour les messages spécifiques (i18n). */
export type ApiKeyErrorCode =
  | "LIMIT_EXCEEDED"
  | "NAME_EXISTS"
  | "NOT_FOUND"
  | "UNKNOWN";

export class ApiKeyError extends Error {
  constructor(
    public readonly code: ApiKeyErrorCode,
    message: string,
  ) {
    super(message);
    this.name = "ApiKeyError";
  }
}

export interface ApiKeyItem {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
  tags: string[] | null;
  description: string | null;
}

export interface ApiKeyCreateResult {
  id: string;
  key: string;
  name: string;
  created_at: string;
  expires_at: string | null;
}

export interface ApiKeyListResponse {
  items: ApiKeyItem[];
}

export async function listApiKeys(): Promise<ApiKeyListResponse> {
  return fetchJsonWithAuth<ApiKeyListResponse>(
    `${getApiBaseUrl()}/user/api/keys`,
    { method: "GET" },
    "Impossible de charger les clés API",
  );
}

export async function createApiKey(
  name: string,
  options: {
    ttlDays?: number;
    expiresAt?: string;
    tags?: string[] | null;
    description?: string | null;
  },
): Promise<ApiKeyCreateResult> {
  const body: {
    name: string;
    ttl_days?: number;
    expires_at?: string;
    tags?: string[] | null;
    description?: string | null;
  } = {
    name: name.trim(),
  };
  if (options.expiresAt) {
    body.expires_at = options.expiresAt;
  } else {
    body.ttl_days = options.ttlDays ?? 30;
  }
  if (options.tags != null && options.tags.length > 0) body.tags = options.tags;
  if (options.description != null && options.description.trim())
    body.description = options.description.trim();
  const response = await fetchWithAuth(`${getApiBaseUrl()}/user/api/keys`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail = (err as { detail?: string }).detail;
    if (response.status === 403) {
      throw new ApiKeyError(
        "LIMIT_EXCEEDED",
        detail || "Limite de clés atteinte.",
      );
    }
    if (response.status === 409) {
      throw new ApiKeyError(
        "NAME_EXISTS",
        detail || "Une clé avec ce nom existe déjà.",
      );
    }
    throw new ApiKeyError("UNKNOWN", detail || "Impossible de créer la clé.");
  }
  return response.json();
}

export async function updateApiKey(
  id: string,
  options: {
    name?: string;
    ttlDays?: number;
    expiresAt?: string;
    tags?: string[] | null;
    description?: string | null;
  },
): Promise<ApiKeyItem> {
  const body: {
    name?: string;
    ttl_days?: number;
    expires_at?: string;
    tags?: string[] | null;
    description?: string | null;
  } = {};
  if (options.name != null) body.name = options.name.trim();
  if (options.expiresAt) {
    body.expires_at = options.expiresAt;
  } else if (options.ttlDays != null) {
    body.ttl_days = options.ttlDays;
  }
  if (options.tags != null) body.tags = options.tags;
  if (options.description !== undefined)
    body.description = (options.description ?? "").toString().trim() || null;
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/keys/${encodeURIComponent(id)}`,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    if (response.status === 404) {
      throw new ApiKeyError("NOT_FOUND", "Clé non trouvée.");
    }
    if (response.status === 409) {
      throw new ApiKeyError("NAME_EXISTS", "Une clé avec ce nom existe déjà.");
    }
    const err = await response.json().catch(() => ({}));
    const detail = (err as { detail?: string }).detail;
    throw new ApiKeyError(
      "UNKNOWN",
      detail || "Impossible de modifier la clé.",
    );
  }
  return response.json();
}

export async function revokeApiKey(id: string): Promise<void> {
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/keys/${encodeURIComponent(id)}`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    if (response.status === 404) {
      throw new ApiKeyError("NOT_FOUND", "Clé non trouvée.");
    }
    const err = await response.json().catch(() => ({}));
    const detail = (err as { detail?: string }).detail;
    throw new ApiKeyError(
      "UNKNOWN",
      detail || "Impossible de révoquer la clé.",
    );
  }
}
