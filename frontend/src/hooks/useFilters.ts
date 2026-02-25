/**
 * Hook personnalisé pour gérer les filtres dans les composants admin.
 * Simplifie la gestion des états de filtres multiples.
 */

import { useState, useCallback, useMemo } from "react";

interface UseFiltersReturn<T> {
  filters: T;
  updateFilter: (key: keyof T, value: T[keyof T]) => void;
  resetFilters: () => void;
  hasActiveFilters: boolean;
  setFilters: (filters: T) => void;
}

export function useFilters<T extends Record<string, unknown>>(
  initialFilters: T,
): UseFiltersReturn<T> {
  const [filters, setFilters] = useState<T>(initialFilters);

  const updateFilter = useCallback((key: keyof T, value: T[keyof T]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
  }, [initialFilters]);

  const hasActiveFilters = useMemo(() => {
    return Object.entries(filters).some(([key, value]) => {
      const initialValue = initialFilters[key as keyof T];
      // Vérifier si la valeur est différente de la valeur initiale
      if (value === null || value === undefined || value === "") {
        return (
          initialValue !== null &&
          initialValue !== undefined &&
          initialValue !== ""
        );
      }
      return value !== initialValue;
    });
  }, [filters, initialFilters]);

  return {
    filters,
    updateFilter,
    resetFilters,
    hasActiveFilters,
    setFilters,
  };
}
