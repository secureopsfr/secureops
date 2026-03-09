"use client";

import { useState, useEffect, useMemo } from "react";
import useSWR from "swr";
import {
  Eye,
  Users,
  Clock,
  MousePointerClick,
  TrendingUp,
  Globe,
  Monitor,
  Smartphone,
  Tablet,
} from "lucide-react";
import Card from "../ui/cards/Card";
import { DropdownSelector } from "../buttons";
import Table from "../Table";
import KpiGrid from "./KpiGrid";
import BarLineEvolutionChart, {
  BarLineEvolutionChartToggles,
} from "../charts/BarLineEvolutionChart";
import { useLanguage } from "../LanguageProvider";
import {
  WINDOW_OPTIONS,
  autoBucketMinutes,
  getBucketOptions,
} from "./RouteMetrics";
import adminService from "../../services/admin";
import type {
  PageViewsSummaryResponse,
  ReferrerSummary,
  TrafficTimeSeriesPoint,
  DeviceBreakdown,
} from "../../services/admin";
import { error as logError } from "../../utils/logger";
import { formatTimestamp } from "../../utils/dateFormat";
import { AdminInlineLoading } from "./AdminSectionLoading";
import { adminAnalyticsKey, adminTimeSeriesKey } from "../../hooks/swr/keys";

/* ─────────────────────── Types ─────────────────────── */

type TrafficToggle = "views" | "uniqueVisitors";

/* ─────────────────────── Helpers ─────────────────────── */

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

