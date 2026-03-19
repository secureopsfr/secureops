/**
 * Service de crawl HTTP (mode async + polling).
 */

import { getApiBaseUrl } from "../utils/apiClient";
import {
  parse429Error,
  parseHttpError,
  pollAsyncJob,
} from "../utils/pollAsyncJob";
import logger from "../utils/logger";
import type { ScanStep } from "./scanService";

export interface CrawlUrlEntry {
  url: string;
  depth?: number;
  /** Paramètres de chemin ({id}, :id) et leurs valeurs pour résolution avant scan. */
  params?: Record<string, string>;
}

export interface CrawlResponse {
  urls: CrawlUrlEntry[];
  /** True si le crawl a été interrompu par le timeout (résultats partiels). */
  timeout_reached?: boolean;
  /** True si une protection anti-bot a été détectée (mode Playwright). */
  anti_bot_suspected?: boolean;
  /** True si une signature anti-bot a été détectée dans le HTML. */
  anti_bot_signature_detected?: boolean;
  /** True si très peu d'URLs ont été trouvées en mode avancé (suspicion anti-bot). */
  anti_bot_low_url_suspected?: boolean;
  /** True si timeout sur le crawler HTML. */
  timeout_html?: boolean;
  /** True si timeout sur le crawler avancé. */
  timeout_playwright?: boolean;
  /** True si trop de requêtes 403 (protection anti-bot, WAF) ; crawl arrêté, résultats partiels. */
  requests_blocked?: boolean;
  /** True si le crawler HTML a été bloqué par 403 consécutifs. */
  requests_blocked_html?: boolean;
  /** True si le crawler avancé a été bloqué par 403 consécutifs. */
  requests_blocked_playwright?: boolean;
  /** Maximum de réponses 403 consécutives observées pendant le crawl. */
  max_consecutive_403?: number;
  /** Chemins Disallow extraits de robots.txt (non crawlés). */
  disallow_paths?: string[];
}

export type CrawlEventType = "step" | "result" | "error";

export type CrawlEventHandler =
  | { type: "step"; data: ScanStep }
  | { type: "result"; data: CrawlResponse }
  | {
      type: "error";
      data: { message: string; status_code: number; i18nKey?: string };
    };

export type CrawlMode = "html" | "playwright" | "both";

interface AsyncCrawlCreateResponse {
  job_id: string;
  status: string;
  scan_type: string;
  job_token?: string | null;
}

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
  getToken?: () => Promise<string | null>,
): Promise<void> {
  const logPrefix = "[crawl-polling]";
  const base = getApiBaseUrl().replace(/\/$/, "");
  const createEndpoint = `${base}/crawl/api/crawl/async`;

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (getToken) {
    const token = await getToken();
    if (token) authHeaders.Authorization = `Bearer ${token}`;
  }

  await pollAsyncJob<CrawlResponse>({
    logPrefix,
    streamErrorKey: "scanner.crawlStreamError",
    createJob: async () => {
      logger.info(`${logPrefix} create job request`, {
        endpoint: createEndpoint,
        url,
        max_urls: maxUrls,
        mode,
      });
      const res = await fetch(createEndpoint, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          url,
          scan_type: "frontend",
          input: { max_urls: maxUrls, mode },
        }),
      });
      if (!res.ok) {
        const errorData =
          res.status === 429
            ? await parse429Error(res)
            : await parseHttpError(res);
        const logFn = res.status >= 500 ? logger.error : logger.warn;
        logFn(
          `${logPrefix} create job failed: ${res.status} - ${errorData.message}`,
        );
        onEvent({ type: "error", data: errorData });
        throw new Error(errorData.message);
      }
      const data = (await res.json()) as AsyncCrawlCreateResponse;
      logger.info(`${logPrefix} create job success`, {
        job_id: data.job_id,
        anonymous: Boolean(data.job_token),
      });
      return { job_id: data.job_id, job_token: data.job_token };
    },
    pollUrl: (jobId) => `${base}/crawl/api/crawl/async/${jobId}`,
    resultUrl: (jobId) => `${base}/crawl/api/crawl/async/${jobId}/result`,
    buildPollHeaders: (jobToken) => {
      const h: Record<string, string> = { Accept: "application/json" };
      if (jobToken) {
        h["X-Job-Token"] = jobToken;
      } else if (authHeaders.Authorization) {
        h.Authorization = authHeaders.Authorization;
      }
      return h;
    },
    onEvent: (ev) => {
      if (ev.type === "step") {
        onEvent({ type: "step", data: ev.data });
      } else if (ev.type === "result") {
        const data = ev.data as CrawlResponse;
        logger.info(`${logPrefix} result received`, {
          urls_count: data.urls?.length ?? 0,
          timeout_reached: data.timeout_reached ?? false,
        });
        onEvent({ type: "result", data });
      } else if (ev.type === "error") {
        onEvent({
          type: "error",
          data: {
            message: ev.data.message,
            status_code: ev.data.status_code,
            i18nKey: ev.data.i18nKey,
          },
        });
      }
    },
    backoff: { initialMs: 500, maxMs: 5000, stepMs: 250 },
  });
}
