/**
 * Service pour l'historique des scans de posture sécurité.
 */

import { fetchWithAuth, getApiBaseUrl } from "../utils/apiClient";
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

export interface ScanHistoryListResponse {
  items: ScanHistoryItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ScanHistoryDetail extends ScanResult {
  id: string;
  created_at: string;
}

/**
 * Enregistre un scan dans l'historique.
 * Utilisé quand l'utilisateur se connecte après un scan (résultats restaurés depuis sessionStorage).
 */
export async function saveScan(result: ScanResult): Promise<void> {
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/history`,
    {
      method: "POST",
      body: JSON.stringify({
        url: result.url,
        status: "success",
        score: result.score,
        findings: result.findings,
        timestamp: result.timestamp,
        duration: result.duration,
      }),
    },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(
      (err.detail as string) || "Erreur lors de la sauvegarde du scan",
    );
  }
}

export async function getScanHistory(
  page = 1,
  limit = 20,
): Promise<ScanHistoryListResponse> {
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/history?page=${page}&limit=${limit}`,
    { method: "GET" },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(
      (err.detail as string) ||
        "Erreur lors de la récupération de l'historique",
    );
  }
  return response.json();
}

export async function getScanDetail(id: string): Promise<ScanHistoryDetail> {
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/history/${id}`,
    { method: "GET" },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err.detail as string) || "Scan non trouvé");
  }
  return response.json();
}

export async function deleteScan(id: string): Promise<void> {
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/history/${id}`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err.detail as string) || "Erreur lors de la suppression");
  }
}

/**
 * Supprime tous les scans de l'historique de l'utilisateur.
 * Utilisé dans la section Données & confidentialité (Mon compte).
 */
export async function deleteAllScans(): Promise<{ deletedCount: number }> {
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/history`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(
      (err.detail as string) || "Erreur lors de la suppression de l'historique",
    );
  }
  const data = await response.json();
  return { deletedCount: (data.deleted_count as number) ?? 0 };
}
