/**
 * Service de tracking analytics côté client.
 *
 * Collecte les événements utilisateur (page_view, page_exit, session_start, etc.)
 * et les envoie par batch au backend via navigator.sendBeacon() pour survivre
 * aux fermetures d'onglet.
 *
 * Fonctionnement :
 * 1. Les événements sont accumulés dans un buffer en mémoire
 * 2. Le buffer est flush périodiquement (toutes les 10s) ou quand il atteint 20 événements
 * 3. navigator.sendBeacon() est utilisé pour garantir l'envoi même si l'onglet se ferme
 * 4. Un fallback fetch() est utilisé si sendBeacon n'est pas disponible
 */

import { log, error as logError } from "../utils/logger";
import { getApiBaseUrl } from "../utils/apiClient";

/* ─────────────────────── Types ─────────────────────── */

export interface AnalyticsEvent {
  sessionId: string;
  userIdHash?: string | null;
  eventType: string;
  page: string;
  referrer?: string | null;
  durationMs?: number | null;
  metadata?: Record<string, unknown> | null;
  viewport?: string | null;
  deviceType?: string | null;
  language?: string | null;
  timestamp: string;
}

/* ─────────────────────── Configuration ─────────────────────── */

const FLUSH_INTERVAL_MS = 10_000; // Flush toutes les 10 secondes
const MAX_BUFFER_SIZE = 20; // Flush dès 20 événements
const INGEST_PATH = "/admin/api/analytics/ingest";

/* ─────────────────────── État interne ─────────────────────── */

const buffer: AnalyticsEvent[] = [];
// eslint-disable-next-line @typescript-eslint/no-unused-vars
let flushTimer: ReturnType<typeof setInterval> | null = null;
let initialized = false;

/* ─────────────────────── Helpers ─────────────────────── */

/**
 * Retourne ou crée un sessionId stocké en sessionStorage.
 * Le sessionId est un UUID v4 qui identifie la session de navigation
 * (renouvelé quand l'utilisateur ferme et rouvre le navigateur).
 */
export function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "ssr";

  const key = "immo_analytics_session_id";
  let sessionId = sessionStorage.getItem(key);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem(key, sessionId);
  }
  return sessionId;
}

/**
 * Détecte le type d'appareil à partir du viewport et du user agent.
 * Pas de fingerprinting : on ne stocke que la catégorie (desktop/mobile/tablet).
 */
export function detectDeviceType(): string {
  if (typeof window === "undefined") return "unknown";

  const width = window.innerWidth;
  const ua = navigator.userAgent.toLowerCase();

  // Détection basée sur le user-agent + viewport
  if (
    /tablet|ipad/i.test(ua) ||
    (width >= 768 && width < 1024 && /android/i.test(ua))
  ) {
    return "tablet";
  }
  if (
    /mobile|iphone|ipod|android.*mobile|windows phone/i.test(ua) ||
    width < 768
  ) {
    return "mobile";
  }
  return "desktop";
}

/**
 * Retourne les dimensions du viewport sous forme "WxH".
 */
function getViewport(): string {
  if (typeof window === "undefined") return "0x0";
  return `${window.innerWidth}x${window.innerHeight}`;
}

/* ─────────────────────── Flush ─────────────────────── */

/**
 * Envoie les événements accumulés au backend.
 *
 * Utilise fetch() avec keepalive:true (survit à la fermeture d'onglet)
 * et credentials:"omit" pour éviter le conflit CORS entre
 * Access-Control-Allow-Origin:"*" et credentials mode "include"
 * que sendBeacon déclenche automatiquement quand des cookies existent.
 */
function flush(): void {
  if (buffer.length === 0) return;
  if (typeof window === "undefined") return;

  const events = buffer.splice(0); // Vide le buffer
  const url = `${getApiBaseUrl()}${INGEST_PATH}`;
  const body = JSON.stringify({ events });

  log(`[Analytics] Flush ${events.length} événements vers ${url}`);

  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    keepalive: true,
    credentials: "omit", // Pas de cookies → pas de conflit CORS avec wildcard origin
  }).catch((err) => {
    logError("[Analytics] Erreur lors du flush:", err);
  });
}

/* ─────────────────────── API publique ─────────────────────── */

/**
 * Initialise le tracker analytics.
 * Configure le flush périodique et les listeners de fermeture.
 */
export function initAnalytics(): void {
  if (typeof window === "undefined") return;
  if (initialized) return;

  initialized = true;

  // Flush périodique
  flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);

  // Flush quand l'utilisateur quitte la page ou change d'onglet
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      flush();
    }
  });

  // Flush avant le unload (safety net)
  window.addEventListener("pagehide", flush);

  log("[Analytics] Tracker initialisé");
}

/**
 * Enregistre un événement analytics dans le buffer.
 * Le flush sera déclenché automatiquement quand le buffer est plein
 * ou lors du flush périodique.
 */
export function trackEvent(
  eventType: string,
  page: string,
  extra: Partial<
    Omit<AnalyticsEvent, "sessionId" | "eventType" | "page" | "timestamp">
  > = {},
): void {
  if (typeof window === "undefined") return;

  const event: AnalyticsEvent = {
    sessionId: getOrCreateSessionId(),
    eventType,
    page,
    viewport: getViewport(),
    deviceType: detectDeviceType(),
    language: navigator.language || null,
    timestamp: new Date().toISOString(),
    ...extra,
  };

  buffer.push(event);
  log("[Analytics] Event:", event.eventType, event.page);

  if (buffer.length >= MAX_BUFFER_SIZE) {
    flush();
  }
}

/**
 * Enregistre un événement page_view.
 */
export function trackPageView(page: string, referrer?: string): void {
  trackEvent("page_view", page, {
    referrer: referrer || document.referrer || null,
  });
}

/**
 * Enregistre un événement page_exit avec la durée passée sur la page.
 */
export function trackPageExit(page: string, durationMs: number): void {
  trackEvent("page_exit", page, { durationMs });
}

/**
 * Enregistre un événement session_start (appelé une seule fois par session).
 */
export function trackSessionStart(page: string): void {
  const key = "immo_analytics_session_started";
  if (typeof window === "undefined") return;

  // Ne tracker qu'une seule fois par session
  if (sessionStorage.getItem(key)) return;
  sessionStorage.setItem(key, "1");

  trackEvent("session_start", page, {
    referrer: document.referrer || null,
  });
}

/**
 * Enregistre un événement de clic sur un élément trackable.
 * Utiliser l'attribut data-track-id sur les éléments HTML pour l'identifier.
 */
export function trackClick(
  page: string,
  targetId: string,
  targetLabel?: string,
): void {
  trackEvent("click", page, {
    metadata: { target_id: targetId, target_label: targetLabel || null },
  });
}

/**
 * Enregistre un événement de scroll depth.
 */
export function trackScrollDepth(page: string, depthPercent: number): void {
  trackEvent("scroll_depth", page, {
    metadata: { depth_percent: depthPercent },
  });
}

/**
 * Force le flush immédiat du buffer (utile pour le debug).
 */
export function forceFlush(): void {
  flush();
}
