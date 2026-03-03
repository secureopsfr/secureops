/**
 * Types génériques pour les réponses API.
 */

/**
 * Réponse paginée standard (items, total, page, per_page, total_pages).
 */
export interface PaginatedListResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
