/**
 * Hook SWR pour les KPIs et données du graphique scanner.
 */

import useSWR from "swr";
import {
  getScanOverview,
  type ScanOverviewResponse,
} from "../../services/scanHistoryService";

function overviewFetcher(params: {
  url: string | null;
  scan_type: string | null;
  date_from: string | null;
  date_to: string | null;
}): Promise<ScanOverviewResponse> {
  return getScanOverview(
    params.url ?? undefined,
    params.scan_type ?? undefined,
    params.date_from ?? undefined,
    params.date_to ?? undefined,
  );
}

function overviewKey(
  url: string | null,
  scan_type: string | null,
  date_from: string | null,
  date_to: string | null,
): [string, typeof url, typeof scan_type, typeof date_from, typeof date_to] {
  return ["scan-overview", url, scan_type, date_from, date_to];
}

export function useScanOverview(
  url: string | null,
  scan_type: string | null,
  date_from: string | null,
  date_to: string | null,
) {
  const { data, error, isLoading, mutate } = useSWR(
    overviewKey(url, scan_type, date_from, date_to),
    ([, u, st, df, dt]) =>
      overviewFetcher({ url: u, scan_type: st, date_from: df, date_to: dt }),
  );

  return {
    overview: data,
    isLoading,
    error,
    mutate,
  };
}
