"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart3,
  Target,
  AlertTriangle,
  Calendar,
  Clock,
  Activity,
  Filter,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import ScannerHistoryAlertsSection from "./ScannerHistoryAlertsSection";
import ScanResults from "./ScanResults";
import ScannerEvolutionChart from "./ScannerEvolutionChart";
import KpiGrid from "../admin/KpiGrid";
import type { KpiItem } from "../admin/KpiGrid";
import type { ScanResult } from "../../services/scanService";
import Drawer from "../ui/Drawer";
import { GenericButton } from "../buttons";
import { getScanHistory } from "../../services/scanHistoryService";
import userService from "../../services/userService";
import { formatUrlDisplay } from "../../utils/urlFormat";
import { getDateRangeFromDays } from "../../utils/apiQueryParams";

/** KPIs fictifs pour le tableau de bord — à remplacer par des données réelles. */
function getFakeKpis(t: (key: string) => string): KpiItem[] {
  return [
    {
      label: t("scanner.gestion.kpiScansThisMonth"),
      value: "12",
      icon: <BarChart3 className="w-4 h-4 text-[rgb(var(--primary))]" />,
      bgColor: "rgba(var(--primary),0.15)",
    },
    {
      label: t("scanner.gestion.kpiTotalScans"),
      value: "156",
      icon: <Activity className="w-4 h-4 text-[rgb(96,165,250)]" />,
      bgColor: "rgba(96,165,250,0.15)",
    },
    {
      label: t("scanner.gestion.kpiAverageScore"),
      value: "78/100",
      icon: <Target className="w-4 h-4 text-[rgb(52,211,153)]" />,
      bgColor: "rgba(52,211,153,0.15)",
    },
    {
      label: t("scanner.gestion.kpiCriticalAnomalies"),
      value: "3",
      icon: <AlertTriangle className="w-4 h-4 text-[rgb(var(--danger))]" />,
      bgColor: "rgba(var(--danger),0.15)",
    },
    {
      label: t("scanner.gestion.kpiActiveScheduled"),
      value: "2",
      icon: <Calendar className="w-4 h-4 text-[rgb(var(--warning))]" />,
      bgColor: "rgba(var(--warning),0.15)",
    },
    {
      label: t("scanner.gestion.kpiLastScan"),
      value: t("scanner.gestion.kpiLastScanValue"),
      icon: <Clock className="w-4 h-4 text-[rgb(168,85,247)]" />,
      bgColor: "rgba(168,85,247,0.15)",
    },
  ];
}

export default function ScannerGestion() {
  const { t, lp } = useLanguage();
  const router = useRouter();
  const [selectedResult, setSelectedResult] = useState<ScanResult | null>(null);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const [scheduleRefreshTrigger, setScheduleRefreshTrigger] = useState(0);
  const [filterUrl, setFilterUrl] = useState<string | null>(null);
  const [filterScanType, setFilterScanType] = useState<string | null>(null);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [urlOptions, setUrlOptions] = useState<string[]>([]);
  const [urlListExpanded, setUrlListExpanded] = useState(false);
  const [filterDateRange, setFilterDateRange] = useState<number | null>(null);

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
      if (filterDateRange === null && retention !== "none") {
        const days = parseInt(retention, 10);
        if (!Number.isNaN(days)) setFilterDateRange(days);
      }
    });
  }, []);

  const { date_from: filterDateFrom, date_to: filterDateTo } =
    filterDateRange != null
      ? getDateRangeFromDays(filterDateRange)
      : { date_from: null, date_to: null };

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

  const handleSelectScan = (result: ScanResult, id?: string) => {
    setSelectedResult(result);
    setSelectedScanId(id ?? null);
  };

  const handleNewScan = () => {
    setSelectedResult(null);
    setSelectedScanId(null);
    router.push(lp("/scanner/analyses"));
  };

  if (selectedResult) {
    return (
      <ScanResults
        result={selectedResult}
        scanId={selectedScanId}
        onNewScan={handleNewScan}
        onSelectScan={handleSelectScan}
      />
    );
  }

  const kpiItems = getFakeKpis(t);

  return (
    <>
      <div className="text-center mb-6">
        <h1 className="page-title mb-2">{t("scanner.gestion.pageTitle")}</h1>
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
              {([7, 30, 90, 365] as const).map((days) => (
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
            <KpiGrid items={kpiItems} columns={6} />
            <p className="text-xs text-[var(--muted)] mt-2">
              {t("scanner.gestion.kpiFakeData")}
            </p>
          </div>
          <ScannerEvolutionChart />
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
