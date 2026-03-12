"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Gauge,
  AlertTriangle,
  Calendar,
  Clock,
  Activity,
  Filter,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import ScannerHistoryAlertsSection from "./ScannerHistoryAlertsSection";
import MultiScanResults from "./MultiScanResults";
import ScanResults from "./ScanResults";
import ScannerEvolutionChart from "./ScannerEvolutionChart";
import KpiGrid from "../admin/KpiGrid";
import type { KpiItem } from "../admin/KpiGrid";
import type { MultiScanResult, ScanResult } from "../../services/scanService";
import Drawer from "../ui/Drawer";
import { GenericButton } from "../buttons";
import { getScanHistory } from "../../services/scanHistoryService";
import type { ScanHistorySelection } from "../../services/scanHistoryService";
import userService from "../../services/userService";
import { formatUrlDisplay } from "../../utils/urlFormat";
import { getDateRangeFromDays } from "../../utils/apiQueryParams";
import { useScanOverview } from "../../hooks/swr/useScanOverview";
import { getTimeAgo } from "../../utils/dateFormat";
import type { ScanOverviewResponse } from "../../services/scanHistoryService";
import AnimateInView from "../AnimateInView";

function buildKpiItems(
  t: (key: string, params?: Record<string, string | number>) => string,
  kpis: ScanOverviewResponse["kpis"] | undefined,
): KpiItem[] {
  const totalScans = kpis?.total_scans ?? "—";
  const avgScore = kpis?.avg_score != null ? `${kpis.avg_score}/100` : "—";
  const criticalCount = kpis?.critical_findings_count ?? "—";
  const activeScheduled = kpis?.active_scheduled_count ?? "—";

  let lastScanValue: string;
  if (kpis?.last_scan_at) {
    const ago = getTimeAgo(kpis.last_scan_at);
    if (ago) {
      const key =
        ago.unit === "minutes"
          ? "scanner.gestion.kpiLastScanAgoMinutes"
          : ago.unit === "hours"
            ? "scanner.gestion.kpiLastScanAgoHours"
            : "scanner.gestion.kpiLastScanAgoDays";
      lastScanValue = t(key, { value: ago.value });
    } else {
      lastScanValue = t("scanner.gestion.kpiLastScanNever");
    }
  } else {
    lastScanValue = t("scanner.gestion.kpiLastScanNever");
  }

  return [
    {
      label: t("scanner.gestion.kpiTotalScans"),
      value: String(totalScans),
      icon: <Activity className="w-4 h-4 text-[rgb(249,115,22)]" />,
      bgColor: "rgba(249,115,22,0.15)",
    },
    {
      label: t("scanner.gestion.kpiAverageScore"),
      value: avgScore,
      icon: <Gauge className="w-4 h-4 text-[rgb(52,211,153)]" />,
      bgColor: "rgba(52,211,153,0.15)",
    },
    {
      label: t("scanner.gestion.kpiCriticalAnomalies"),
      value: String(criticalCount),
      icon: <AlertTriangle className="w-4 h-4 text-[rgb(var(--danger))]" />,
      bgColor: "rgba(var(--danger),0.15)",
    },
    {
      label: t("scanner.gestion.kpiActiveScheduled"),
      value: String(activeScheduled),
      icon: <Calendar className="w-4 h-4 text-[rgb(var(--warning))]" />,
      bgColor: "rgba(var(--warning),0.15)",
    },
    {
      label: t("scanner.gestion.kpiLastScan"),
      value: lastScanValue,
      icon: <Clock className="w-4 h-4 text-[rgb(168,85,247)]" />,
      bgColor: "rgba(168,85,247,0.15)",
    },
  ];
}

