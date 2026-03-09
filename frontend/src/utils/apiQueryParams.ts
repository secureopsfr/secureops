/**
 * Utilitaires pour construire les paramètres de requête API (pagination, filtres).
 */

/**
 * Construit une chaîne de paramètres pour les requêtes paginées.
 *
 * @param options.page - Numéro de page
 * @param options.limit - Nombre d'éléments par page
 * @param options.url - Filtre optionnel par URL
 * @param options.scan_type - Filtre optionnel par type (frontend, backend, custom)
 */
export function buildPaginatedQuery(params: {
  page: number;
  limit: number;
  url?: string | null;
  scan_type?: string | null;
}): string {
  const search = new URLSearchParams({
    page: String(params.page),
    limit: String(params.limit),
  });
  if (params.url?.trim()) {
    search.set("url", params.url.trim());
  }
  if (
    params.scan_type &&
    ["frontend", "backend", "custom"].includes(params.scan_type)
  ) {
    search.set("scan_type", params.scan_type);
  }
  return search.toString();
}
