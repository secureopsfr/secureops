/**
 * Service admin pour la gestion des pages de documentation.
 */

import { fetchJsonWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";

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

export async function getDocs(): Promise<DocPagesResponse> {
  try {
    return await fetchJsonWithAuth<DocPagesResponse>(
      `${getApiBaseUrl()}/admin/api/docs`,
      { method: "GET" },
      "Erreur lors de la récupération des pages doc",
    );
  } catch (err: unknown) {
    logError("[AdminDocsService] Erreur récupération docs:", err);
    showErrorToast(getToastT()("admin.toast.loadDocs"));
    throw err;
  }
}

export async function getDocContent(slug: string): Promise<DocPageContent> {
  try {
    return await fetchJsonWithAuth<DocPageContent>(
      `${getApiBaseUrl()}/admin/api/docs/${encodeURIComponent(slug)}`,
      { method: "GET" },
      "Erreur lors de la récupération de la page doc",
    );
  } catch (err: unknown) {
    logError("[AdminDocsService] Erreur récupération doc:", err);
    showErrorToast(getToastT()("admin.toast.loadDoc"));
    throw err;
  }
}

export async function updateDoc(
  slug: string,
  content: string,
): Promise<Record<string, unknown>> {
  try {
    const title = extractTitleFromHtml(content);
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/docs/${encodeURIComponent(slug)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content }),
      },
      "Erreur lors de la mise à jour de la page doc",
    );
  } catch (err: unknown) {
    logError("[AdminDocsService] Erreur mise à jour doc:", err);
    showErrorToast(getToastT()("admin.toast.updateDoc"));
    throw err;
  }
}

export async function createDoc(
  slug: string,
  title: string,
  content: string = "",
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/docs`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug, title, content }),
      },
      "Erreur lors de la création de la page doc",
    );
  } catch (err: unknown) {
    logError("[AdminDocsService] Erreur création doc:", err);
    showErrorToast(getToastT()("admin.gallery.createDoc"));
    throw err;
  }
}

export async function deleteDoc(
  slug: string,
): Promise<Record<string, unknown>> {
  try {
    return await fetchJsonWithAuth<Record<string, unknown>>(
      `${getApiBaseUrl()}/admin/api/docs/${encodeURIComponent(slug)}`,
      { method: "DELETE" },
      "Erreur lors de la suppression de la page doc",
    );
  } catch (err: unknown) {
    logError("[AdminDocsService] Erreur suppression doc:", err);
    showErrorToast(getToastT()("admin.toast.deleteDoc"));
    throw err;
  }
}

/** Extrait le premier h1 du HTML pour le titre. */
function extractTitleFromHtml(html: string): string {
  const m = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  if (m) {
    const raw = m[1].replace(/<[^>]+>/g, "").trim();
    return raw.slice(0, 200) || "Sans titre";
  }
  return "Sans titre";
}