export default function ScannerGestion() {
  const { t, lp } = useLanguage();
  const router = useRouter();
  const [selectedResult, setSelectedResult] = useState<ScanResult | null>(null);
  const [selectedMultiResult, setSelectedMultiResult] =
    useState<MultiScanResult | null>(null);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const [scheduleRefreshTrigger] = useState(0);
  const [filterUrl, setFilterUrl] = useState<string | null>(null);
  const [filterScanType, setFilterScanType] = useState<string | null>(null);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [urlOptions, setUrlOptions] = useState<string[]>([]);
  const [urlListExpanded, setUrlListExpanded] = useState(false);
  const [filterDateRange, setFilterDateRange] = useState<number | null>(null);
  const [historyRetentionDays, setHistoryRetentionDays] = useState<
    number | null
  >(null);

  const URL_DISPLAY_LIMIT = 5;
  const displayedUrls = urlListExpanded
    ? urlOptions
    : urlOptions.slice(0, URL_DISPLAY_LIMIT);
  const hasMoreUrls = urlOptions.length > URL_DISPLAY_LIMIT;
  const hiddenCount = urlOptions.length - URL_DISPLAY_LIMIT;

  useEffect(() => {
    getScanHistory(1, 100)
      .then((res) => {
        const urls = [...new Set(res.items.map((i) => i.url))];
        setUrlOptions(urls);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    userService.getSubscription().then((res) => {
      const raw = res.subscription?.history_retention;
      const retention = typeof raw === "string" ? raw : "30";
      const days = retention === "none" ? null : parseInt(retention, 10);
      setHistoryRetentionDays(Number.isNaN(days) ? null : days);
      setFilterDateRange((prev) =>
        prev === null && days != null ? days : prev,
      );
    });
  }, []);

  const timeWindowOptions =
    historyRetentionDays == null
      ? []
      : [7, 30, 90, 365].filter((d) => d <= historyRetentionDays);

  useEffect(() => {
    if (
      historyRetentionDays != null &&
      filterDateRange != null &&
      filterDateRange > historyRetentionDays
    ) {
      setFilterDateRange(historyRetentionDays);
    }
  }, [historyRetentionDays, filterDateRange]);

  const { date_from: filterDateFrom, date_to: filterDateTo } = useMemo(() => {
    if (filterDateRange == null)
      return {
        date_from: null as string | null,
        date_to: null as string | null,
      };
    return getDateRangeFromDays(filterDateRange);
  }, [filterDateRange]);

  const { overview, isLoading: overviewLoading } = useScanOverview(
    filterUrl,
    filterScanType,
    filterDateFrom,
    filterDateTo,
  );

  const handleSelectFilter = useCallback(
    (url: string | null, scanType: string | null) => {
      setFilterUrl(url);
      setFilterScanType(scanType);
      setFilterDrawerOpen(false);
    },
    [],
  );

  const handleSelectDateRange = useCallback((days: number | null) => {
    setFilterDateRange(days);
    setFilterDrawerOpen(false);
  }, []);

  const handleSelectScan = (selection: ScanHistorySelection) => {
    setSelectedScanId(selection.scan_id ?? null);
    if (selection.result_mode === "multi") {
      setSelectedMultiResult(selection.result);
      setSelectedResult(null);
      return;
    }
    setSelectedResult(selection.result);
    setSelectedMultiResult(null);
  };

  const handleNewScan = () => {
    setSelectedResult(null);
    setSelectedMultiResult(null);
    setSelectedScanId(null);
    router.push(lp("/scanner/analyses"));
  };

  if (selectedMultiResult) {
    return (
      <MultiScanResults
        result={selectedMultiResult}
        onNewScan={handleNewScan}
      />
    );
  }

  if (selectedResult) {
    return (
      <ScanResults
        result={selectedResult}
        scanId={selectedScanId}
        onNewScan={handleNewScan}
      />
    );
  }

  const kpiItems = buildKpiItems(t, overview?.kpis);

  return (
    <>
      <AnimateInView
        initialOnly
        delay={80}
        className="page-section landing-reveal-page"
        as="section"
        aria-label={t("scanner.ariaHeader")}
      >
        <div className="page-container">
          <div className="page-header text-center mb-4">
            <h1 className="page-title mb-2">
              {t("scanner.gestion.pageTitle")}
            </h1>
            <p className="page-subtitle mt-0 max-w-2xl mx-auto">
              {t("scanner.gestion.pageSubtitle")}
            </p>
            <div className="flex justify-center mt-3">
              <GenericButton
                variant="outline"
                label={t("scanner.gestion.filterButton")}
                icon={<Filter className="w-4 h-4" />}
                iconPosition="left"
                onClick={() => setFilterDrawerOpen(true)}
              />
            </div>
          </div>
        </div>
      </AnimateInView>

      <Drawer
        isOpen={filterDrawerOpen}
        onClose={() => setFilterDrawerOpen(false)}
        title={t("scanner.gestion.filterDrawerTitle")}
      >
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-[var(--text)] mb-2">
              {t("scanner.gestion.filterByUrl")}
            </h3>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleSelectFilter(null, filterScanType)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  filterUrl === null
                    ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                    : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                }`}
              >
                {t("scanner.gestion.filterAllScans")}
              </button>
              {displayedUrls.map((u) => (
                <button
                  key={u}
                  type="button"
                  onClick={() => handleSelectFilter(u, filterScanType)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors truncate ${
                    filterUrl === u
                      ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                      : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                  }`}
                  title={u}
                >
                  {formatUrlDisplay(u)}
                </button>
              ))}
              {hasMoreUrls && (
                <button
                  type="button"
                  onClick={() => setUrlListExpanded(!urlListExpanded)}
                  className="w-full text-left px-4 py-2 text-sm text-[rgb(var(--primary))] hover:bg-[rgba(var(--primary),0.08)] rounded-lg transition-colors"
                >
                  {urlListExpanded
                    ? t("scanner.gestion.filterUrlShowLess")
                    : t("scanner.gestion.filterUrlShowMore", {
                        count: hiddenCount,
                      })}
                </button>
              )}
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[var(--text)] mb-2">
              {t("scanner.gestion.filterByScanType")}
            </h3>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleSelectFilter(filterUrl, null)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  filterScanType === null
                    ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                    : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                }`}
              >
                {t("scanner.gestion.filterScanTypeAll")}
              </button>
              <button
                type="button"
                onClick={() => handleSelectFilter(filterUrl, "frontend")}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  filterScanType === "frontend"
                    ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                    : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                }`}
              >
                {t("scanner.scanTypeFrontend")}
              </button>
              <button
                type="button"
                onClick={() => handleSelectFilter(filterUrl, "backend")}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  filterScanType === "backend"
                    ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                    : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                }`}
              >
                {t("scanner.scanTypeBackend")}
              </button>
              <button
                type="button"
                onClick={() => handleSelectFilter(filterUrl, "custom")}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  filterScanType === "custom"
                    ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                    : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                }`}
              >
                {t("scanner.scanTypeCustom")}
              </button>
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[var(--text)] mb-1">
              {t("scanner.gestion.filterByTimeWindow")}
            </h3>
            <p className="text-xs text-[var(--muted)] mb-2">
              {t("scanner.gestion.filterTimeWindowAlertExclude")}
            </p>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleSelectDateRange(null)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  filterDateRange === null
                    ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                    : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                }`}
              >
                {t("scanner.gestion.filterTimeWindowAll")}
              </button>
              {timeWindowOptions.map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => handleSelectDateRange(days)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                    filterDateRange === days
                      ? "bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] font-medium"
                      : "hover:bg-[var(--color-surface-hover)] text-[var(--text)]"
                  }`}
                >
                  {t("scanner.gestion.filterTimeWindowDays", { days })}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Drawer>

      <div className="[&>section+section]:-mt-3">
        <section>
          <div className="mb-4">
            <KpiGrid items={kpiItems} columns={5} />
          </div>
          <ScannerEvolutionChart
            data={
              overview?.chart_data ??
              (
                overview as
                  | { chartData?: ScanOverviewResponse["chart_data"] }
                  | undefined
              )?.chartData ??
              []
            }
            isLoading={!overview && overviewLoading}
          />
        </section>
        <section>
          <ScannerHistoryAlertsSection
            onSelectScan={handleSelectScan}
            scheduleRefreshTrigger={scheduleRefreshTrigger}
            filterUrl={filterUrl}
            filterScanType={filterScanType}
            filterDateFrom={filterDateFrom ?? undefined}
            filterDateTo={filterDateTo ?? undefined}
          />
        </section>
      </div>
    </>
  );
}
