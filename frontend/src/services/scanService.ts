/**
 * Service de scan de posture sécurité.
 * Appelle l'API SSE et parse les événements (step, result, error).
 */

import { getApiBaseUrl } from "../utils/apiClient";

export interface ScanStep {
  step: string;
  message: string;
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

export type ScanEventType = "step" | "result" | "error" | "save_failed";

export type ScanEventHandler =
  | { type: "step"; data: ScanStep }
  | { type: "result"; data: ScanResult }
  | { type: "error"; data: ScanError }
  | { type: "save_failed"; data: string };

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
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl.replace(/\/$/, "")}/scan/api/scan`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (getToken) {
    const token = await getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({ url }),
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
          // Ne pas return : le flux peut encore émettre save_failed
        } else if (event === "error" && data && typeof data === "object") {
          onEvent({ type: "error", data: data as ScanError });
          return;
        } else if (
          event === "save_failed" &&
          data &&
          typeof data === "object"
        ) {
          onEvent({
            type: "save_failed",
            data:
              (data as { message?: string }).message ?? "Erreur de sauvegarde",
          });
        }
      }
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
  } finally {
    reader.releaseLock();
  }
}
