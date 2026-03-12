"use client";

import { useState } from "react";
import { TrendingUp } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import Card from "../ui/cards/Card";
import BarLineEvolutionChart, {
  BarLineEvolutionChartToggles,
} from "../charts/BarLineEvolutionChart";
import { AdminInlineLoading } from "../admin/AdminSectionLoading";

export interface ScannerEvolutionChartProps {
  data?: Array<{ ts: string; scans: number; score: number; anomalies: number }>;
  isLoading?: boolean;
}

export default function ScannerEvolutionChart({
  data = [],
  isLoading = false,
}: ScannerEvolutionChartProps) {
  const { t } = useLanguage();
  const [curveMode, setCurveMode] = useState<"score" | "anomalies">("score");

  const curveConfig =
    curveMode === "score"
      ? {
          dataKey: "score" as const,
          name: t("scanner.evolution.chartScore"),
          domain: [0, 100] as [number, number],
        }
      : {
          dataKey: "anomalies" as const,
          name: t("scanner.evolution.chartAnomalies"),
          domain: [0, "auto"] as [number, "auto"],
        };

  return (
    <Card disableHover className="no-hover" style={{ overflow: "visible" }}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-6 h-6 text-[rgb(var(--primary))]" />
          <h2 className="text-xl font-bold text-[var(--text)]">
            {t("scanner.gestion.tabEvolution")}
          </h2>
        </div>
        {data.length > 0 && (
          <BarLineEvolutionChartToggles
            toggleOptions={[
              {
                key: "score",
                label: t("scanner.evolution.curveViewScore"),
              },
              {
                key: "anomalies",
                label: t("scanner.evolution.curveViewAnomalies"),
                activeColor: "blue",
              },
            ]}
            activeKeys={new Set([curveMode])}
            onToggle={(k) => setCurveMode(k as "score" | "anomalies")}
          />
        )}
      </div>
      {isLoading && (
        <AdminInlineLoading message={t("admin.analytics.loadingChart")} />
      )}
      {!isLoading && data.length === 0 && (
        <div className="py-8 text-center">
          <TrendingUp className="w-10 h-10 text-[var(--muted)] mx-auto mb-3 opacity-50" />
          <p className="text-sm text-[var(--muted)]">
            {t("scanner.evolution.noData")}
          </p>
        </div>
      )}
      {!isLoading && data.length > 0 && (
        <BarLineEvolutionChart
          data={data}
          xAxisKey="ts"
          height={320}
          barSeries={{
            dataKey: "scans",
            name: t("scanner.evolution.chartScans"),
            yAxisId: "left",
            fill: "rgba(var(--primary), 0.6)",
            maxBarSize: 32,
          }}
          showBar={true}
          curveSeries={{
            type: "line",
            dataKey: curveConfig.dataKey,
            name: curveConfig.name,
            yAxisId: "right",
            domain: curveConfig.domain,
            stroke: "rgb(96, 165, 250)",
          }}
          showCurve={true}
          showDotsThreshold={60}
        />
      )}
    </Card>
  );
}
