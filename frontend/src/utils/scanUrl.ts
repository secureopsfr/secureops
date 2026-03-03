/**
 * Normalise l'URL pour un scan : ajoute https:// si pas de schéma.
 * Utilisé par le scanner direct et les scans planifiés (mêmes garde-fous).
 */
export function normalizeScanUrl(url: string): string {
  const trimmed = url.trim();
  if (!trimmed) return trimmed;
  if (trimmed.match(/^https?:\/\//i)) return trimmed;
  if (trimmed.includes("://")) return trimmed; // Schéma invalide (file:, ftp:, etc.)
  return `https://${trimmed}`;
}
