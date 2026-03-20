"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchJsonWithAuth, getApiBaseUrl } from "../utils/apiClient";
import { DAILY_QUOTA_CHANGED_EVENT } from "../utils/quotaEvents";

export interface DailyQuota {
  used: number;
  remaining: number;
  limit: number;
  reset_at: string;
}

export interface UseQuotaResult {
  quota: DailyQuota | null;
  loading: boolean;
}

/**
 * Récupère le quota journalier de l'utilisateur connecté.
 *
 * N'est actif que si isAuthenticated est true.
 * Appel unique au montage du composant (refresh page → nouveau fetch).
 */
export function useQuota(isAuthenticated: boolean): UseQuotaResult {
  const [quota, setQuota] = useState<DailyQuota | null>(null);
  const [loading, setLoading] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const fetchQuota = useCallback(async () => {
    if (!isAuthenticated) {
      setQuota(null);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchJsonWithAuth<DailyQuota>(
        `${getApiBaseUrl()}/user/api/user/quota/daily`,
        {},
        "Impossible de récupérer le quota",
      );
      if (mountedRef.current) {
        setQuota(data);
      }
    } catch {
      if (mountedRef.current) {
        setQuota(null);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      setQuota(null);
      return;
    }

    let cancelled = false;

    const run = async () => {
      if (cancelled) return;
      await fetchQuota();
    };

    void run();

    const onRefresh = () => {
      if (!cancelled && mountedRef.current) void fetchQuota();
    };
    window.addEventListener(DAILY_QUOTA_CHANGED_EVENT, onRefresh);

    return () => {
      cancelled = true;
      window.removeEventListener(DAILY_QUOTA_CHANGED_EVENT, onRefresh);
    };
  }, [isAuthenticated, fetchQuota]);

  return { quota, loading };
}