function formatNumber(n: number | null | undefined, locale = "fr-FR"): string {
  if (n == null) return "—";
  return n.toLocaleString(locale);
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function getDeviceIcon(deviceType: string) {
  switch (deviceType.toLowerCase()) {
    case "mobile":
      return <Smartphone className="w-4 h-4" />;
    case "tablet":
      return <Tablet className="w-4 h-4" />;
    case "desktop":
      return <Monitor className="w-4 h-4" />;
    default:
      return <Monitor className="w-4 h-4 opacity-50" />;
  }
}

/* ─────────────────────── Composant ─────────────────────── */

export default function SiteAnalytics() {
  const { t } = useLanguage();
  const [windowMinutes, setWindowMinutes] = useState<number | null>(10080);
  const [bucketMinutes, setBucketMinutes] = useState<number>(
    autoBucketMinutes(10080),
  );
  const effectiveWindowMinutes = windowMinutes ?? 10080;

  useEffect(() => {
    setBucketMinutes(autoBucketMinutes(effectiveWindowMinutes));
  }, [effectiveWindowMinutes]);

  const bucketOptions = useMemo(
    () => getBucketOptions(effectiveWindowMinutes),
    [effectiveWindowMinutes],
  );

  const handleWindowChange = (value: string) => {
    const num = Number(value);
    setWindowMinutes(Number.isNaN(num) ? null : num);
  };

  /* ── état UI ── */
  const [toggles, setToggles] = useState<Set<TrafficToggle>>(
    new Set(["views", "uniqueVisitors"]),
  );

  const showViews = toggles.has("views");
  const showUnique = toggles.has("uniqueVisitors");

  /* ── SWR : données principales (summary, referrers, devices) ── */
  interface AnalyticsBundle {
    summary: PageViewsSummaryResponse | null;
    referrers: ReferrerSummary[];
    devices: DeviceBreakdown[];
    fetchError: string | null;
  }

  const {
    data: analyticsData,
    isLoading: loading,
    mutate: revalidateAnalytics,
  } = useSWR<AnalyticsBundle>(
    adminAnalyticsKey(windowMinutes),
    async () => {
      const params = windowMinutes !== null ? { windowMinutes } : {};
      const [pagesRes, refRes, devRes] = await Promise.all([
        adminService.getPageViewsSummary({ ...params, limit: 50 }),
        adminService.getReferrersSummary({ ...params, limit: 20 }),
        adminService.getDeviceBreakdown(params),
      ]);

      let summary: PageViewsSummaryResponse | null = null;
      let fetchError: string | null = null;
      if (pagesRes.success && pagesRes.data) {
        summary = pagesRes.data;
      } else {
        fetchError = pagesRes.error || "Error loading analytics";
      }

      return {
        summary,
        referrers: refRes.success && refRes.referrers ? refRes.referrers : [],
        devices: devRes.success && devRes.devices ? devRes.devices : [],
        fetchError,
      };
    },
    { dedupingInterval: 30_000 },
  );

  const summary = analyticsData?.summary ?? null;
  const referrers = analyticsData?.referrers ?? [];
  const devices = analyticsData?.devices ?? [];
  const fetchError = analyticsData?.fetchError ?? null;

  /* ── SWR : série temporelle ── */
  interface TimeSeriesBundle {
    points: TrafficTimeSeriesPoint[];
    chartError: string | null;
  }

  const {
    data: tsData,
    isLoading: chartLoading,
    mutate: revalidateTs,
  } = useSWR<TimeSeriesBundle>(
    adminTimeSeriesKey(windowMinutes, bucketMinutes),
    async () => {
      try {
        const res = await adminService.getTrafficTimeseries({
          windowMinutes: effectiveWindowMinutes,
          bucketMinutes,
        });
        if (res.success && Array.isArray(res.points)) {
          return { points: res.points, chartError: null };
        }
        return {
          points: [],
          chartError: res.error || "Error loading chart",
        };
      } catch (err: unknown) {
        logError("[SiteAnalytics] Timeseries error:", err);
        return {
          points: [],
          chartError: err instanceof Error ? err.message : "Connection error",
        };
      }
    },
    { dedupingInterval: 30_000 },
  );

  const trafficPoints = useMemo(() => tsData?.points ?? [], [tsData]);
  const chartError = tsData?.chartError ?? null;

  const loadData = () => revalidateAnalytics();

  /* ── données chart ── */
  const chartData = useMemo(
    () =>
      trafficPoints.map((p) => ({
        ts: formatTimestamp(p.timestamp, effectiveWindowMinutes),
        views: p.views,
        uniqueVisitors: p.uniqueVisitors,
      })),
    [trafficPoints, effectiveWindowMinutes],
  );

  /* ── handlers ── */
  const handleToggle = (metric: TrafficToggle) => {
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

  /* ─────────────────────── état loading / erreur ─────────────────────── */

  if (fetchError && !summary) {
    return (
      <Card disableHover>
        <div className="py-12 text-center">
          <p className="text-[rgb(var(--danger))] mb-4">{fetchError}</p>
          <button
            onClick={loadData}
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
    <div className="space-y-6">
      {/* ═══════════ En-tête ═══════════ */}
      <Card disableHover style={{ overflow: "visible" }}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-[var(--text)]">
              {t("admin.analytics.title")}
            </h2>
            <p className="text-[var(--muted)] mt-1">
              {t("admin.analytics.description")}
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[var(--muted)]">
                {t("admin.common.window")} :
              </span>
              <DropdownSelector
                selectedValue={String(effectiveWindowMinutes)}
                onChange={handleWindowChange}
                options={WINDOW_OPTIONS}
                width="10rem"
              />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[var(--muted)]">
                {t("admin.common.step")} :
              </span>
              <DropdownSelector
                selectedValue={String(bucketMinutes)}
                onChange={(v) => setBucketMinutes(Number(v))}
                options={bucketOptions}
                width="11rem"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* ═══════════ KPI Cards ═══════════ */}
      {loading && !summary ? (
        <AdminInlineLoading message={t("admin.analytics.loadingAnalytics")} />
      ) : (
        <>
          <KpiGrid
            columns={5}
            items={[
              {
                label: t("admin.analytics.views"),
                value: formatNumber(summary?.totalViews, t("locale")),
                icon: <Eye className="w-4 h-4 text-[rgb(var(--primary))]" />,
                bgColor: "rgba(var(--primary),0.15)",
              },
              {
                label: t("admin.analytics.visitors"),
                value: formatNumber(summary?.totalUniqueVisitors, t("locale")),
                icon: <Users className="w-4 h-4 text-[rgb(96,165,250)]" />,
                bgColor: "rgba(96,165,250,0.15)",
              },
              {
                label: t("admin.analytics.pagesPerSession"),
                value:
                  summary?.avgPagesPerSession != null
                    ? summary.avgPagesPerSession.toFixed(1)
                    : "—",
                icon: (
                  <MousePointerClick className="w-4 h-4 text-[rgb(52,211,153)]" />
                ),
                bgColor: "rgba(52,211,153,0.15)",
              },
              {
                label: t("admin.analytics.avgDuration"),
                value: formatDuration(summary?.avgSessionDurationMs),
                icon: <Clock className="w-4 h-4 text-[rgb(var(--warning))]" />,
                bgColor: "rgba(var(--warning),0.15)",
              },
              {
                label: t("admin.analytics.bounce"),
                value: formatPercent(summary?.bounceRate),
                icon: (
                  <TrendingUp className="w-4 h-4 text-[rgb(var(--danger))]" />
                ),
                bgColor: "rgba(var(--danger),0.15)",
              },
            ]}
          />

          {/* ═══════════ Graphique d'évolution du trafic ═══════════ */}
          <Card
            disableHover
            className="no-hover"
            style={{ overflow: "visible" }}
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[rgb(var(--primary))]" />
                <h3
                  className="text-base font-semibold text-[var(--text)]"
                  style={{ margin: 0 }}
                >
                  {t("admin.analytics.trafficEvolution")}
                </h3>
              </div>

              <BarLineEvolutionChartToggles
                toggleOptions={[
                  {
                    key: "views",
                    label: t("admin.analytics.pageViewsToggle"),
                  },
                  {
                    key: "uniqueVisitors",
                    label: t("admin.analytics.uniqueVisitorsToggle"),
                    activeColor: "blue",
                  },
                ]}
                activeKeys={toggles}
                onToggle={(k) => handleToggle(k as TrafficToggle)}
              />
            </div>

            {chartLoading && trafficPoints.length === 0 && (
              <AdminInlineLoading message={t("admin.analytics.loadingChart")} />
            )}

            {chartError && trafficPoints.length === 0 && (
              <div className="py-8 text-center">
                <p className="text-[rgb(var(--danger))] mb-4">{chartError}</p>
                <button
                  onClick={() => revalidateTs()}
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
                  {t("admin.analytics.noTrafficData")}
                </p>
              </div>
            )}

            {chartData.length > 0 && (
              <BarLineEvolutionChart
                data={chartData}
                xAxisKey="ts"
                height={320}
                barSeries={{
                  dataKey: "views",
                  name: t("admin.analytics.chartPageViews"),
                  yAxisId: "left",
                  fill: "rgba(var(--primary), 0.6)",
                  maxBarSize: 32,
                }}
                showBar={showViews}
                curveSeries={{
                  type: "line",
                  dataKey: "uniqueVisitors",
                  name: t("admin.analytics.chartVisitors"),
                }}
                showCurve={showUnique}
                showDotsThreshold={60}
              />
            )}
          </Card>

          {/* ═══════════ Tableaux côte à côte : Pages + Referrers ═══════════ */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tableau des pages les plus vues */}
            <Card disableHover style={{ overflow: "visible" }}>
              <div className="flex items-center gap-2 mb-4">
                <Eye className="w-4 h-4 text-[rgb(var(--primary))]" />
                <h3
                  className="text-base font-semibold text-[var(--text)]"
                  style={{ margin: 0 }}
                >
                  {t("admin.analytics.mostViewedPages")}
                </h3>
              </div>

              {summary?.pages && summary.pages.length > 0 ? (
                <Table
                  data={summary.pages as unknown as Record<string, unknown>[]}
                  columns={[
                    {
                      key: "page",
                      header: t("admin.analytics.colPage"),
                      render: (item) => (
                        <span
                          className="font-mono text-xs"
                          title={String(item.page ?? "")}
                          style={{
                            display: "block",
                            maxWidth: "14rem",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            textAlign: "center",
                            margin: "0 auto",
                          }}
                        >
                          {String(item.page ?? "—")}
                        </span>
                      ),
                      align: "center",
                      sticky: true,
                    },
                    {
                      key: "views",
                      header: t("admin.analytics.colViews"),
                      align: "center",
                      render: (item) =>
                        formatNumber(item.views as number, t("locale")),
                    },
                    {
                      key: "uniqueVisitors",
                      header: t("admin.analytics.colUnique"),
                      align: "center",
                      render: (item) =>
                        formatNumber(
                          item.uniqueVisitors as number,
                          t("locale"),
                        ),
                    },
                    {
                      key: "avgDurationMs",
                      header: t("admin.analytics.colAvgDuration"),
                      align: "center",
                      render: (item) =>
                        formatDuration(item.avgDurationMs as number | null),
                    },
                  ]}
                  emptyMessage={t("admin.analytics.noPageData")}
                  cellClassName="text-xs"
                />
              ) : (
                <div className="py-8 text-center">
                  <p className="text-sm text-[var(--muted)]">
                    {t("admin.analytics.noPageViews")}
                  </p>
                </div>
              )}
            </Card>

            {/* Tableau des referrers */}
            <Card disableHover style={{ overflow: "visible" }}>
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-4 h-4 text-[rgb(var(--primary))]" />
                <h3
                  className="text-base font-semibold text-[var(--text)]"
                  style={{ margin: 0 }}
                >
                  {t("admin.analytics.trafficSources")}
                </h3>
              </div>

              {referrers.length > 0 ? (
                <Table
                  data={referrers as unknown as Record<string, unknown>[]}
                  columns={[
                    {
                      key: "referrer",
                      header: t("admin.analytics.colSource"),
                      render: (item) => (
                        <span
                          className="font-mono text-xs"
                          title={String(item.referrer ?? "")}
                          style={{
                            display: "block",
                            maxWidth: "14rem",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            textAlign: "center",
                            margin: "0 auto",
                          }}
                        >
                          {item.referrer === "direct"
                            ? t("admin.analytics.directAccess")
                            : String(item.referrer ?? "—")}
                        </span>
                      ),
                      align: "center",
                      sticky: true,
                    },
                    {
                      key: "count",
                      header: t("admin.analytics.colVisits"),
                      align: "center",
                      render: (item) =>
                        formatNumber(item.count as number, t("locale")),
                    },
                    {
                      key: "uniqueVisitors",
                      header: t("admin.analytics.colUnique"),
                      align: "center",
                      render: (item) =>
                        formatNumber(
                          item.uniqueVisitors as number,
                          t("locale"),
                        ),
                    },
                  ]}
                  emptyMessage={t("admin.analytics.noTrafficSources")}
                  cellClassName="text-xs"
                />
              ) : (
                <div className="py-8 text-center">
                  <p className="text-sm text-[var(--muted)]">
                    {t("admin.analytics.noTrafficSources")}
                  </p>
                </div>
              )}
            </Card>
          </div>

          {/* ═══════════ Répartition par appareil ═══════════ */}
          <Card disableHover>
            <div className="flex items-center gap-2 mb-4">
              <Monitor className="w-4 h-4 text-[rgb(var(--primary))]" />
              <h3
                className="text-base font-semibold text-[var(--text)]"
                style={{ margin: 0 }}
              >
                {t("admin.analytics.deviceBreakdown")}
              </h3>
            </div>

            {devices.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {devices.map((device) => (
                  <div
                    key={device.deviceType}
                    className="flex items-center gap-4 p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)]"
                  >
                    <div className="p-2 rounded-lg bg-[rgba(var(--primary),0.1)] text-[rgb(var(--primary))]">
                      {getDeviceIcon(device.deviceType)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--text)] capitalize">
                        {device.deviceType}
                      </p>
                      <p className="text-xs text-[var(--muted)]">
                        {formatNumber(device.count, t("locale"))}{" "}
                        {t("admin.analytics.sessions")}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-[var(--text)]">
                        {device.percentage.toFixed(1)}%
                      </p>
                    </div>
                    {/* Barre de progression */}
                    <div
                      className="absolute bottom-0 left-0 right-0 h-1 rounded-b-lg overflow-hidden"
                      style={{ position: "relative" }}
                    >
                      <div
                        className="h-full rounded-full bg-[rgb(var(--primary))]"
                        style={{
                          width: `${device.percentage}%`,
                          opacity: 0.6,
                          transition: "width 0.5s ease",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-[var(--muted)]">
                  {t("admin.analytics.noDeviceData")}
                </p>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
