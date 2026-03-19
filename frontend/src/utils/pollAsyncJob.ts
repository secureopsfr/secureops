/**
 * Utilitaire générique pour le pattern "create job → poll status → fetch result".
 *
 * Utilisé par runAsyncScan, runMultiScan et runCrawl pour éviter la
 * duplication de la boucle de polling.
 */

import logger from "./logger";
import type { ScanStep } from "../services/scanService";

export type AsyncJobStatus = "pending" | "running" | "completed" | "failed";

interface JobStatusResponse {
  job_id: string;
  status: AsyncJobStatus | string;
  progress_log?: Array<ScanStep & { at: string }>;
  error?: {
    message?: string;
    status_code?: number;
    error_type?: string;
  };
}

export interface AsyncJobError {
  message: string;
  status_code: number;
  error_type?: string;
  i18nKey?: string;
}

export type AsyncJobEvent<TResult> =
  | { type: "step"; data: ScanStep }
  | { type: "result"; data: TResult }
  | { type: "error"; data: AsyncJobError };

export interface PollAsyncJobConfig<TResult> {
  /** Returns the POST response body (job_id + optional job_token). */
  createJob: () => Promise<{ job_id: string; job_token?: string | null }>;
  /** Full URL for polling status, given the job_id. */
  pollUrl: (jobId: string) => string;
  /** Full URL for fetching the final result, given the job_id. */
  resultUrl: (jobId: string) => string;
  /**
   * Build poll request headers. Called once after createJob resolves so
   * callers can include auth/job-token headers.
   */
  buildPollHeaders: (jobToken: string | undefined) => Record<string, string>;
  onEvent: (event: AsyncJobEvent<TResult>) => void;
  logPrefix?: string;
  backoff?: { initialMs: number; maxMs: number; stepMs: number };
  /** Optional i18nKey to attach to stream/network errors. */
  streamErrorKey?: string;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Parse une réponse HTTP d'erreur (4xx, 5xx) et extrait le message du body JSON.
 * Utilisé pour afficher des messages clairs (ex. domaine interdit, URL invalide).
 */
export async function parseHttpError(res: Response): Promise<AsyncJobError> {
  let body: Record<string, unknown> = {};
  try {
    body = (await res.json()) as Record<string, unknown>;
  } catch {
    return { message: `Erreur HTTP ${res.status}`, status_code: res.status };
  }
  const detail = body["detail"];
  const message =
    typeof detail === "string"
      ? detail
      : Array.isArray(detail) && detail.length > 0
        ? String(detail[0])
        : String(body["detail"] ?? `Erreur HTTP ${res.status}`);
  return { message, status_code: res.status };
}

/**
 * Parse une réponse 429 et retourne le bon i18nKey selon qu'il s'agit
 * d'un quota journalier épuisé ou d'un rate limit court terme.
 */
export async function parse429Error(res: Response): Promise<AsyncJobError> {
  let body: Record<string, unknown> = {};
  try {
    body = (await res.json()) as Record<string, unknown>;
  } catch {
    // body non-JSON : on garde les valeurs par défaut
  }
  const isQuota =
    "remaining" in body && body["remaining"] === 0 && "reset_at" in body;
  return {
    message: String(body["detail"] ?? `Erreur HTTP ${res.status}`),
    status_code: res.status,
    i18nKey: isQuota ? "scanner.quotaExceeded" : "scanner.rateLimitExceeded",
  };
}

export async function pollAsyncJob<TResult>(
  config: PollAsyncJobConfig<TResult>,
): Promise<void> {
  const {
    createJob,
    pollUrl,
    resultUrl,
    buildPollHeaders,
    onEvent,
    logPrefix = "[async-job]",
    backoff = { initialMs: 500, maxMs: 5000, stepMs: 250 },
    streamErrorKey,
  } = config;

  let createData: { job_id: string; job_token?: string | null };
  try {
    createData = await createJob();
    logger.info(`${logPrefix} job created`, { job_id: createData.job_id });
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

  const jobId = createData.job_id;
  const jobToken = createData.job_token ?? undefined;
  const pollHeaders = buildPollHeaders(jobToken);

  let seenProgress = 0;
  let pollIntervalMs = backoff.initialMs;

  try {
    while (true) {
      const statusRes = await fetch(pollUrl(jobId), {
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

      const statusData = (await statusRes.json()) as JobStatusResponse;
      logger.info(`${logPrefix} status update`, {
        job_id: statusData.job_id,
        status: statusData.status,
        progress_count: statusData.progress_log?.length ?? 0,
      });

      const progress = statusData.progress_log ?? [];
      const hasNewProgress = progress.length > seenProgress;
      for (let i = seenProgress; i < progress.length; i += 1) {
        const { at, ...stepData } = progress[i];
        void at;
        onEvent({ type: "step", data: stepData });
      }
      seenProgress = progress.length;
      pollIntervalMs = hasNewProgress
        ? backoff.initialMs
        : Math.min(backoff.maxMs, pollIntervalMs + backoff.stepMs);

      if (statusData.status === "failed") {
        logger.error(`${logPrefix} job failed`, {
          job_id: jobId,
          error: statusData.error,
        });
        onEvent({
          type: "error",
          data: {
            message: statusData.error?.message ?? "Erreur lors du job",
            status_code: statusData.error?.status_code ?? 500,
            error_type: statusData.error?.error_type,
          },
        });
        return;
      }

      if (statusData.status === "completed") {
        logger.info(`${logPrefix} fetching result`, { job_id: jobId });
        const resultRes = await fetch(resultUrl(jobId), {
          method: "GET",
          headers: pollHeaders,
        });
        if (!resultRes.ok) {
          logger.error(`${logPrefix} result fetch failed`, {
            job_id: jobId,
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
        const resultData = (await resultRes.json()) as TResult;
        logger.info(`${logPrefix} result received`, { job_id: jobId });
        onEvent({ type: "result", data: resultData });
        return;
      }

      await delay(pollIntervalMs);
    }
  } catch (err) {
    const rawMessage =
      err instanceof Error ? err.message : "Erreur lors de la lecture du flux";
    const isStreamError =
      /input stream|transfer closed|timeout|aborted|network/i.test(rawMessage);
    onEvent({
      type: "error",
      data: {
        message: rawMessage,
        status_code: 500,
        i18nKey: isStreamError && streamErrorKey ? streamErrorKey : undefined,
      },
    });
  }
}
