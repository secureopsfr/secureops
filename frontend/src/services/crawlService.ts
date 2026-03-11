/**
 * Service de crawl HTTP (mode async + polling).
 */

import { getApiBaseUrl } from "../utils/apiClient";
import logger from "../utils/logger";

export interface CrawlUrlEntry {
  url: string;
  type: string;
  depth: number;
}

export interface CrawlResponse {
  urls: CrawlUrlEntry[];
  /** True si le crawl a été interrompu par le timeout (résultats partiels). */
  timeout_reached?: boolean;
  /** True si une protection anti-bot a été détectée (mode Playwright). */
  anti_bot_suspected?: boolean;
  /** True si trop de requêtes 403 (protection anti-bot, WAF) ; crawl arrêté, résultats partiels. */
  requests_blocked?: boolean;
  /** Chemins Disallow extraits de robots.txt (non crawlés). */
  disallow_paths?: string[];
}

export type CrawlEventType = "step" | "result" | "error";

export type CrawlEventHandler =
  | { type: "step"; data: { step: string; message: string } }
  | { type: "result"; data: CrawlResponse }
  | {
      type: "error";
      data: { message: string; status_code: number; i18nKey?: string };
    };

type AsyncJobStatus = "pending" | "running" | "completed" | "failed";

interface AsyncCrawlCreateResponse {
  job_id: string;
  status: AsyncJobStatus;
  scan_type: "frontend" | "backend" | "custom";
  job_token?: string | null;
}

interface AsyncCrawlStatusResponse {
  job_id: string;
  status: AsyncJobStatus;
  progress_log?: Array<{ step: string; message: string; at: string }>;
  error?: {
    message?: string;
    status_code?: number;
    error_type?: string;
  };
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export type CrawlMode = "html" | "playwright" | "both";

/**
 * Lance un crawl asynchrone (queue) et récupère progression + résultat par polling.
 *
 * @param url - URL de départ à crawler
 * @param onEvent - Callback pour chaque événement (step, result, error)
 * @param maxUrls - Limite d'URLs (5–200, défaut 50)
 * @param mode - Mode de crawl : html, playwright ou both (fusion des deux)
 */
export async function runCrawl(
  url: string,
  onEvent: (ev: CrawlEventHandler) => void,
  maxUrls: number = 50,
  mode: CrawlMode = "html",
): Promise<void> {
  const logPrefix = "[crawl-polling]";
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl.replace(/\/$/, "")}/crawl/api/crawl/async`;

  let createResponse: Response;
  try {
    logger.info(`${logPrefix} create job request`, {
      endpoint,
      url,
      max_urls: maxUrls,
      mode,
    });
    createResponse = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        url,
        scan_type: "frontend",
        input: { max_urls: maxUrls, mode },
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
  let createData: AsyncCrawlCreateResponse;
  try {
    createData = (await createResponse.json()) as AsyncCrawlCreateResponse;
    logger.info(`${logPrefix} create job success`, {
      job_id: createData.job_id,
      status: createData.status,
      scan_type: createData.scan_type,
      anonymous: Boolean(createData.job_token),
    });
  } catch {
    onEvent({
      type: "error",
      data: { message: "Réponse de création invalide", status_code: 500 },
    });
    return;
  }
  const jobId = createData.job_id;
  const jobToken = createData.job_token ?? undefined;
  const statusEndpoint = `${baseUrl.replace(/\/$/, "")}/crawl/api/crawl/async/${jobId}`;
  const resultEndpoint = `${statusEndpoint}/result`;
  let seenProgress = 0;
  let pollIntervalMs = 500;

  try {
    while (true) {
      const pollHeaders: Record<string, string> = {
        Accept: "application/json",
      };
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
      const statusData = (await statusRes.json()) as AsyncCrawlStatusResponse;
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
          data: { step: entry.step, message: entry.message },
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
            message: statusData.error?.message ?? "Erreur lors du crawl",
            status_code: statusData.error?.status_code ?? 500,
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
        const resultData = (await resultRes.json()) as CrawlResponse;
        logger.info(`${logPrefix} result received`, {
          job_id: statusData.job_id,
          urls_count: resultData.urls?.length ?? 0,
          timeout_reached: resultData.timeout_reached ?? false,
        });
        onEvent({ type: "result", data: resultData });
        return;
      }
      await delay(pollIntervalMs);
    }
  } catch (err) {
    const rawMessage =
      err instanceof Error ? err.message : "Erreur lors de la lecture du flux";
    // Message plus explicite pour timeout/connexion coupée (ex. "Error in input stream")
    const isStreamError =
      /input stream|transfer closed|timeout|aborted|network/i.test(rawMessage);
    onEvent({
      type: "error",
      data: {
        message: rawMessage,
        status_code: 500,
        i18nKey: isStreamError ? "scanner.crawlStreamError" : undefined,
      },
    });
  }
}
