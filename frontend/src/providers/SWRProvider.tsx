"use client";

import { SWRConfig } from "swr";
import type { ReactNode } from "react";

/**
 * Configuration globale SWR.
 *
 * – dedupingInterval : évite les appels en double pendant 30 s
 * – revalidateOnFocus : désactivé par défaut (les données admin ne changent
 *   pas aussi souvent et l'utilisateur peut rafraîchir manuellement)
 * – revalidateOnReconnect : réactif si la connexion réseau revient
 * – errorRetryCount : 2 tentatives max en cas d'erreur réseau
 * – shouldRetryOnError : seulement pour les erreurs réseau, pas les 4xx
 */
export function SWRProvider({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        dedupingInterval: 30_000,
        revalidateOnFocus: false,
        revalidateOnReconnect: true,
        errorRetryCount: 2,
        keepPreviousData: true,
      }}
    >
      {children}
    </SWRConfig>
  );
}
