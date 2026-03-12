"use client";

import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const TOOLTIP_STYLE = {
  contentStyle: {
    background: "var(--color-overlay-panel-solid)",
    border: "1px solid var(--border)",
    borderRadius: "0.5rem",
    fontSize: "0.8rem",
    color: "var(--text)",
  },
  labelStyle: { color: "var(--muted)", marginBottom: 4 },
} as const;

const AXIS_TICK = { fontSize: 11, fill: "var(--muted)" };
const AXIS_LABEL_STYLE = { fontSize: 11, fill: "var(--muted)" };

export interface ToggleOption {
  key: string;
  label: string;
  /** Couleur du toggle actif : "primary" (défaut) ou "blue" pour la 2e série */
  activeColor?: "primary" | "blue";
}

export interface BarLineEvolutionChartProps<T extends Record<string, unknown>> {
  data: T[];
  xAxisKey?: string;
  height?: number;
  /** Série en barres */
  barSeries?: {
    dataKey: keyof T | string;
    name: string;
    yAxisId?: "left" | "right";
    fill?: string;
    fillOpacity?: number;
    maxBarSize?: number;
  };
  /** Afficher la série barres */
  showBar?: boolean;
  /** Série courbe : line ou area */
  curveSeries?: {
    type: "line" | "area";
    dataKey: keyof T | string;
    name: string;
    yAxisId?: "left" | "right";
    domain?: [number, number] | [number, "auto"];
    stroke?: string;
  };
  /** Afficher la série courbe */
  showCurve?: boolean;
  /** Options de toggle (style admin : barres arrondies, bordures) */
  toggleOptions?: ToggleOption[];
  /** Clés actives (pour le style des boutons) */
  activeKeys?: Set<string>;
  onToggle?: (key: string) => void;
  /** Nombre de points pour afficher les dots sur les Line (ex: <= 60) */
  showDotsThreshold?: number;
}

/**
 * Graphique ComposedChart : barres + courbe (line/area) avec toggles.
 * Utilisé par SiteAnalytics, RouteMetrics et le scanner.
 */
function BarLineEvolutionChart<T extends Record<string, unknown>>({
  data,
  xAxisKey = "ts",
  height = 320,
  barSeries,
  curveSeries,
  toggleOptions = [],
  activeKeys = new Set(),
  onToggle,
  showDotsThreshold = 60,
  showBar: showBarProp = true,
  showCurve: showCurveProp = true,
}: BarLineEvolutionChartProps<T>) {
  const hasBar = !!barSeries;
  const hasCurve = !!curveSeries;
  const showBar = hasBar && showBarProp;
  const showCurve = hasCurve && showCurveProp;

  if (!hasBar && !hasCurve) return null;

  const barYAxis = barSeries?.yAxisId ?? "left";
  const curveYAxis =
    curveSeries?.yAxisId ??
    (showBar ? (barYAxis === "left" ? "right" : "left") : "left");
  const CurveComponent = curveSeries?.type === "area" ? Area : Line;

  return (
    <>
      {toggleOptions.length > 0 && onToggle && (
        <div className="flex gap-2 rounded-lg border border-[var(--border)] p-1 bg-[var(--color-surface-subtle)]">
          {toggleOptions.map((opt) => {
            const isActive = activeKeys.has(opt.key);
            const colorClass =
              opt.activeColor === "blue"
                ? "bg-[rgba(96,165,250,0.2)] text-[rgb(96,165,250)]"
                : "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]";
            return (
              <button
                key={opt.key}
                type="button"
                onClick={() => onToggle(opt.key)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                  isActive
                    ? colorClass
                    : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      )}

      <div style={{ width: "100%", height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
              opacity={0.5}
            />
            <XAxis
              dataKey={xAxisKey}
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              interval="preserveStartEnd"
              minTickGap={40}
            />

            {showBar && (
              <YAxis
                yAxisId={barYAxis}
                orientation={barYAxis === "left" ? "left" : "right"}
                tick={AXIS_TICK}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
                label={{
                  value: barSeries!.name,
                  angle: barYAxis === "left" ? -90 : 90,
                  position: barYAxis === "left" ? "insideLeft" : "insideRight",
                  offset: 10,
                  style: AXIS_LABEL_STYLE,
                }}
                allowDecimals={false}
              />
            )}

            {showCurve && (
              <YAxis
                yAxisId={curveYAxis}
                orientation={curveYAxis === "left" ? "left" : "right"}
                domain={curveSeries!.domain}
                tick={AXIS_TICK}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
                label={{
                  value: curveSeries!.name,
                  angle: curveYAxis === "left" ? -90 : 90,
                  position:
                    curveYAxis === "left" ? "insideLeft" : "insideRight",
                  offset: 10,
                  style: AXIS_LABEL_STYLE,
                }}
                allowDecimals={false}
              />
            )}

            <Tooltip {...TOOLTIP_STYLE} />
            <Legend
              wrapperStyle={{
                fontSize: "0.75rem",
                color: "var(--muted)",
              }}
            />

            {showBar && (
              <Bar
                yAxisId={barYAxis}
                dataKey={barSeries!.dataKey as string}
                name={barSeries!.name}
                fill={barSeries!.fill ?? "rgba(var(--primary), 0.6)"}
                fillOpacity={barSeries!.fillOpacity}
                radius={[3, 3, 0, 0]}
                maxBarSize={barSeries!.maxBarSize ?? 32}
              />
            )}

            {showCurve && (
              <CurveComponent
                yAxisId={curveYAxis}
                type="monotone"
                dataKey={curveSeries!.dataKey as string}
                name={curveSeries!.name}
                stroke={curveSeries!.stroke ?? "rgb(96, 165, 250)"}
                strokeWidth={2}
                {...(curveSeries!.type === "area"
                  ? { fill: "rgba(var(--primary), 0.2)" }
                  : {
                      dot: data.length <= showDotsThreshold ? { r: 3 } : false,
                      activeDot: { r: 4 },
                      connectNulls: true,
                    })}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

export default React.memo(
  BarLineEvolutionChart,
) as typeof BarLineEvolutionChart;

/** Toggles seuls, à placer dans l'en-tête à côté du titre */
export function BarLineEvolutionChartToggles({
  toggleOptions,
  activeKeys,
  onToggle,
}: {
  toggleOptions: ToggleOption[];
  activeKeys: Set<string>;
  onToggle: (key: string) => void;
}) {
  return (
    <div className="flex gap-2 rounded-lg border border-[var(--border)] p-1 bg-[var(--color-surface-subtle)]">
      {toggleOptions.map((opt) => {
        const isActive = activeKeys.has(opt.key);
        const colorClass =
          opt.activeColor === "blue"
            ? "bg-[rgba(96,165,250,0.2)] text-[rgb(96,165,250)]"
            : "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]";
        return (
          <button
            key={opt.key}
            type="button"
            onClick={() => onToggle(opt.key)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
              isActive
                ? colorClass
                : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
