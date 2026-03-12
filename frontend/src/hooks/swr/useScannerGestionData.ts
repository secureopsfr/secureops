/**
 * Hook SWR pour les données de la page vue d'ensemble du scanner.
 * Remplace les deux useEffect indépendants (URL list + subscription).
 */

import useSWR from "swr";
import { getScanHistory } from "../../services/scanHistoryService";
import userService from "../../services/userService";

interface ScannerGestionData {
  urlOptions: string[];
  historyRetentionDays: number | null;
}

async function fetchScannerGestionData(): Promise<ScannerGestionData> {
  const [historyRes, subscriptionRes] = await Promise.all([
    getScanHistory(1, 100),
    userService.getSubscription(),
  ]);

  const urlOptions = [...new Set(historyRes.items.map((i) => i.url))];

  const raw = subscriptionRes.subscription?.history_retention;
  const retention = typeof raw === "string" ? raw : "30";
  const days = retention === "none" ? null : parseInt(retention, 10);
  const historyRetentionDays = Number.isNaN(days) ? null : days;

  return { urlOptions, historyRetentionDays };
}

export function useScannerGestionData() {
  const { data, isLoading, error } = useSWR<ScannerGestionData>(
    "scanner-gestion-data",
    fetchScannerGestionData,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  );

  return {
    urlOptions: data?.urlOptions ?? [],
    historyRetentionDays: data?.historyRetentionDays ?? null,
    isLoading,
    error,
  };
}
