/**
 * Service pour l'historique des scans de posture sécurité.
 */

import {
  fetchJsonWithAuth,
  fetchWithAuth,
  getApiBaseUrl,
} from "../utils/apiClient";
import type { PaginatedListResponse } from "../types/api";
import type { ScanResult } from "./scanService";

export interface ScanHistoryItem {
  id: string;
  url: string;
  status: string;
  score: number | null;
  timestamp: string;
  duration: number;
  created_at: string;
}

export type ScanHistoryListResponse = PaginatedListResponse<ScanHistoryItem>;

export interface ScanHistoryDetail extends ScanResult {
  id: string;
  created_at: string;
}

/**
 * Enregistre un scan dans l'historique.
 * Utilisé quand l'utilisateur se connecte après un scan (résultats restaurés depuis sessionStorage).
 *
 * Returns:
 *   string | null: ID du scan créé, ou null si non enregistré (ex. retention "none").
 */
export async function saveScan(result: ScanResult): Promise<string | null> {
  const body: Record<string, unknown> = {
    url: result.url,
    status: "success",
    score: result.score,
    findings: result.findings,
    timestamp: result.timestamp,
    duration: result.duration,
  };
  if (result.category_summaries?.length) {
    body.category_summaries = result.category_summaries;
  }
  const data = await fetchJsonWithAuth<{ id?: string }>(
    `${getApiBaseUrl()}/user/api/scans/history`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    "Erreur lors de la sauvegarde du scan",
  );
  return data?.id && data.id.length > 0 ? data.id : null;
}

export async function getScanHistory(
  page = 1,
  limit = 20,
): Promise<ScanHistoryListResponse> {
  return fetchJsonWithAuth<ScanHistoryListResponse>(
    `${getApiBaseUrl()}/user/api/scans/history?page=${page}&limit=${limit}`,
    { method: "GET" },
    "Erreur lors de la récupération de l'historique",
  );
}

export async function getScanDetail(id: string): Promise<ScanHistoryDetail> {
  return fetchJsonWithAuth<ScanHistoryDetail>(
    `${getApiBaseUrl()}/user/api/scans/history/${id}`,
    { method: "GET" },
    "Scan non trouvé",
  );
}

export async function deleteScan(id: string): Promise<void> {
  await fetchJsonWithAuth(
    `${getApiBaseUrl()}/user/api/scans/history/${id}`,
    { method: "DELETE" },
    "Erreur lors de la suppression",
  );
}

/**
 * Télécharge le rapport PDF d'un scan sauvegardé.
 * Nécessite un scan_id (scan sauvegardé dans l'historique).
 * Langue déduite de la langue du compte (locale).
 */
export async function downloadScanPdf(
  scanId: string,
  lang: "fr" | "en" = "fr",
): Promise<void> {
  const params = new URLSearchParams();
  params.set("scan_id", scanId);
  params.set("lang", lang);

  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/scan/api/scan/export/pdf?${params.toString()}`,
    { method: "GET" },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Erreur lors du téléchargement du PDF");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `scan-${scanId.slice(0, 8)}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Supprime tous les scans de l'historique de l'utilisateur.
 * Utilisé dans la section Données & confidentialité (Mon compte).
 */
export async function deleteAllScans(): Promise<{ deletedCount: number }> {
  const data = await fetchJsonWithAuth<{ deleted_count?: number }>(
    `${getApiBaseUrl()}/user/api/scans/history`,
    { method: "DELETE" },
    "Erreur lors de la suppression de l'historique",
  );
  return { deletedCount: data.deleted_count ?? 0 };
}
