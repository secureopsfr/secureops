/**
 * Stockage temporaire des résultats de scan (sessionStorage).
 * Permet de conserver les résultats pendant la redirection vers la connexion.
 */

import type { ScanResult } from "../services/scanService";

const STORAGE_KEY = "secureops-pending-scan-results";

/**
 * Enregistre les résultats en attente (utilisateur non connecté).
 */
export function savePendingScanResult(result: ScanResult): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(result));
  } catch {
    // sessionStorage full ou indisponible
  }
}

/**
 * Récupère et supprime les résultats en attente.
 */
export function consumePendingScanResult(): ScanResult | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    sessionStorage.removeItem(STORAGE_KEY);
    return JSON.parse(raw) as ScanResult;
  } catch {
    return null;
  }
}

/**
 * Vérifie si des résultats sont en attente (sans les consommer).
 */
export function hasPendingScanResult(): boolean {
  if (typeof window === "undefined") return false;
  return sessionStorage.getItem(STORAGE_KEY) !== null;
}
