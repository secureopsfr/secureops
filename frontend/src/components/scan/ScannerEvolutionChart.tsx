"use client";

import { TrendingUp } from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import Card from "../ui/cards/Card";
import { useLanguage } from "../LanguageProvider";

/** Données fictives pour l'évolution du score — à remplacer par les vraies données plus tard. */
const FAKE_EVOLUTION_DATA = [
  { ts: "03/03", score: 62, anomalies: 8 },
  { ts: "04/03", score: 68, anomalies: 6 },
  { ts: "05/03", score: 71, anomalies: 5 },
  { ts: "06/03", score: 65, anomalies: 7 },
  { ts: "07/03", score: 78, anomalies: 4 },
  { ts: "08/03", score: 82, anomalies: 3 },
  { ts: "09/03", score: 85, anomalies: 2 },
];

export default function ScannerEvolutionChart() {
  const { t } = useLanguage();

  return (
    <Card disableHover className="no-hover" style={{ overflow: "visible" }}>
      <div className="flex items-center gap-3 mb-4">
        <TrendingUp className="w-6 h-6 text-[rgb(var(--primary))]" />
        <h2 className="text-xl font-bold text-[var(--text)]">
          {t("scanner.gestion.tabEvolution")}
        </h2>
      </div>
      <div style={{ width: "100%", height: 240 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={FAKE_EVOLUTION_DATA}
            margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
              opacity={0.5}
            />
            <XAxis
              dataKey="ts"
              tick={{ fontSize: 11, fill: "var(--muted)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              interval="preserveStartEnd"
              minTickGap={40}
            />
            <YAxis
              yAxisId="left"
              orientation="left"
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: "var(--muted)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              label={{
                value: t("scanner.evolution.chartScore"),
                angle: -90,
                position: "insideLeft",
                offset: 10,
                style: { fontSize: 11, fill: "var(--muted)" },
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: "var(--muted)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              label={{
                value: t("scanner.evolution.chartAnomalies"),
                angle: 90,
                position: "insideRight",
                offset: 10,
                style: { fontSize: 11, fill: "var(--muted)" },
              }}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                background: "var(--color-overlay-panel-solid)",
                border: "1px solid var(--border)",
                borderRadius: "0.5rem",
                fontSize: "0.8rem",
                color: "var(--text)",
              }}
              labelStyle={{ color: "var(--muted)", marginBottom: 4 }}
            />
            <Legend
              wrapperStyle={{
                fontSize: "0.75rem",
                color: "var(--muted)",
              }}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="score"
              name={t("scanner.evolution.chartScore")}
              fill="rgba(var(--primary), 0.2)"
              stroke="rgb(var(--primary))"
              strokeWidth={2}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="anomalies"
              name={t("scanner.evolution.chartAnomalies")}
              stroke="rgb(96, 165, 250)"
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 4 }}
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
