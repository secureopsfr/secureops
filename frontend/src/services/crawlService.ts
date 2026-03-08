/**
 * Service de crawl HTTP.
 * Découvre les URLs d'un site pour validation avant scan.
 */

import { getApiBaseUrl } from "../utils/apiClient";

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

function parseSSEBlock(block: string): { event: string; data: unknown } | null {
  let event = "message";
  let data: unknown = null;
  for (const line of block.split("\n")) {
    if (line.startsWith("event: ")) {
      event = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      try {
        data = JSON.parse(line.slice(6));
      } catch {
        data = line.slice(6);
      }
    }
  }
  if (data === null) return null;
  return { event, data };
}

export type CrawlMode = "html" | "playwright" | "both";

/**
 * Lance un crawl en streaming SSE.
 * Émet des étapes (validation, SSRF, robots, crawl) puis result ou error.
 *
 * @param url - URL de départ à crawler
 * @param onEvent - Callback pour chaque événement (step, result, error)
 * @param maxUrls - Limite d'URLs (5–200, défaut 50)
 * @param mode - Mode de crawl : html, playwright ou both (fusion des deux)
 */
export async function runCrawlStream(
  url: string,
  onEvent: (ev: CrawlEventHandler) => void,
  maxUrls: number = 50,
  mode: CrawlMode = "html",
): Promise<void> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl.replace(/\/$/, "")}/crawl/api/crawl/stream`;

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ url, max_urls: maxUrls, mode }),
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

  if (!response.ok) {
    onEvent({
      type: "error",
      data: {
        message: `Erreur HTTP ${response.status}`,
        status_code: response.status,
      },
    });
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onEvent({
      type: "error",
      data: { message: "Flux de réponse indisponible", status_code: 500 },
    });
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";
      for (const block of blocks) {
        if (!block.trim()) continue;
        const parsed = parseSSEBlock(block);
        if (!parsed) continue;
        const { event, data } = parsed;
        if (
          event === "step" &&
          data &&
          typeof data === "object" &&
          "step" in data &&
          "message" in data
        ) {
          onEvent({
            type: "step",
            data: data as { step: string; message: string },
          });
        } else if (event === "result" && data && typeof data === "object") {
          onEvent({ type: "result", data: data as CrawlResponse });
        } else if (event === "error" && data && typeof data === "object") {
          onEvent({
            type: "error",
            data: {
              message:
                (data as { message?: string }).message ??
                "Erreur lors du crawl",
              status_code:
                (data as { status_code?: number }).status_code ?? 500,
            },
          });
          return;
        }
      }
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
  } finally {
    reader.releaseLock();
  }
}
