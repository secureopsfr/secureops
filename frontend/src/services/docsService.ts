/**
 * Service pour la lecture des pages de documentation.
 * Les endpoints GET /admin/api/docs sont publics (pas d'authentification).
 */

import { fetchJson } from "../utils/apiClient";
import { getApiBaseUrl } from "../utils/apiClient";

export interface DocPageRecord {
  slug: string;
  title: string;
  size: number;
  updated_at: string;
}

export interface DocPagesResponse {
  docs: DocPageRecord[];
  total: number;
}

export interface DocPageContent {
  slug: string;
  title: string;
  content: string;
  size: number;
  updated_at: string;
}

export async function getDocsList(
  lang: string = "fr",
): Promise<DocPagesResponse> {
  const params = new URLSearchParams({ lang: lang.slice(0, 2) });
  return fetchJson(
    `${getApiBaseUrl()}/admin/api/docs?${params}`,
    {},
    "Impossible de charger la documentation",
  );
}

export async function getDocBySlug(
  slug: string,
  lang: string = "fr",
): Promise<DocPageContent> {
  const params = new URLSearchParams({ lang: lang.slice(0, 2) });
  return fetchJson(
    `${getApiBaseUrl()}/admin/api/docs/${encodeURIComponent(slug)}?${params}`,
    {},
    "Page de documentation introuvable",
  );
}
