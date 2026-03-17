/**
 * Service de scan de posture sécurité (mode async + polling).
 */

import { getApiBaseUrl } from "../utils/apiClient";
import { pollAsyncJob } from "../utils/pollAsyncJob";
import logger from "../utils/logger";

export interface ScanStep {
  step: string;
  /** Vide depuis le backend ; conservé pour compatibilité et fallback. */
  message: string;
  anomaly_count?: number;
  /** Données structurées pour les steps multi-scan (page_scan_*). */
  url?: string;
  page_index?: number;
  total_pages?: number;
  /** Score global pour multi_scan_done. */
  score?: number;
  /** Nombre d'URLs explorées pour crawl_progress / crawl_done. */
  url_count?: number;
}

/** Étape affichée dans le loader (done dérivé de step.endsWith("_done")). */
export type ScanStepDisplay = ScanStep & { done?: boolean };

export interface ScanFinding {
  id: string;
  category: string;
  title: string;
  severity: string;
  evidence: string;
  recommendation: string;
  references: string[];
}

export interface CategorySummary {
  category: string;
  label_fr: string;
  label_en: string;
  description_fr: string;
  description_en: string;
  checks_fr: string[];
  checks_en: string[];
  anomaly_count: number;
  /** Nombre de tests effectués dans cette catégorie (calculé par le backend). */
  checks_count?: number;
  /** Posture TLS (catégorie tls uniquement) : ok, warning, critical. */
  tls_posture?: "ok" | "warning" | "critical";
  /** Version TLS négociée (catégorie tls uniquement), ex. "TLS 1.2", "TLS 1.3". */
  tls_version?: string;
}

export interface ScanResult {
  url: string;
  timestamp: string;
  duration: number;
  score: number;
  findings: ScanFinding[];
  scan_type?: AsyncScanType;
  scan_mode?: AsyncScanMode;
  category_summaries?: CategorySummary[];
  /** Nombre total de tests effectués (calculé par le backend). */
  total_tests_count?: number;
}

/** Résultat du scan pour une page individuelle (mode multi-URL). */
export interface PageScanResult {
  url: string;
  score: number;
  findings: ScanFinding[];
  category_summaries?: CategorySummary[];
  total_tests_count?: number;
  /** Message d'erreur si la page était inaccessible. */
  error?: string;
}

/** Résultat agrégé d'un scan multi-URL sur un même domaine. */
export interface MultiScanResult {
  result_mode: "multi";
  base_url: string;
  urls: string[];
  score_global: number;
  page_results: PageScanResult[];
  timestamp: string;
  duration: number;
  scan_type: string;
  scan_mode?: AsyncScanMode;
  status: string;
}

export type MultiScanEventHandler =
  | { type: "step"; data: ScanStep }
  | { type: "result"; data: MultiScanResult }
  | { type: "error"; data: ScanError }
  | { type: "save_done"; data: { scan_id: string } }
  | { type: "save_failed"; data: string };

export interface ScanError {
  message: string;
  status_code: number;
  error_type?: string;
  /** Clé i18n pour afficher un message traduit (ex. scanner.crawlStreamError). */
  i18nKey?: string;
}

export type ScanEventType =
  | "step"
  | "result"
  | "error"
  | "save_failed"
  | "save_done";

export type ScanEventHandler =
  | { type: "step"; data: ScanStep }
  | { type: "result"; data: ScanResult }
  | { type: "error"; data: ScanError }
  | { type: "save_failed"; data: string }
  | { type: "save_done"; data: { scan_id: string } };

export type AsyncScanType = "frontend" | "backend";
export type AsyncScanMode = "passive" | "intrusive" | "destructive" | "custom";

interface AsyncScanCreateResponse {
  job_id: string;
  status: string;
  scan_type: string;
  job_token?: string | null;
}

/**
 * Lance un scan et consomme le flux SSE.
 * Appelle onEvent pour chaque événement (step, result, error, save_failed).
 *
 * @param url - URL à scanner
 * @param onEvent - Callback pour chaque événement SSE
 * @param getToken - Optionnel : retourne le token pour sauvegarder dans l'historique (si connecté)
 */
export async function runScan(
  url: string,
  onEvent: (ev: ScanEventHandler) => void,
  getToken?: () => Promise<string | null>,
): Promise<void> {
  return runAsyncScan(
    url,
    onEvent,
    {
      scanType: "frontend",
      scanMode: "passive",
      input: {},
      logPrefix: "[scan-polling]",
    },
    getToken,
  );
}

