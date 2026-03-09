"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart3,
  Target,
  AlertTriangle,
  Calendar,
  Clock,
  Activity,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import ScanHistoryBlock from "./ScanHistoryBlock";
import ScheduledScansBlock from "./ScheduledScansBlock";
import AlertHistoryBlock from "./AlertHistoryBlock";
import ScanResults from "./ScanResults";
import ScannerEvolutionChart from "./ScannerEvolutionChart";
import KpiGrid from "../admin/KpiGrid";
import type { KpiItem } from "../admin/KpiGrid";
import type { ScanResult } from "../../services/scanService";

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
      />
    );
  }

  const kpiItems = getFakeKpis(t);

  return (
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
        <ScheduledScansBlock refreshTrigger={scheduleRefreshTrigger} />
      </section>
      <section>
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 min-w-0">
            <ScanHistoryBlock onSelectScan={handleSelectScan} />
          </div>
          <div className="flex-1 min-w-0">
            <AlertHistoryBlock />
          </div>
        </div>
      </section>
    </div>
  );
}
