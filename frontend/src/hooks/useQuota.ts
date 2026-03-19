"use client";

import { useEffect, useRef, useState } from "react";
import { fetchJsonWithAuth, getApiBaseUrl } from "../utils/apiClient";

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

  useEffect(() => {
    if (!isAuthenticated) {
      setQuota(null);
      return;
    }

    let cancelled = false;

    const fetch = async () => {
      setLoading(true);
      try {
        const data = await fetchJsonWithAuth<DailyQuota>(
          `${getApiBaseUrl()}/user/api/user/quota/daily`,
          {},
          "Impossible de récupérer le quota",
        );
        if (!cancelled && mountedRef.current) {
          setQuota(data);
        }
      } catch {
        // Échec silencieux : ne pas casser le header si le quota est indisponible
        if (!cancelled && mountedRef.current) {
          setQuota(null);
        }
      } finally {
        if (!cancelled && mountedRef.current) {
          setLoading(false);
        }
      }
    };

    fetch();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  return { quota, loading };
}
