/**
 * Service pour la lecture des pages de documentation (utilisateurs connectés).
 * Les endpoints GET /admin/api/docs sont accessibles avec auth simple (pas admin).
 */

import { fetchWithAuth } from "../utils/apiClient";
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
  const res = await fetchWithAuth(`${getApiBaseUrl()}/admin/api/docs`);
  if (!res.ok) {
    throw new Error("Impossible de charger la documentation");
  }
  return res.json();
}

export async function getDocBySlug(slug: string): Promise<DocPageContent> {
  const res = await fetchWithAuth(
    `${getApiBaseUrl()}/admin/api/docs/${encodeURIComponent(slug)}`,
  );
  if (!res.ok) {
    throw new Error("Page de documentation introuvable");
  }
  return res.json();
}
