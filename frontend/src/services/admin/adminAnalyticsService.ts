/**
 * Service d'administration pour les analytics du site.
 */

import { fetchWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";
import type {
  ApiResponse,
  PageViewsSummaryResponse,
  ReferrerSummary,
  TrafficTimeSeriesPoint,
  DeviceBreakdown,
} from "../../types";

/**
 * Récupère les métriques de vues par page et les KPI globaux.
 */
export async function getPageViewsSummary({
  windowMinutes,
  limit = 50,
}: {
  windowMinutes?: number | null;
  limit?: number;
} = {}): Promise<ApiResponse & { data?: PageViewsSummaryResponse }> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/analytics/pages`);
    if (windowMinutes !== null && windowMinutes !== undefined) {
      url.searchParams.set("window_minutes", windowMinutes.toString());
    }
    url.searchParams.set("limit", limit.toString());

    const response = await fetchWithAuth(url.toString(), {
      method: "GET",
    });

    const data = await response.json();

    if (response.ok) {
      return {
        success: true,
        data,
      };
    }

    const errorMessage =
      data.detail ||
      data.error ||
      "Erreur lors de la récupération des analytics";
    showErrorToast(errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  } catch (err: unknown) {
    logError(
      "[AdminAnalyticsService] Erreur lors de l'appel API analytics pages:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadAnalytics"));
    return {
      success: false,
      error: "Erreur de connexion au serveur",
    };
  }
}

/**
 * Récupère le top des referrers.
 */
export async function getReferrersSummary({
  windowMinutes,
  limit = 20,
}: {
  windowMinutes?: number | null;
  limit?: number;
} = {}): Promise<ApiResponse & { referrers?: ReferrerSummary[] }> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/analytics/referrers`);
    if (windowMinutes !== null && windowMinutes !== undefined) {
      url.searchParams.set("window_minutes", windowMinutes.toString());
    }
    url.searchParams.set("limit", limit.toString());

    const response = await fetchWithAuth(url.toString(), {
      method: "GET",
    });

    const data = await response.json();

    if (response.ok && Array.isArray(data.referrers)) {
      return {
        success: true,
        referrers: data.referrers,
      };
    }

    const errorMessage =
      data.detail ||
      data.error ||
      "Erreur lors de la récupération des referrers";
    showErrorToast(errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  } catch (err: unknown) {
    logError(
      "[AdminAnalyticsService] Erreur lors de l'appel API referrers:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadReferrers"));
    return {
      success: false,
      error: "Erreur de connexion au serveur",
    };
  }
}

/**
 * Récupère la série temporelle de trafic (vues + visiteurs uniques par bucket).
 */
export async function getTrafficTimeseries({
  windowMinutes = 10080,
  bucketMinutes,
}: {
  windowMinutes?: number;
  bucketMinutes?: number | null;
} = {}): Promise<
  ApiResponse & { points?: TrafficTimeSeriesPoint[]; bucketMinutes?: number }
> {
  try {
    const url = new URL(
      `${getApiBaseUrl()}/admin/api/analytics/traffic/timeseries`,
    );
    url.searchParams.set("window_minutes", windowMinutes.toString());
    if (bucketMinutes != null && bucketMinutes > 0) {
      url.searchParams.set("bucket_minutes", bucketMinutes.toString());
    }

    const response = await fetchWithAuth(url.toString(), {
      method: "GET",
    });

    const data = await response.json();

    if (response.ok && Array.isArray(data.points)) {
      return {
        success: true,
        points: data.points,
        bucketMinutes: data.bucketMinutes,
      };
    }

    const errorMessage =
      data.detail || data.error || "Erreur lors de la récupération du trafic";
    showErrorToast(errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  } catch (err: unknown) {
    logError(
      "[AdminAnalyticsService] Erreur lors de l'appel API traffic timeseries:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadTraffic"));
    return {
      success: false,
      error: "Erreur de connexion au serveur",
    };
  }
}

/**
 * Récupère la répartition par type d'appareil.
 */
export async function getDeviceBreakdown({
  windowMinutes,
}: {
  windowMinutes?: number | null;
} = {}): Promise<ApiResponse & { devices?: DeviceBreakdown[] }> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/analytics/devices`);
    if (windowMinutes !== null && windowMinutes !== undefined) {
      url.searchParams.set("window_minutes", windowMinutes.toString());
    }

    const response = await fetchWithAuth(url.toString(), {
      method: "GET",
    });

    const data = await response.json();

    if (response.ok && Array.isArray(data.devices)) {
      return {
        success: true,
        devices: data.devices,
      };
    }

    const errorMessage =
      data.detail ||
      data.error ||
      "Erreur lors de la récupération des données appareils";
    showErrorToast(errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  } catch (err: unknown) {
    logError(
      "[AdminAnalyticsService] Erreur lors de l'appel API devices:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadDevices"));
    return {
      success: false,
      error: "Erreur de connexion au serveur",
    };
  }
}
