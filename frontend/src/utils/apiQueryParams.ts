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
 * @param options.date_from - Filtre optionnel date de début (ISO string)
 * @param options.date_to - Filtre optionnel date de fin (ISO string)
 */
export function buildPaginatedQuery(params: {
  page: number;
  limit: number;
  url?: string | null;
  scan_type?: string | null;
  date_from?: string | null;
  date_to?: string | null;
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
  if (params.date_from?.trim()) {
    search.set("date_from", params.date_from.trim());
  }
  if (params.date_to?.trim()) {
    search.set("date_to", params.date_to.trim());
  }
  return search.toString();
}

/** Calcule date_from et date_to ISO pour une fenêtre de X jours (par rapport à maintenant). */
export function getDateRangeFromDays(days: number): {
  date_from: string;
  date_to: string;
} {
  const now = new Date();
  const from = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
  return {
    date_from: from.toISOString(),
    date_to: now.toISOString(),
  };
}
