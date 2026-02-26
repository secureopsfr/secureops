/**
 * Service de scan de posture sécurité.
 * Appelle l'API SSE et parse les événements (step, result, error).
 */

import { getApiBaseUrl } from "../utils/apiClient";

export interface ScanStep {
  step: string;
  message: string;
}

export interface ScanFinding {
  id: string;
  category: string;
  title: string;
  severity: string;
  evidence: string;
  recommendation: string;
  references: string[];
}

export interface ScanResult {
  url: string;
  timestamp: string;
  duration: number;
  score: number;
  findings: ScanFinding[];
}

export interface ScanError {
  message: string;
  status_code: number;
  error_type?: string;
}

export type ScanEventType = "step" | "result" | "error";

export type ScanEventHandler =
  | { type: "step"; data: ScanStep }
  | { type: "result"; data: ScanResult }
  | { type: "error"; data: ScanError };

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

/**
 * Lance un scan et consomme le flux SSE.
 * Appelle onEvent pour chaque événement (step, result, error).
 */
export async function runScan(
  url: string,
  onEvent: (ev: ScanEventHandler) => void,
): Promise<void> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl.replace(/\/$/, "")}/scan/api/scan`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ url }),
  });

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
      data: {
        message: "Flux de réponse indisponible",
        status_code: 500,
      },
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
          "step" in data
        ) {
          onEvent({ type: "step", data: data as ScanStep });
        } else if (event === "result" && data && typeof data === "object") {
          onEvent({ type: "result", data: data as ScanResult });
          return;
        } else if (event === "error" && data && typeof data === "object") {
          onEvent({ type: "error", data: data as ScanError });
          return;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
