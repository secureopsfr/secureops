"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { BarChart3, Eye, TrendingUp } from "lucide-react";
import Card from "../ui/cards/Card";
import BarLineEvolutionChart, {
  BarLineEvolutionChartToggles,
} from "../charts/BarLineEvolutionChart";
import Table from "../Table";
import { DropdownSelector } from "../buttons";
import adminService from "../../services/admin";
import type { TimeSeriesPoint } from "../../services/admin";
import { error as logError } from "../../utils/logger";
import { formatTimestamp } from "../../utils/dateFormat";
import { AdminInlineLoading } from "./AdminSectionLoading";
import { useLanguage } from "../LanguageProvider";

/* ─────────────────────── constantes ─────────────────────── */

export const WINDOW_OPTIONS = [
  { value: "5", label: "5 min" },
  { value: "15", label: "15 min" },
  { value: "30", label: "30 min" },
  { value: "60", label: "1 heure" },
  { value: "360", label: "6 heures" },
  { value: "1440", label: "24 heures" },
  { value: "10080", label: "7 jours" },
  { value: "43200", label: "30 jours" },
];

/** Toutes les valeurs de pas possibles avec leur label lisible. */
const ALL_BUCKET_OPTIONS = [
  { minutes: 1, label: "1 min" },
  { minutes: 5, label: "5 min" },
  { minutes: 15, label: "15 min" },
  { minutes: 30, label: "30 min" },
  { minutes: 60, label: "1 heure" },
  { minutes: 120, label: "2 heures" },
  { minutes: 360, label: "6 heures" },
  { minutes: 720, label: "12 heures" },
  { minutes: 1440, label: "24 heures" },
];

/**
 * Calcule automatiquement le pas (bucket) en minutes en fonction de la fenêtre.
 * Miroir de la logique backend `_auto_bucket_minutes`.
 */
export function autoBucketMinutes(windowMinutes: number): number {
  if (windowMinutes <= 60) return 1;
  if (windowMinutes <= 360) return 5;
  if (windowMinutes <= 1440) return 15;
  if (windowMinutes <= 10080) return 60;
  if (windowMinutes <= 43200) return 360;
  return 1440;
}

/**
 * Retourne les options de pas filtrées selon la fenêtre :
 *  - min : 1 min (toujours)
 *  - max : fenêtre / 2 (il faut au moins 2 points)
 *  - on s'assure que la valeur auto est présente dans la liste
 */
export function getBucketOptions(
  windowMinutes: number,
): { value: string; label: string }[] {
  const maxBucket = Math.floor(windowMinutes / 2);
  const autoValue = autoBucketMinutes(windowMinutes);
  const filtered = ALL_BUCKET_OPTIONS.filter(
    (b) => b.minutes >= 1 && b.minutes <= maxBucket,
  );
  // S'assurer que la valeur auto est toujours présente
  if (
    !filtered.some((b) => b.minutes === autoValue) &&
    autoValue <= maxBucket
  ) {
    filtered.push({ minutes: autoValue, label: `${autoValue} min` });
    filtered.sort((a, b) => a.minutes - b.minutes);
  }
  return filtered.map((b) => ({
    value: String(b.minutes),
    label: b.minutes === autoValue ? `${b.label} (auto)` : b.label,
  }));
}

type MetricToggle = "count" | "avgMs";

/* ─────────────────────── helpers ─────────────────────── */

/* ─────────────────────── types ─────────────────────── */

interface RouteMetricsProps {
  metrics?: Record<string, unknown>[];
  windowMinutes: number | null;
  bucketMinutes: number;
  title?: string;
  entityLabel?: string;
  entityKey?: string;
  emptyMessage?: string;
}

/**
 * Affiche une carte contenant :
 *  1. Un graphique d'évolution temporelle (requêtes / temps moyen)
 *  2. Un tableau détaillé des métriques par entité (route ou service)
 *
 * Le sélecteur Route/Service est local à chaque bulle.
 * Fenêtre et Pas sont gérés par le parent.
 */
