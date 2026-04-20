/**
 * Service pour l'historique des scans de posture sécurité.
 */

import {
  fetchJsonWithAuth,
  fetchWithAuth,
  getApiBaseUrl,
} from "../utils/apiClient";
import { buildPaginatedQuery } from "../utils/apiQueryParams";
import type { PaginatedListResponse } from "../types/api";
import type { MultiScanResult, ScanResult } from "./scanService";

export type ScanType = "frontend" | "backend";

export interface ScanHistoryItem {
  id: string;
  url: string;
  scan_type: ScanType;
  scan_mode?: "passive" | "intrusive" | "destructive" | "custom";
  result_mode: "single" | "multi";
  status: string;
  score: number | null;
  timestamp: string;
  duration: number;
  created_at: string;
}

export type ScanHistoryListResponse = PaginatedListResponse<ScanHistoryItem>;

export interface ScanHistoryDetail extends ScanResult {
  id: string;
  scan_type: ScanType;
  scan_mode?: "passive" | "intrusive" | "destructive" | "custom";
  status: string;
  created_at: string;
  result_mode?: "single" | "multi";
  page_results?: MultiScanResult["page_results"];
  urls?: string[];
}

export type ScanHistorySelection =
  | { result_mode: "single"; scan_id: string; result: ScanResult }
  | { result_mode: "multi"; scan_id: string; result: MultiScanResult };

/**
 * Enregistre un scan dans l'historique.
 * Utilisé quand l'utilisateur se connecte après un scan (résultats restaurés depuis sessionStorage).
 *
 * Returns:
 *   string | null: ID du scan créé, ou null si non enregistré (ex. retention "none").
 */
export async function saveScan(
  result: ScanResult,
  scanType: ScanType = "frontend",
): Promise<string | null> {
  const body: Record<string, unknown> = {
    url: result.url,
    scan_type: scanType,
    scan_mode: result.scan_mode ?? "passive",
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

/** Enregistre un scan multi-URL dans l'historique utilisateur. */
export async function saveMultiScan(
  result: MultiScanResult,
): Promise<string | null> {
  const body: Record<string, unknown> = {
    url: result.base_url,
    scan_type: result.scan_type || "frontend",
    scan_mode: result.scan_mode || "passive",
    result_mode: "multi",
    status: result.status || "success",
    score: result.score_global,
    findings: [],
    timestamp: result.timestamp,
    duration: result.duration,
    page_results: result.page_results,
    urls: result.urls,
  };
  const data = await fetchJsonWithAuth<{ id?: string }>(
    `${getApiBaseUrl()}/user/api/scans/history`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    "Erreur lors de la sauvegarde du scan multi-URL",
  );
  return data?.id && data.id.length > 0 ? data.id : null;
}

export interface ScanOverviewResponse {
  kpis: {
    scans_in_period: number;
    total_scans: number;
    avg_score: number | null;
    critical_findings_count: number;
    active_scheduled_count: number;
    last_scan_at: string | null;
  };
  chart_data: Array<{
    ts: string;
    scans: number;
    score: number;
    anomalies: number;
  }>;
}

/**
 * Récupère les KPIs et les données du graphique pour la vue d'ensemble scanner.
 * Respecte les mêmes filtres que l'historique (url, scan_type, date_from, date_to).
 */
export async function getScanOverview(
  url?: string | null,
  scan_type?: string | null,
  date_from?: string | null,
  date_to?: string | null,
  scan_mode?: string | null,
): Promise<ScanOverviewResponse> {
  const params = new URLSearchParams();
  if (url?.trim()) params.set("url", url.trim());
  if (scan_type && ["frontend", "backend", "custom"].includes(scan_type)) {
    params.set("scan_type", scan_type);
  }
  if (
    scan_mode &&
    ["passive", "intrusive", "destructive", "custom"].includes(scan_mode)
  ) {
    params.set("scan_mode", scan_mode);
  }
  if (date_from?.trim()) params.set("date_from", date_from.trim());
  if (date_to?.trim()) params.set("date_to", date_to.trim());
  const query = params.toString();
  return fetchJsonWithAuth<ScanOverviewResponse>(
    `${getApiBaseUrl()}/user/api/scans/history/overview${query ? `?${query}` : ""}`,
    { method: "GET" },
    "Erreur lors de la récupération des statistiques",
  );
}

export async function getScanHistory(
  page = 1,
  limit = 20,
  url?: string | null,
  scan_type?: string | null,
  date_from?: string | null,
  date_to?: string | null,
  scan_mode?: string | null,
): Promise<ScanHistoryListResponse> {
  const query = buildPaginatedQuery({
    page,
    limit,
    url,
    scan_type,
    scan_mode,
    date_from,
    date_to,
  });
  return fetchJsonWithAuth<ScanHistoryListResponse>(
    `${getApiBaseUrl()}/user/api/scans/history?${query}`,
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
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/history/${id}`,
    { method: "DELETE" },
  );
  // Idempotence UX: if scan is already gone, treat as success.
  if (response.status === 404 || response.status === 204) {
    return;
  }
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail =
      (err as { detail?: string | string[] }).detail ??
      "Erreur lors de la suppression";
    throw new Error(Array.isArray(detail) ? detail.join(", ") : detail);
  }
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
