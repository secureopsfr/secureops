/**
 * Service de scan de posture sécurité (mode async + polling).
 */

import { getApiBaseUrl } from "../utils/apiClient";
import logger from "../utils/logger";

export interface ScanStep {
  step: string;
  message: string;
  anomaly_count?: number;
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

type AsyncJobStatus = "pending" | "running" | "completed" | "failed";
export type AsyncScanType = "frontend" | "backend" | "custom";

interface AsyncScanCreateResponse {
  job_id: string;
  status: AsyncJobStatus;
  scan_type: "frontend" | "backend" | "custom";
  job_token?: string | null;
}

interface AsyncScanStatusResponse {
  job_id: string;
  status: AsyncJobStatus;
  progress_log?: Array<{
    step: string;
    message: string;
    at: string;
    anomaly_count?: number;
  }>;
  error?: {
    message?: string;
    status_code?: number;
    error_type?: string;
  };
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
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
    input?: Record<string, unknown>;
    logPrefix?: string;
  },
  getToken?: () => Promise<string | null>,
): Promise<void> {
  const logPrefix = options.logPrefix ?? "[scan-polling]";
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl.replace(/\/$/, "")}/scan/api/scan/async`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (getToken) {
    const token = await getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let createResponse: Response;
  try {
    logger.info(`${logPrefix} create job request`, { endpoint, url });
    createResponse = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({
        url,
        scan_type: options.scanType,
        input: options.input ?? {},
      }),
    });
  } catch (err) {
    onEvent({
      type: "error",
      data: {
        message: err instanceof Error ? err.message : "Erreur réseau",
        status_code: 0,
      },
    });
    return;
  }

  if (!createResponse.ok) {
    logger.error(`${logPrefix} create job failed`, {
      status: createResponse.status,
    });
    onEvent({
      type: "error",
      data: {
        message: `Erreur HTTP ${createResponse.status}`,
        status_code: createResponse.status,
      },
    });
    return;
  }
  let createData: AsyncScanCreateResponse;
  try {
    createData = (await createResponse.json()) as AsyncScanCreateResponse;
    logger.info(`${logPrefix} create job success`, {
      job_id: createData.job_id,
      status: createData.status,
      scan_type: createData.scan_type,
      anonymous: Boolean(createData.job_token),
    });
  } catch {
    onEvent({
      type: "error",
      data: {
        message: "Réponse de création invalide",
        status_code: 500,
      },
    });
    return;
  }
  const jobId = createData.job_id;
  const jobToken = createData.job_token ?? undefined;
  const statusEndpoint = `${baseUrl.replace(/\/$/, "")}/scan/api/scan/async/${jobId}`;
  const resultEndpoint = `${statusEndpoint}/result`;
  let seenProgress = 0;
  let pollIntervalMs = 500;

  try {
    while (true) {
      const pollHeaders: Record<string, string> = {
        Accept: "application/json",
      };
      if (headers.Authorization)
        pollHeaders.Authorization = headers.Authorization;
      if (jobToken) pollHeaders["X-Job-Token"] = jobToken;

      const statusRes = await fetch(statusEndpoint, {
        method: "GET",
        headers: pollHeaders,
      });
      logger.debug(`${logPrefix} status poll`, {
        job_id: jobId,
        http_status: statusRes.status,
        poll_interval_ms: pollIntervalMs,
      });
      if (!statusRes.ok) {
        onEvent({
          type: "error",
          data: {
            message: `Erreur statut HTTP ${statusRes.status}`,
            status_code: statusRes.status,
          },
        });
        return;
      }
      const statusData = (await statusRes.json()) as AsyncScanStatusResponse;
      logger.info(`${logPrefix} status update`, {
        job_id: statusData.job_id,
        status: statusData.status,
        progress_count: statusData.progress_log?.length ?? 0,
        last_step:
          statusData.progress_log && statusData.progress_log.length > 0
            ? statusData.progress_log[statusData.progress_log.length - 1].step
            : undefined,
      });
      const progress = statusData.progress_log ?? [];
      const hasNewProgress = progress.length > seenProgress;
      for (let i = seenProgress; i < progress.length; i += 1) {
        const entry = progress[i];
        onEvent({
          type: "step",
          data: {
            step: entry.step,
            message: entry.message,
            anomaly_count:
              typeof entry.anomaly_count === "number"
                ? entry.anomaly_count
                : undefined,
          },
        });
      }
      seenProgress = progress.length;
      pollIntervalMs = hasNewProgress
        ? 500
        : Math.min(5000, pollIntervalMs + 250);

      if (statusData.status === "failed") {
        logger.error(`${logPrefix} job failed`, {
          job_id: statusData.job_id,
          error: statusData.error,
        });
        onEvent({
          type: "error",
          data: {
            message: statusData.error?.message ?? "Erreur de scan",
            status_code: statusData.error?.status_code ?? 500,
            error_type: statusData.error?.error_type,
          },
        });
        return;
      }
      if (statusData.status === "completed") {
        logger.info(`${logPrefix} fetching result`, {
          job_id: statusData.job_id,
        });
        const resultRes = await fetch(resultEndpoint, {
          method: "GET",
          headers: pollHeaders,
        });
        if (!resultRes.ok) {
          logger.error(`${logPrefix} result fetch failed`, {
            job_id: statusData.job_id,
            status: resultRes.status,
          });
          onEvent({
            type: "error",
            data: {
              message: `Erreur résultat HTTP ${resultRes.status}`,
              status_code: resultRes.status,
            },
          });
          return;
        }
        const resultData = (await resultRes.json()) as ScanResult;
        logger.info(`${logPrefix} result received`, {
          job_id: statusData.job_id,
          findings_count: resultData.findings?.length ?? 0,
          score: resultData.score,
        });
        onEvent({ type: "result", data: resultData });
        return;
      }
      await delay(pollIntervalMs);
    }
  } catch (err) {
    onEvent({
      type: "error",
      data: {
        message:
          err instanceof Error
            ? err.message
            : "Erreur lors de la lecture du flux",
        status_code: 500,
      },
    });
  }
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
): Promise<void> {
  const logPrefix = "[multi-scan-polling]";
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl.replace(/\/$/, "")}/scan/api/scan/multi-async`;

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

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    Authorization: `Bearer ${token}`,
  };

  let createResponse: Response;
  try {
    logger.info(`${logPrefix} create job request`, {
      endpoint,
      urlsCount: urls.length,
    });
    createResponse = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({ urls, scan_type: "frontend" }),
    });
  } catch (err) {
    onEvent({
      type: "error",
      data: {
        message: err instanceof Error ? err.message : "Erreur réseau",
        status_code: 0,
      },
    });
    return;
  }

  if (!createResponse.ok) {
    let errorMsg = `Erreur HTTP ${createResponse.status}`;
    try {
      const body = await createResponse.json();
      if (body?.detail) errorMsg = body.detail;
    } catch {}
    onEvent({
      type: "error",
      data: { message: errorMsg, status_code: createResponse.status },
    });
    return;
  }

  interface MultiCreateResponse {
    job_id: string;
    status: string;
    scan_type: string;
  }

  let createData: MultiCreateResponse;
  try {
    createData = (await createResponse.json()) as MultiCreateResponse;
    logger.info(`${logPrefix} create job success`, {
      job_id: createData.job_id,
    });
  } catch {
    onEvent({
      type: "error",
      data: { message: "Réponse de création invalide", status_code: 500 },
    });
    return;
  }

  const jobId = createData.job_id;
  const statusEndpoint = `${baseUrl.replace(/\/$/, "")}/scan/api/scan/async/${jobId}`;
  const resultEndpoint = `${statusEndpoint}/result`;
  let seenProgress = 0;
  let pollIntervalMs = 500;

  try {
    while (true) {
      const pollHeaders: Record<string, string> = {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
      };

      const statusRes = await fetch(statusEndpoint, {
        method: "GET",
        headers: pollHeaders,
      });
      if (!statusRes.ok) {
        onEvent({
          type: "error",
          data: {
            message: `Erreur statut HTTP ${statusRes.status}`,
            status_code: statusRes.status,
          },
        });
        return;
      }

      interface StatusResponse {
        job_id: string;
        status: string;
        result_mode?: string;
        progress_log?: Array<{
          step: string;
          message: string;
          at: string;
          anomaly_count?: number;
        }>;
        error?: { message?: string; status_code?: number; error_type?: string };
      }

      const statusData = (await statusRes.json()) as StatusResponse;
      const progress = statusData.progress_log ?? [];
      const hasNewProgress = progress.length > seenProgress;
      for (let i = seenProgress; i < progress.length; i++) {
        const entry = progress[i];
        onEvent({
          type: "step",
          data: {
            step: entry.step,
            message: entry.message,
            anomaly_count: entry.anomaly_count,
          },
        });
      }
      seenProgress = progress.length;
      pollIntervalMs = hasNewProgress
        ? 500
        : Math.min(8000, pollIntervalMs + 500);

      if (statusData.status === "failed") {
        onEvent({
          type: "error",
          data: {
            message: statusData.error?.message ?? "Erreur de scan multi-URL",
            status_code: statusData.error?.status_code ?? 500,
            error_type: statusData.error?.error_type,
          },
        });
        return;
      }

      if (statusData.status === "completed") {
        const resultRes = await fetch(resultEndpoint, {
          method: "GET",
          headers: pollHeaders,
        });
        if (!resultRes.ok) {
          onEvent({
            type: "error",
            data: {
              message: `Erreur résultat HTTP ${resultRes.status}`,
              status_code: resultRes.status,
            },
          });
          return;
        }
        const resultData = (await resultRes.json()) as MultiScanResult;
        logger.info(`${logPrefix} result received`, {
          job_id: jobId,
          pages: resultData.page_results?.length ?? 0,
          score_global: resultData.score_global,
        });
        onEvent({ type: "result", data: resultData });
        return;
      }

      await delay(pollIntervalMs);
    }
  } catch (err) {
    onEvent({
      type: "error",
      data: {
        message: err instanceof Error ? err.message : "Erreur lors du polling",
        status_code: 500,
      },
    });
  }
}
