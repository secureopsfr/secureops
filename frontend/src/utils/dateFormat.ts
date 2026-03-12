/**
 * Formate une date en format long français (ex: "12 février 2026").
 * @param dateString - Date ISO ou null/undefined
 * @returns Date formatée ou "—" si invalide
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return "—";
  try {
    return new Date(dateString).toLocaleDateString("fr-FR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateString;
  }
}

/**
 * Formate une date avec heure en format long français (ex: "12 février 2026 à 14:30").
 * @param dateString - Date ISO ou null/undefined
 * @param fallback - Valeur de retour si dateString est null/undefined (défaut "—")
 * @returns Date/heure formatée ou fallback si invalide
 */
export function formatDateTime(
  dateString: string | null | undefined,
  fallback: string = "—",
): string {
  if (!dateString) return fallback;
  try {
    return new Date(dateString).toLocaleString("fr-FR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

/**
 * Formate une date avec heure en format court français (ex: "12 févr., 14:30").
 * @param dateString - Date ISO ou null/undefined
 * @returns Date/heure formatée en court ou "—" si invalide
 */
export function formatDateTimeShort(
  dateString: string | null | undefined,
): string {
  if (!dateString) return "—";
  try {
    return new Date(dateString).toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

/**
 * Formate un timestamp pour les axes de graphiques, en adaptant le format
 * selon la fenêtre temporelle affichée.
 * - ≤ 24h : heure seulement (ex: "14:30")
 * - ≤ 7j  : date + heure (ex: "12/02 14:30")
 * - > 7j  : date seulement (ex: "12/02")
 * @param ts - Timestamp ISO
 * @param windowMinutes - Fenêtre temporelle en minutes
 * @returns Timestamp formaté
 */
export function formatTimestamp(ts: string, windowMinutes: number): string {
  const d = new Date(ts);
  if (windowMinutes <= 1440) {
    return d.toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  if (windowMinutes <= 10080) {
    return d.toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
}

/**
 * Calcule le temps écoulé depuis une date (pour affichage "il y a X min/h/j").
 * @param dateString - Date ISO
 * @returns { unit, value } ou null si date invalide
 */
export function getTimeAgo(dateString: string | null | undefined): {
  unit: "minutes" | "hours" | "days";
  value: number;
} | null {
  if (!dateString) return null;
  const d = new Date(dateString);
  if (Number.isNaN(d.getTime())) return null;
  const now = Date.now();
  const diffMs = now - d.getTime();
  const diffM = Math.floor(diffMs / (60 * 1000));
  const diffH = Math.floor(diffMs / (60 * 60 * 1000));
  const diffD = Math.floor(diffMs / (24 * 60 * 60 * 1000));
  if (diffM < 60) return { unit: "minutes", value: Math.max(1, diffM) };
  if (diffH < 24) return { unit: "hours", value: diffH };
  return { unit: "days", value: diffD };
}
