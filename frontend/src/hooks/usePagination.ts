/**
 * Hook personnalisé pour gérer la pagination (offset ou page-based).
 * Simplifie la gestion de la pagination dans les composants admin.
 */

import { useState, useCallback } from "react";

interface UsePaginationReturn {
  offset: number;
  limit: number;
  page: number;
  setPage: (page: number) => void;
  handleNext: () => void;
  handlePrevious: () => void;
  reset: () => void;
  setLimit: (limit: number) => void;
}

export function usePagination(initialLimit = 20): UsePaginationReturn {
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(initialLimit);
  const [page, setPage] = useState(0);

  const handleNext = useCallback(() => {
    setOffset((prev) => prev + limit);
    setPage((prev) => prev + 1);
  }, [limit]);

  const handlePrevious = useCallback(() => {
    setOffset((prev) => Math.max(0, prev - limit));
    setPage((prev) => Math.max(0, prev - 1));
  }, [limit]);

  const reset = useCallback(() => {
    setOffset(0);
    setPage(0);
  }, []);

  const updateLimit = useCallback((newLimit: number) => {
    setLimit(newLimit);
    // Recalculer l'offset pour rester sur une "page" valide
    setOffset(0);
    setPage(0);
  }, []);

  return {
    offset,
    limit,
    page,
    setPage,
    handleNext,
    handlePrevious,
    reset,
    setLimit: updateLimit,
  };
}
