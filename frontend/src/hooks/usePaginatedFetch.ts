"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface PaginatedFetchResult<T> {
  items: T[];
  setItems: React.Dispatch<React.SetStateAction<T[]>>;
  total: number;
  setTotal: React.Dispatch<React.SetStateAction<number>>;
  page: number;
  setPage: (page: number | ((p: number) => number)) => void;
  loading: boolean;
  load: (pageOverride?: number) => Promise<void>;
  totalPages: number;
}

interface UsePaginatedFetchOptions<T> {
  fetchFn: (
    page: number,
    perPage: number,
  ) => Promise<{ items: T[]; total: number }>;
  perPage?: number;
  onError?: () => void;
  /** Déclenche un rechargement quand la valeur change (ex. page, filterUrl). */
  refreshTrigger?: number | string;
}

/**
 * Hook pour gérer le chargement paginé (items, total, page, load, totalPages).
 * Utilise des refs pour fetchFn/onError afin d'éviter des rechargements en boucle.
 */
export function usePaginatedFetch<T>({
  fetchFn,
  perPage = 10,
  onError,
  refreshTrigger = 0,
}: UsePaginatedFetchOptions<T>): PaginatedFetchResult<T> {
  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchFnRef = useRef(fetchFn);
  const onErrorRef = useRef(onError);
  fetchFnRef.current = fetchFn;
  onErrorRef.current = onError;

  const load = useCallback(
    async (pageOverride?: number) => {
      const p = pageOverride ?? page;
      setLoading(true);
      try {
        const res = await fetchFnRef.current(p, perPage);
        setItems(res.items);
        setTotal(res.total);
        if (pageOverride !== undefined) setPage(pageOverride);
      } catch {
        onErrorRef.current?.();
      } finally {
        setLoading(false);
      }
    },
    [page, perPage],
  );

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  const totalPages = Math.max(1, Math.ceil(total / perPage));

  return {
    items,
    setItems,
    total,
    setTotal,
    page,
    setPage,
    loading,
    load,
    totalPages,
  };
}
