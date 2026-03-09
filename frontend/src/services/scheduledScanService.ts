/**
 * Service pour les scans planifiés (monitoring continu).
 */

import { fetchJsonWithAuth, getApiBaseUrl } from "../utils/apiClient";
import type { PaginatedListResponse } from "../types/api";

export type Frequency = "daily" | "weekly" | "monthly";

export type ScanType = "frontend" | "backend" | "custom";

export interface ScheduledScan {
  id: string;
  url: string;
  scan_type: ScanType;
  frequency: string;
  schedule_hour: number;
  schedule_minute: number;
  schedule_day_of_week: number | null;
  schedule_day_of_month: number | null;
  next_run_at: string;
  enabled: boolean;
  scan_alerts_enabled: boolean;
  created_at: string;
}

export interface ScanAlertEvent {
  id: string;
  url: string;
  scan_type: ScanType;
  alert_type: string;
  email_sent: boolean;
  triggered_at: string;
}

export interface CreateScheduledScanInput {
  url: string;
  scan_type: ScanType;
  frequency: Frequency;
  schedule_hour?: number;
  schedule_minute?: number;
  schedule_day_of_week?: number;
  schedule_day_of_month?: number;
  /** Fuseau utilisateur (ex. Europe/Paris). Si absent, détecté automatiquement. */
  timezone?: string;
  /** Recevoir des emails en cas de régression ou finding critique (défaut true). */
  scan_alerts_enabled?: boolean;
}

/** Retourne le fuseau horaire du navigateur (ex. Europe/Paris). */
export function getUserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export interface UpdateScheduledScanInput {
  frequency?: Frequency;
  schedule_hour?: number;
  schedule_minute?: number;
  schedule_day_of_week?: number;
  schedule_day_of_month?: number;
  enabled?: boolean;
  scan_alerts_enabled?: boolean;
}

export async function createScheduledScan(
  input: CreateScheduledScanInput,
): Promise<ScheduledScan> {
  return fetchJsonWithAuth<ScheduledScan>(
    `${getApiBaseUrl()}/user/api/scans/schedule`,
    {
      method: "POST",
      body: JSON.stringify({
        url: input.url,
        scan_type: input.scan_type,
        frequency: input.frequency,
        schedule_hour: input.schedule_hour ?? 2,
        schedule_minute: input.schedule_minute ?? 0,
        schedule_day_of_week: input.schedule_day_of_week ?? null,
        schedule_day_of_month: input.schedule_day_of_month ?? null,
        timezone: input.timezone ?? getUserTimezone(),
        scan_alerts_enabled: input.scan_alerts_enabled ?? true,
      }),
    },
    "Erreur lors de la création du scan planifié",
  );
}

export type ScheduledScanListResponse = PaginatedListResponse<ScheduledScan>;

export async function getScheduledScans(
  page = 1,
  limit = 10,
): Promise<ScheduledScanListResponse> {
  return fetchJsonWithAuth<ScheduledScanListResponse>(
    `${getApiBaseUrl()}/user/api/scans/schedule?page=${page}&limit=${limit}`,
    { method: "GET" },
    "Erreur lors de la récupération des scans planifiés",
  );
}

export async function updateScheduledScan(
  id: string,
  input: UpdateScheduledScanInput,
): Promise<ScheduledScan> {
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

  return fetchJsonWithAuth<ScheduledScan>(
    `${getApiBaseUrl()}/user/api/scans/schedule/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    "Erreur lors de la modification du scan planifié",
  );
}

export async function deleteScheduledScan(id: string): Promise<void> {
  await fetchJsonWithAuth(
    `${getApiBaseUrl()}/user/api/scans/schedule/${id}`,
    { method: "DELETE" },
    "Erreur lors de la suppression du scan planifié",
  );
}

export type ScanAlertHistoryListResponse =
  PaginatedListResponse<ScanAlertEvent>;

export async function getScanAlertHistory(
  page = 1,
  limit = 10,
): Promise<ScanAlertHistoryListResponse> {
  return fetchJsonWithAuth<ScanAlertHistoryListResponse>(
    `${getApiBaseUrl()}/user/api/scans/schedule/alerts/history?page=${page}&limit=${limit}`,
    { method: "GET" },
    "Erreur lors de la récupération de l'historique des alertes",
  );
}

export async function deleteScanAlertEvent(eventId: string): Promise<void> {
  await fetchJsonWithAuth(
    `${getApiBaseUrl()}/user/api/scans/schedule/alerts/history/${eventId}`,
    { method: "DELETE" },
    "Erreur lors de la suppression de l'événement d'alerte",
  );
}