export async function runAsyncScan(
  url: string,
  onEvent: (ev: ScanEventHandler) => void,
  options: {
    scanType: AsyncScanType;
    scanMode?: AsyncScanMode;
    input?: Record<string, unknown>;
    logPrefix?: string;
  },
  getToken?: () => Promise<string | null>,
): Promise<void> {
  const logPrefix = options.logPrefix ?? "[scan-polling]";
  const base = getApiBaseUrl().replace(/\/$/, "");
  const createEndpoint = `${base}/scan/api/scan/async`;

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (getToken) {
    const token = await getToken();
    if (token) authHeaders.Authorization = `Bearer ${token}`;
  }

  let createData: AsyncScanCreateResponse | null = null;

  await pollAsyncJob<ScanResult>({
    logPrefix,
    createJob: async () => {
      logger.info(`${logPrefix} create job request`, {
        endpoint: createEndpoint,
        url,
      });
      const res = await fetch(createEndpoint, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          url,
          scan_type: options.scanType,
          scan_mode: options.scanMode ?? "passive",
          input: options.input ?? {},
        }),
      });
      if (!res.ok) {
        logger.error(`${logPrefix} create job failed`, { status: res.status });
        onEvent({
          type: "error",
          data: {
            message: `Erreur HTTP ${res.status}`,
            status_code: res.status,
          },
        });
        throw new Error(`create job failed: ${res.status}`);
      }
      const data = (await res.json()) as AsyncScanCreateResponse;
      createData = data;
      logger.info(`${logPrefix} create job success`, {
        job_id: data.job_id,
        scan_type: data.scan_type,
        anonymous: Boolean(data.job_token),
      });
      return { job_id: data.job_id, job_token: data.job_token };
    },
    pollUrl: (jobId) => `${base}/scan/api/scan/async/${jobId}`,
    resultUrl: (jobId) => `${base}/scan/api/scan/async/${jobId}/result`,
    buildPollHeaders: (jobToken) => {
      const h: Record<string, string> = { Accept: "application/json" };
      if (authHeaders.Authorization)
        h.Authorization = authHeaders.Authorization;
      if (jobToken) h["X-Job-Token"] = jobToken;
      return h;
    },
    onEvent: (ev) => {
      if (ev.type === "step") {
        onEvent({ type: "step", data: ev.data });
      } else if (ev.type === "result") {
        onEvent({ type: "result", data: ev.data });
      } else if (ev.type === "error") {
        onEvent({ type: "error", data: ev.data });
      }
    },
    backoff: { initialMs: 500, maxMs: 5000, stepMs: 250 },
  });

  void createData;
}

/**
 * Lance un scan multi-URL (même domaine, utilisateur connecté requis).
 * Crée un job via POST /scan/api/scan/multi-async puis poll le résultat.
 *
 * @param urls       - Liste d'URLs à scanner (même domaine)
 * @param onEvent    - Callback pour chaque événement (step, result, error)
 * @param getToken   - Retourne le token d'authentification (requis)
 */
export async function runMultiScan(
  urls: string[],
  onEvent: (ev: MultiScanEventHandler) => void,
  getToken: () => Promise<string | null>,
  options?: { scanType?: AsyncScanType; scanMode?: AsyncScanMode },
): Promise<void> {
  const logPrefix = "[multi-scan-polling]";
  const base = getApiBaseUrl().replace(/\/$/, "");
  const createEndpoint = `${base}/scan/api/scan/multi-async`;

  const token = await getToken();
  if (!token) {
    onEvent({
      type: "error",
      data: {
        message: "Authentification requise pour le scan multi-URL",
        status_code: 401,
      },
    });
    return;
  }

  const authHeader = `Bearer ${token}`;

  await pollAsyncJob<MultiScanResult>({
    logPrefix,
    createJob: async () => {
      logger.info(`${logPrefix} create job request`, {
        endpoint: createEndpoint,
        urlsCount: urls.length,
      });
      const res = await fetch(createEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          Authorization: authHeader,
        },
        body: JSON.stringify({
          urls,
          scan_type: options?.scanType ?? "frontend",
          scan_mode: options?.scanMode ?? "passive",
        }),
      });
      if (!res.ok) {
        let errorMsg = `Erreur HTTP ${res.status}`;
        try {
          const body = await res.json();
          if (body?.detail) errorMsg = body.detail;
        } catch {}
        onEvent({
          type: "error",
          data: { message: errorMsg, status_code: res.status },
        });
        throw new Error(`create job failed: ${res.status}`);
      }
      const data = (await res.json()) as { job_id: string; status: string };
      logger.info(`${logPrefix} create job success`, { job_id: data.job_id });
      return { job_id: data.job_id };
    },
    pollUrl: (jobId) => `${base}/scan/api/scan/async/${jobId}`,
    resultUrl: (jobId) => `${base}/scan/api/scan/async/${jobId}/result`,
    buildPollHeaders: () => ({
      Accept: "application/json",
      Authorization: authHeader,
    }),
    onEvent: (ev) => {
      if (ev.type === "step") {
        onEvent({ type: "step", data: ev.data });
      } else if (ev.type === "result") {
        const data = ev.data as MultiScanResult;
        const errorCount =
          data.page_results?.filter((p) => p.error).length ?? 0;
        logger.info(`${logPrefix} result received`, {
          pages: data.page_results?.length ?? 0,
          score_global: data.score_global,
          errorCount,
        });
        onEvent({ type: "result", data });
      } else if (ev.type === "error") {
        onEvent({ type: "error", data: ev.data });
      }
    },
    backoff: { initialMs: 500, maxMs: 8000, stepMs: 500 },
  });
}
