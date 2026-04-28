/**
 * Service pour les scans planifiés (monitoring continu).
 */

import {
  fetchJsonWithAuth,
  fetchWithAuth,
  getApiBaseUrl,
} from "../utils/apiClient";
import userService from "./userService";
import { buildPaginatedQuery } from "../utils/apiQueryParams";
import type { PaginatedListResponse } from "../types/api";

export type Frequency = "daily" | "weekly" | "monthly";

export type ScanType = "frontend" | "backend";
export type ScanMode = "passive" | "intrusive" | "destructive" | "custom";
export type ResultMode = "single" | "multi";

export interface ScheduledScan {
  id: string;
  url: string;
  scan_type: ScanType;
  scan_mode: ScanMode;
  result_mode?: ResultMode;
  urls?: string[] | null;
  frequency: string;
  schedule_hour: number;
  schedule_minute: number;
  schedule_day_of_week: number | null;
  schedule_day_of_month: number | null;
  next_run_at: string;
  enabled: boolean;
  scan_alerts_enabled: boolean;
  alert_on_regression: boolean;
  alert_on_critical_finding: boolean;
  alert_score_threshold: number | null;
  created_at: string;
}

export interface ScanAlertEvent {
  id: string;
  url: string;
  scan_type: ScanType;
  scan_mode: ScanMode;
  alert_type: string;
  email_sent: boolean;
  triggered_at: string;
}

export interface CreateScheduledScanInput {
  url: string;
  scan_type: ScanType;
  scan_mode?: ScanMode;
  result_mode?: ResultMode;
  urls?: string[];
  frequency: Frequency;
  schedule_hour?: number;
  schedule_minute?: number;
  schedule_day_of_week?: number;
  schedule_day_of_month?: number;
  /** Fuseau utilisateur (ex. Europe/Paris). Si absent, détecté automatiquement. */
  timezone?: string;
  /** Recevoir des emails en cas de régression ou finding critique (défaut true). */
  scan_alerts_enabled?: boolean;
  /** Déclencher une alerte en cas de régression du score (défaut true). */
  alert_on_regression?: boolean;
  /** Déclencher une alerte en cas de finding critique (défaut true). */
  alert_on_critical_finding?: boolean;
  /** Seuil de chute de score en points déclenchant l'alerte (1-100). null = défaut serveur (10 pts). */
  alert_score_threshold?: number | null;
}

/** Retourne le fuseau horaire du navigateur (ex. Europe/Paris). */
export function getUserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

async function ensureUserInitialized(): Promise<void> {
  await userService.initUser();
}

export interface UpdateScheduledScanInput {
  frequency?: Frequency;
  schedule_hour?: number;
  schedule_minute?: number;
  schedule_day_of_week?: number;
  schedule_day_of_month?: number;
  enabled?: boolean;
  scan_alerts_enabled?: boolean;
  alert_on_regression?: boolean;
  alert_on_critical_finding?: boolean;
  alert_score_threshold?: number | null;
}

export async function createScheduledScan(
  input: CreateScheduledScanInput,
): Promise<ScheduledScan> {
  await ensureUserInitialized();
  return fetchJsonWithAuth<ScheduledScan>(
    `${getApiBaseUrl()}/user/api/scans/schedule`,
    {
      method: "POST",
      body: JSON.stringify({
        url: input.url,
        scan_type: input.scan_type,
        scan_mode: input.scan_mode ?? "passive",
        result_mode: input.result_mode ?? "single",
        urls: input.urls ?? null,
        frequency: input.frequency,
        schedule_hour: input.schedule_hour ?? 2,
        schedule_minute: input.schedule_minute ?? 0,
        schedule_day_of_week: input.schedule_day_of_week ?? null,
        schedule_day_of_month: input.schedule_day_of_month ?? null,
        timezone: input.timezone ?? getUserTimezone(),
        scan_alerts_enabled: input.scan_alerts_enabled ?? true,
        alert_on_regression: input.alert_on_regression ?? true,
        alert_on_critical_finding: input.alert_on_critical_finding ?? true,
        alert_score_threshold: input.alert_score_threshold ?? null,
      }),
    },
    "Erreur lors de la création du scan planifié",
  );
}

