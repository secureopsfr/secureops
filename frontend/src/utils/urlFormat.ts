/**
 * Utilitaires de formatage d'URL pour l'affichage.
 */

/**
 * Formate une URL pour l'affichage (retire protocole et slash final).
 *
 * @param url - URL brute (ex. https://example.com/)
 * @returns URL simplifiée (ex. example.com)
 */
export function formatUrlDisplay(url: string): string {
  return url.replace(/^https?:\/\//, "").replace(/\/$/, "") || url;
}