export default function RouteMetrics({
  metrics: propsMetrics,
  windowMinutes,
  bucketMinutes,
  title,
  entityLabel,
  entityKey = "route",
  emptyMessage,
}: RouteMetricsProps) {
  const { t } = useLanguage();
  const resolvedTitle = title ?? t("admin.api.routeMetrics");
  const resolvedEntityLabel = entityLabel ?? "Route";
  const resolvedEmptyMessage = emptyMessage ?? t("admin.api.noPerformanceData");
  const effectiveWindowMinutes = windowMinutes ?? 10080;

  /* ── état tableau ── */
  const [viewMode, setViewMode] = useState<"summary" | "detailed">("summary");
  const [internalMetrics, setInternalMetrics] = useState<
    Record<string, unknown>[]
  >([]);
  const [, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  /* ── état local (entité + graphique) ── */
  const [selectedEntity, setSelectedEntity] = useState<string>("__all__");
  const [toggles, setToggles] = useState<Set<MetricToggle>>(
    new Set(["count", "avgMs"]),
  );
  const [points, setPoints] = useState<TimeSeriesPoint[]>([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);

  const metrics = propsMetrics !== undefined ? propsMetrics : internalMetrics;

  /* ── entités disponibles (routes ou services) ── */
  const availableEntities = useMemo(() => {
    const entities = new Set<string>();
    for (const m of metrics) {
      const val = m[entityKey] as string | undefined;
      if (val) entities.add(val);
    }
    return Array.from(entities).sort();
  }, [metrics, entityKey]);

  const entityOptions = useMemo(() => {
    const allLabel =
      entityKey === "servicePrefix"
        ? t("admin.api.allServices")
        : t("admin.api.allRoutes");
    return [
      { value: "__all__", label: allLabel },
      ...availableEntities.map((e) => ({ value: e, label: e })),
    ];
  }, [availableEntities, entityKey, t]);

  /* ── métriques filtrées par entité sélectionnée (pour le tableau) ── */
  const filteredMetrics = useMemo(() => {
    if (selectedEntity === "__all__") return metrics;
    return metrics.filter((m) => m[entityKey] === selectedEntity);
  }, [metrics, selectedEntity, entityKey]);

  /* ── chargement données tableau ── */
  const loadMetrics = useCallback(async () => {
    if (propsMetrics !== undefined) return;

    setLoading(true);
    setFetchError(null);
    try {
      let result;
      const params =
        windowMinutes !== null && windowMinutes !== undefined
          ? { windowMinutes, limit: 50 }
          : { limit: 50 };

      if (entityKey === "route") {
        result = await adminService.getPerformance(params);
      } else if (entityKey === "servicePrefix") {
        result = await adminService.getServicePerformance(params);
      } else {
        result = { success: false, error: "Invalid entityKey" };
      }

      if (result.success && Array.isArray(result.metrics)) {
        setInternalMetrics(result.metrics as Record<string, unknown>[]);
      } else {
        setInternalMetrics([]);
        setFetchError(result.error || t("routeMetrics.errorLoad"));
      }
    } catch (err: unknown) {
      logError(
        `[RouteMetrics] Erreur lors du chargement des métriques (${entityLabel}):`,
        err,
      );
      setInternalMetrics([]);
      setFetchError(
        err instanceof Error ? err.message : t("routeMetrics.errorConnection"),
      );
    } finally {
      setLoading(false);
    }
  }, [windowMinutes, entityKey, entityLabel, propsMetrics, t]);

  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  /* ── compteur pour forcer un retry manuel ── */
  const [tsRetryKey, setTsRetryKey] = useState(0);

  /* ── chargement données graphique (même fenêtre + même entité + même pas) ── */
  useEffect(() => {
    let cancelled = false;

    (async () => {
      setChartLoading(true);
      setChartError(null);
      try {
        const isServiceMode = entityKey === "servicePrefix";
        const res = await adminService.getTimeseries({
          route:
            !isServiceMode && selectedEntity !== "__all__"
              ? selectedEntity
              : null,
          servicePrefix:
            isServiceMode && selectedEntity !== "__all__"
              ? selectedEntity
              : null,
          windowMinutes: effectiveWindowMinutes,
          bucketMinutes,
        });
        if (cancelled) return;
        if (res.success && Array.isArray(res.points)) {
          setPoints(res.points);
        } else {
          setPoints([]);
          setChartError(res.error || t("routeMetrics.errorLoadData"));
        }
      } catch (err: unknown) {
        if (cancelled) return;
        logError("[RouteMetrics] Erreur timeseries:", err);
        setPoints([]);
        setChartError(
          err instanceof Error
            ? err.message
            : t("routeMetrics.errorConnectionShort"),
        );
      } finally {
        if (!cancelled) setChartLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    t,
    selectedEntity,
    effectiveWindowMinutes,
    bucketMinutes,
    entityKey,
    tsRetryKey,
  ]);

  /* ── handlers ── */
  const handleToggle = (metric: MetricToggle) => {
    setToggles((prev) => {
      const next = new Set(prev);
      if (next.has(metric)) {
        if (next.size > 1) next.delete(metric);
      } else {
        next.add(metric);
      }
      return next;
    });
  };

  /* ── données chart ── */
  const chartData = useMemo(
    () =>
      points.map((p) => ({
        ts: formatTimestamp(p.timestamp, effectiveWindowMinutes),
        count: p.count,
        avgMs: p.avgMs != null ? Math.round(p.avgMs * 100) / 100 : null,
      })),
    [points, effectiveWindowMinutes],
  );

  const showCount = toggles.has("count");
  const showAvgMs = toggles.has("avgMs");

  /* ── helpers tableau ── */
  const hasTableData =
    Array.isArray(filteredMetrics) && filteredMetrics.length > 0;

  const formatNumber = (value: unknown) => {
    if (value == null) return "—";
    if (typeof value === "number") {
      return Number.isInteger(value) ? value.toString() : value.toFixed(2);
    }
    return String(value);
  };

  const formatPercent = (value: unknown) => {
    if (value == null) return "—";
    return `${((value as number) * 100).toFixed(2)}%`;
  };

  const getErrorCount = (m: Record<string, unknown>) => {
    const count = (m.requestCount as number) ?? (m.count as number) ?? 0;
    const clientErrors = count * ((m.clientErrorRate as number) ?? 0);
    const serverErrors = count * ((m.serverErrorRate as number) ?? 0);
    return Math.round(clientErrors + serverErrors);
  };

  /* ─────────────────────── état loading / erreur global ─────────────────────── */

  if (fetchError && metrics.length === 0) {
    return (
      <Card disableHover>
        <div className="py-12 text-center">
          <p className="text-[rgb(var(--danger))] mb-4">{fetchError}</p>
          <button
            onClick={loadMetrics}
            className="px-4 py-2 rounded-lg bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] hover:bg-[rgba(var(--primary),0.3)] transition-colors"
          >
            {t("admin.common.retry")}
          </button>
        </div>
      </Card>
    );
  }

  /* ─────────────────────── rendu ─────────────────────── */

  return (
    <Card disableHover className="no-hover" style={{ overflow: "visible" }}>
      {/* ═══════════ En-tête principal + sélecteurs partagés ═══════════ */}
      <div className="flex flex-col gap-4 mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Titre */}
          <div className="flex items-center gap-3" style={{ minWidth: 0 }}>
            <BarChart3
              className="w-5 h-5 text-[rgb(var(--primary))]"
              style={{ flexShrink: 0 }}
            />
            <h2
              className="text-xl font-bold text-[var(--text)]"
              style={{ margin: 0 }}
            >
              {resolvedTitle}
            </h2>
          </div>

          {/* Sélecteur Route/Service (local à chaque bulle) */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[var(--muted)]">{resolvedEntityLabel} :</span>
            <DropdownSelector
              selectedValue={selectedEntity}
              onChange={setSelectedEntity}
              options={entityOptions}
              width="18rem"
            />
          </div>
        </div>
      </div>

      {/* ═══════════ SECTION 1 : Évolution temporelle ═══════════ */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <h3
              className="text-base font-semibold text-[var(--text)]"
              style={{ margin: 0 }}
            >
              {t("admin.api.timeEvolution")}
            </h3>
          </div>

          <BarLineEvolutionChartToggles
            toggleOptions={[
              { key: "count", label: t("admin.api.requestsToggle") },
              {
                key: "avgMs",
                label: t("admin.api.avgTimeToggle"),
                activeColor: "blue",
              },
            ]}
            activeKeys={toggles}
            onToggle={(k) => handleToggle(k as MetricToggle)}
          />
        </div>

        {/* Contenu graphique */}
        {chartLoading && points.length === 0 && (
          <AdminInlineLoading message={t("admin.api.loadingChart")} />
        )}

        {chartError && points.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-[rgb(var(--danger))] mb-4">{chartError}</p>
            <button
              onClick={() => setTsRetryKey((k) => k + 1)}
              className="px-4 py-2 rounded-lg bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] hover:bg-[rgba(var(--primary),0.3)] transition-colors"
            >
              {t("admin.common.retry")}
            </button>
          </div>
        )}

        {!chartLoading && !chartError && chartData.length === 0 && (
          <div className="py-8 text-center">
            <TrendingUp className="w-10 h-10 text-[var(--muted)] mx-auto mb-3 opacity-50" />
            <p className="text-sm text-[var(--muted)]">
              {t("admin.api.noDataSelection")}
            </p>
          </div>
        )}

        {chartData.length > 0 && (
          <BarLineEvolutionChart
            data={chartData}
            xAxisKey="ts"
            height={320}
            barSeries={{
              dataKey: "count",
              name: t("admin.api.chartRequests"),
              yAxisId: "left",
              fill: "rgba(var(--primary), 0.6)",
              maxBarSize: 32,
            }}
            showBar={showCount}
            curveSeries={{
              type: "line",
              dataKey: "avgMs",
              name: t("admin.api.chartAvgTime"),
            }}
            showCurve={showAvgMs}
            showDotsThreshold={60}
          />
        )}
      </div>

      {/* ═══════════ Séparateur ═══════════ */}
      <hr
        style={{
          border: "none",
          borderTop: "1px solid var(--border)",
          margin: "0 0 1.5rem 0",
          opacity: 0.5,
        }}
      />

      {/* ═══════════ SECTION 2 : Détail par endpoint / service ═══════════ */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <h3
              className="text-base font-semibold text-[var(--text)]"
              style={{ margin: 0 }}
            >
              {entityKey === "servicePrefix"
                ? t("admin.api.detailByService")
                : t("admin.api.detailByRoute")}
            </h3>
          </div>

          {/* Vue résumé / détaillé (spécifique au tableau) */}
          <div className="flex gap-2 rounded-lg border border-[var(--border)] p-1 bg-[var(--color-surface-subtle)]">
            <button
              type="button"
              onClick={() => setViewMode("summary")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                viewMode === "summary"
                  ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                  : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
              }`}
            >
              {t("admin.api.summary")}
            </button>
            <button
              type="button"
              onClick={() => setViewMode("detailed")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                viewMode === "detailed"
                  ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                  : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
              }`}
            >
              {t("admin.api.detailed")}
            </button>
          </div>
        </div>

        {!hasTableData && (
          <div className="py-12 text-center">
            <Eye className="w-12 h-12 text-[var(--muted)] mx-auto mb-4 opacity-50" />
            <p className="text-sm text-[var(--muted)]">
              {resolvedEmptyMessage}
            </p>
          </div>
        )}

        {hasTableData && viewMode === "summary" && (
          <Table
            data={filteredMetrics}
            columns={[
              {
                key: entityKey ?? "route",
                header: resolvedEntityLabel,
                render: (item) => (
                  <span
                    className="font-mono"
                    title={String(item[entityKey ?? "route"] ?? "")}
                    style={{
                      display: "block",
                      maxWidth: "12rem",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      textAlign: "center",
                      margin: "0 auto",
                    }}
                  >
                    {String(item[entityKey ?? "route"] ?? "—")}
                  </span>
                ),
                className: "font-mono",
                align: "center",
                sticky: true,
              },
              {
                key: "requestCount",
                header: t("admin.api.colRequests"),
                align: "center",
                render: (item) =>
                  String(item.requestCount ?? item.count ?? "—"),
              },
              {
                key: "avgMs",
                header: t("admin.api.colAvgMs"),
                align: "center",
                render: (item) => {
                  const avgMs = item.avgMs ?? item.avgDurationMs;
                  return avgMs != null ? Math.round(avgMs as number) : "—";
                },
              },
              {
                key: "errors",
                header: t("admin.api.colErrors"),
                align: "center",
                render: (item) => getErrorCount(item),
              },
            ]}
            emptyMessage={resolvedEmptyMessage}
          />
        )}

        {hasTableData && viewMode === "detailed" && (
          <Table
            data={filteredMetrics}
            columns={[
              {
                key: entityKey ?? "route",
                header: resolvedEntityLabel,
                render: (item) => (
                  <span
                    className="font-mono text-xs"
                    title={String(item[entityKey ?? "route"] ?? "")}
                    style={{
                      display: "block",
                      maxWidth: "12rem",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      textAlign: "center",
                      margin: "0 auto",
                    }}
                  >
                    {String(item[entityKey ?? "route"] ?? "—")}
                  </span>
                ),
                className: "font-mono",
                align: "center",
                sticky: true,
              },
              {
                key: "requestCount",
                header: t("admin.api.colRequests"),
                align: "center",
                render: (item) =>
                  String(item.requestCount ?? item.count ?? "—"),
              },
              {
                key: "successRate",
                header: t("admin.api.colSuccessRate"),
                align: "center",
                render: (item) => formatPercent(item.successRate),
              },
              {
                key: "clientErrorRate",
                header: t("admin.api.col4xxErrors"),
                align: "center",
                render: (item) => formatPercent(item.clientErrorRate),
              },
              {
                key: "serverErrorRate",
                header: t("admin.api.col5xxErrors"),
                align: "center",
                render: (item) => formatPercent(item.serverErrorRate),
              },
              {
                key: "timeoutRate",
                header: t("admin.api.colTimeouts"),
                align: "center",
                render: (item) => formatPercent(item.timeoutRate),
              },
              {
                key: "avgMs",
                header: t("admin.api.colAvg"),
                align: "center",
                render: (item) =>
                  formatNumber(item.avgMs ?? item.avgDurationMs),
              },
              {
                key: "p5Ms",
                header: t("admin.api.colP5"),
                align: "center",
                render: (item) => formatNumber(item.p5Ms),
              },
              {
                key: "p95Ms",
                header: t("admin.api.colP95"),
                align: "center",
                render: (item) => formatNumber(item.p95Ms),
              },
              {
                key: "medianMs",
                header: t("admin.api.colMedian"),
                align: "center",
                render: (item) => formatNumber(item.medianMs),
              },
              {
                key: "minMs",
                header: t("admin.api.colMin"),
                align: "center",
                render: (item) => formatNumber(item.minMs),
              },
              {
                key: "maxMs",
                header: t("admin.api.colMax"),
                align: "center",
                render: (item) => formatNumber(item.maxMs),
              },
              {
                key: "stdMs",
                header: t("admin.api.colStd"),
                align: "center",
                render: (item) => formatNumber(item.stdMs),
              },
              {
                key: "avgRequestSizeKb",
                header: t("admin.api.colAvgReqSize"),
                align: "center",
                render: (item) => formatNumber(item.avgRequestSizeKb),
              },
              {
                key: "p95RequestSizeKb",
                header: t("admin.api.colP95ReqSize"),
                align: "center",
                render: (item) => formatNumber(item.p95RequestSizeKb),
              },
              {
                key: "avgResponseSizeKb",
                header: t("admin.api.colAvgRespSize"),
                align: "center",
                render: (item) => formatNumber(item.avgResponseSizeKb),
              },
              {
                key: "p95ResponseSizeKb",
                header: t("admin.api.colP95RespSize"),
                align: "center",
                render: (item) => formatNumber(item.p95ResponseSizeKb),
              },
            ]}
            emptyMessage={resolvedEmptyMessage}
            cellClassName="text-xs"
          />
        )}
      </div>
    </Card>
  );
}