export type ScheduledScanListResponse = PaginatedListResponse<ScheduledScan>;

export async function getScheduledScans(
  page = 1,
  limit = 10,
  url?: string | null,
  scan_type?: string | null,
  scan_mode?: string | null,
): Promise<ScheduledScanListResponse> {
  await ensureUserInitialized();
  const query = buildPaginatedQuery({ page, limit, url, scan_type, scan_mode });
  return fetchJsonWithAuth<ScheduledScanListResponse>(
    `${getApiBaseUrl()}/user/api/scans/schedule?${query}`,
    { method: "GET" },
    "Erreur lors de la récupération des scans planifiés",
  );
}

export async function updateScheduledScan(
  id: string,
  input: UpdateScheduledScanInput,
): Promise<ScheduledScan> {
  await ensureUserInitialized();
  const body: Record<string, unknown> = {};
  if (input.frequency !== undefined) body.frequency = input.frequency;
  if (input.schedule_hour !== undefined)
    body.schedule_hour = input.schedule_hour;
  if (input.schedule_minute !== undefined)
    body.schedule_minute = input.schedule_minute;
  if (input.schedule_day_of_week !== undefined)
    body.schedule_day_of_week = input.schedule_day_of_week;
  if (input.schedule_day_of_month !== undefined)
    body.schedule_day_of_month = input.schedule_day_of_month;
  if (input.enabled !== undefined) body.enabled = input.enabled;
  if (input.scan_alerts_enabled !== undefined)
    body.scan_alerts_enabled = input.scan_alerts_enabled;
  if (input.alert_on_regression !== undefined)
    body.alert_on_regression = input.alert_on_regression;
  if (input.alert_on_critical_finding !== undefined)
    body.alert_on_critical_finding = input.alert_on_critical_finding;
  if (input.alert_score_threshold !== undefined)
    body.alert_score_threshold = input.alert_score_threshold;

  return fetchJsonWithAuth<ScheduledScan>(
    `${getApiBaseUrl()}/user/api/scans/schedule/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    "Erreur lors de la modification du scan planifié",
  );
}

export async function deleteScheduledScan(id: string): Promise<void> {
  await ensureUserInitialized();
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/schedule/${id}`,
    { method: "DELETE" },
  );
  if (response.status === 404 || response.status === 204) {
    return;
  }
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail =
      (err as { detail?: string | string[] }).detail ??
      "Erreur lors de la suppression du scan planifié";
    throw new Error(Array.isArray(detail) ? detail.join(", ") : detail);
  }
}

export type ScanAlertHistoryListResponse =
  PaginatedListResponse<ScanAlertEvent>;

export async function getScanAlertHistory(
  page = 1,
  limit = 10,
  url?: string | null,
  scan_type?: string | null,
  scan_mode?: string | null,
  date_from?: string | null,
  date_to?: string | null,
): Promise<ScanAlertHistoryListResponse> {
  await ensureUserInitialized();
  const query = buildPaginatedQuery({
    page,
    limit,
    url,
    scan_type,
    scan_mode,
    date_from,
    date_to,
  });
  return fetchJsonWithAuth<ScanAlertHistoryListResponse>(
    `${getApiBaseUrl()}/user/api/scans/schedule/alerts/history?${query}`,
    { method: "GET" },
    "Erreur lors de la récupération de l'historique des alertes",
  );
}

export async function deleteScanAlertEvent(eventId: string): Promise<void> {
  await ensureUserInitialized();
  const response = await fetchWithAuth(
    `${getApiBaseUrl()}/user/api/scans/schedule/alerts/history/${eventId}`,
    { method: "DELETE" },
  );
  if (response.status === 404 || response.status === 204) {
    return;
  }
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail =
      (err as { detail?: string | string[] }).detail ??
      "Erreur lors de la suppression de l'événement d'alerte";
    throw new Error(Array.isArray(detail) ? detail.join(", ") : detail);
  }
}
