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

export async function getDocsList(): Promise<DocPagesResponse> {
  return fetchJson(
    `${getApiBaseUrl()}/admin/api/docs`,
    {},
    "Impossible de charger la documentation",
  );
}

export async function getDocBySlug(slug: string): Promise<DocPageContent> {
  return fetchJson(
    `${getApiBaseUrl()}/admin/api/docs/${encodeURIComponent(slug)}`,
    {},
    "Page de documentation introuvable",
  );
}
