/**
 * Service d'administration pour les métriques de performance API.
 */

import { fetchWithAuth, getApiBaseUrl } from "../../utils/apiClient";
import { error as logError, log } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";
import type { ApiResponse, TimeSeriesPoint } from "../../types";

/**
 * Récupère les métriques de performance agrégées pour l'admin.
 */
export async function getPerformance({
  windowMinutes,
  limit = 50,
}: {
  windowMinutes?: number | null;
  limit?: number;
} = {}): Promise<ApiResponse> {
  try {
    const url = new URL(
      `${getApiBaseUrl()}/admin/api/metrics/performance/summary`,
    );
    if (windowMinutes !== null && windowMinutes !== undefined) {
      url.searchParams.set("window_minutes", windowMinutes.toString());
    }
    url.searchParams.set("limit", limit.toString());

    log("[AdminMetricsService] Appel API métriques:", url.toString());

    const response = await fetchWithAuth(url.toString(), {
      method: "GET",
    });

    log(
      "[AdminMetricsService] Réponse status:",
      response.status,
      response.statusText,
    );

    const data = await response.json();
    log("[AdminMetricsService] Données reçues:", data);

    if (response.ok && Array.isArray(data.metrics)) {
      log(
        "[AdminMetricsService] Métriques retournées:",
        data.metrics.length,
        "entrées",
      );
      return {
        success: true,
        metrics: data.metrics,
      };
    }

    logError("[AdminMetricsService] Erreur dans la réponse:", data);
    const errorMessage =
      data.detail ||
      data.error ||
      "Erreur lors de la récupération des métriques";
    showErrorToast(errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  } catch (err: unknown) {
    logError("[AdminMetricsService] Erreur lors de l'appel API:", err);
    showErrorToast(getToastT()("admin.toast.loadPerfMetrics"));
    return {
      success: false,
      error: "Erreur de connexion au serveur",
    };
  }
}

/**
 * Récupère les métriques de performance agrégées par service backend.
 */
export async function getServicePerformance({
  windowMinutes,
  limit = 50,
}: {
  windowMinutes?: number | null;
  limit?: number;
} = {}): Promise<ApiResponse> {
  try {
    const url = new URL(
      `${getApiBaseUrl()}/admin/api/metrics/performance/services`,
    );
    if (windowMinutes !== null && windowMinutes !== undefined) {
      url.searchParams.set("window_minutes", windowMinutes.toString());
    }
    url.searchParams.set("limit", limit.toString());

    const response = await fetchWithAuth(url.toString(), {
      method: "GET",
    });

    const data = await response.json();

    if (response.ok && Array.isArray(data.metrics)) {
      return {
        success: true,
        metrics: data.metrics,
      };
    }

    const errorMessage =
      data.detail ||
      data.error ||
      "Erreur lors de la récupération des métriques services";
    showErrorToast(errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  } catch (err: unknown) {
    logError("[AdminMetricsService] Erreur lors de l'appel API services:", err);
    showErrorToast(getToastT()("admin.toast.loadServiceMetrics"));
    return {
      success: false,
      error: "Erreur de connexion au serveur",
    };
  }
}

/**
 * Récupère une série temporelle de métriques pour tracer un graphe d'évolution.
 */
export async function getTimeseries({
  route,
  servicePrefix,
  windowMinutes = 10080,
  bucketMinutes,
}: {
  route?: string | null;
  servicePrefix?: string | null;
  windowMinutes?: number;
  bucketMinutes?: number | null;
} = {}): Promise<
  ApiResponse & { points?: TimeSeriesPoint[]; bucketMinutes?: number }
> {
  try {
    const url = new URL(
      `${getApiBaseUrl()}/admin/api/metrics/performance/timeseries`,
    );
    if (route) {
      url.searchParams.set("route", route);
    }
    if (servicePrefix) {
      url.searchParams.set("service_prefix", servicePrefix);
    }
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
      data.detail ||
      data.error ||
      "Erreur lors de la récupération des données temporelles";
    showErrorToast(errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  } catch (err: unknown) {
    logError(
      "[AdminMetricsService] Erreur lors de l'appel API timeseries:",
      err,
    );
    showErrorToast(getToastT()("admin.toast.loadTimeData"));
    return {
      success: false,
      error: "Erreur de connexion au serveur",
    };
  }
}
