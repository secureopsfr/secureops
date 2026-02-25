"use client";

import { useEffect, useState, useMemo } from "react";
import useSWR from "swr";
import { Clock, CheckCircle, AlertTriangle, Zap, Activity } from "lucide-react";
import Card from "../cards/Card";
import { DropdownSelector } from "../buttons";
import RouteMetrics, {
  WINDOW_OPTIONS,
  autoBucketMinutes,
  getBucketOptions,
} from "./RouteMetrics";
import KpiGrid from "./KpiGrid";
import adminService from "../../services/admin";
import { error } from "../../utils/logger";
import { computeApiKpis } from "../../utils/metricsHelpers";
import { adminPerfMetricsKey } from "../../hooks/swr/keys";
import { useLanguage } from "../LanguageProvider";

/* ─────────────────────── Composant ─────────────────────── */

export default function ApiMetrics() {
  const { t, language } = useLanguage();
  const loc = language === "en" ? "en-US" : "fr-FR";
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

  /* ── SWR : métriques de performance ── */
  interface MetricsBundle {
    perfMetrics: Record<string, unknown>[];
    serviceMetrics: Record<string, unknown>[];
  }

  const { data: metricsData } = useSWR<MetricsBundle>(
    adminPerfMetricsKey(windowMinutes),
    async () => {
      let perf: Record<string, unknown>[] = [];
      let service: Record<string, unknown>[] = [];

      try {
        if (typeof adminService.getPerformance === "function") {
          const params =
            windowMinutes !== null && windowMinutes !== undefined
              ? { windowMinutes, limit: 50 }
              : { limit: 50 };
          const res = await adminService.getPerformance(params);
          if (res?.success && Array.isArray(res.metrics)) {
            perf = res.metrics as Record<string, unknown>[];
          }
        }

        if (typeof adminService.getServicePerformance === "function") {
          const serviceParams =
            windowMinutes !== null && windowMinutes !== undefined
              ? { windowMinutes, limit: 50 }
              : { limit: 50 };
          const serviceRes =
            await adminService.getServicePerformance(serviceParams);
          if (serviceRes?.success && Array.isArray(serviceRes.metrics)) {
            service = serviceRes.metrics as Record<string, unknown>[];
          }
        }
      } catch (e) {
        error("Erreur lors du chargement des métriques:", e);
      }

      return { perfMetrics: perf, serviceMetrics: service };
    },
    { dedupingInterval: 30_000 },
  );

  const perfMetrics = useMemo(
    () => metricsData?.perfMetrics ?? [],
    [metricsData],
  );
  const serviceMetrics = metricsData?.serviceMetrics ?? [];

  const apiKpis = useMemo(() => computeApiKpis(perfMetrics), [perfMetrics]);

  return (
    <div className="space-y-6">
      <Card disableHover style={{ overflow: "visible" }}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-[var(--text)]">
              {t("admin.api.title")}
            </h2>
            <p className="text-[var(--muted)] mt-1">
              {t("admin.api.description")}
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

      {apiKpis && (
        <KpiGrid
          columns={5}
          items={[
            {
              label: t("admin.api.requests"),
              value: apiKpis.totalRequests.toLocaleString(loc),
              icon: <Activity className="w-4 h-4 text-[rgb(var(--primary))]" />,
              bgColor: "rgba(var(--primary),0.15)",
            },
            {
              label: t("admin.api.avgTime"),
              value:
                apiKpis.avgMs != null ? `${Math.round(apiKpis.avgMs)} ms` : "—",
              icon: <Clock className="w-4 h-4 text-[rgb(var(--warning))]" />,
              bgColor: "rgba(var(--warning),0.15)",
            },
            {
              label: t("admin.api.success"),
              value:
                apiKpis.successRate != null
                  ? `${(apiKpis.successRate * 100).toFixed(1)}%`
                  : "—",
              icon: <CheckCircle className="w-4 h-4 text-[rgb(52,211,153)]" />,
              bgColor: "rgba(52,211,153,0.15)",
            },
            {
              label: t("admin.api.errors"),
              value: apiKpis.totalErrors.toLocaleString(loc),
              icon: (
                <AlertTriangle className="w-4 h-4 text-[rgb(var(--danger))]" />
              ),
              bgColor: "rgba(var(--danger),0.15)",
            },
            {
              label: t("admin.api.p95Max"),
              value:
                apiKpis.maxP95 != null
                  ? `${Math.round(apiKpis.maxP95)} ms`
                  : "—",
              icon: <Zap className="w-4 h-4 text-[rgb(96,165,250)]" />,
              bgColor: "rgba(96,165,250,0.15)",
            },
          ]}
        />
      )}

      <RouteMetrics
        metrics={serviceMetrics}
        windowMinutes={windowMinutes}
        bucketMinutes={bucketMinutes}
        title={t("admin.api.serviceMetrics")}
        entityLabel={t("admin.api.serviceLabel")}
        entityKey="servicePrefix"
        emptyMessage={t("admin.api.noServiceData")}
      />
      <RouteMetrics
        metrics={perfMetrics}
        windowMinutes={windowMinutes}
        bucketMinutes={bucketMinutes}
        title={t("admin.api.routeMetrics")}
      />
    </div>
  );
}
