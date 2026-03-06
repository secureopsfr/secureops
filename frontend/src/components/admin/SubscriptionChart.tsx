"use client";

import React from "react";
import { TrendingUp } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import Card from "../ui/cards/Card";

const MONTH_LABELS = [
  "Jan",
  "Fév",
  "Mar",
  "Avr",
  "Mai",
  "Jun",
  "Jul",
  "Aoû",
  "Sep",
  "Oct",
  "Nov",
  "Déc",
];

interface SubscriptionChartProps {
  data: Array<{ month: string; free: number; premium: number }>;
}

/**
 * Graphique en barres montrant l'évolution des inscriptions free vs premium
 * sur les 12 derniers mois.
 */
export default function SubscriptionChart({ data }: SubscriptionChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <Card style={{ overflow: "visible" }}>
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-[rgb(var(--primary))]" />
        <h3
          className="text-base font-semibold text-[var(--text)]"
          style={{ margin: 0 }}
        >
          Évolution des inscriptions (12 mois)
        </h3>
      </div>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
              opacity={0.3}
            />
            <XAxis
              dataKey="month"
              tick={{ fill: "var(--muted)", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              tickFormatter={(v: string) => {
                const [, m] = v.split("-");
                return MONTH_LABELS[parseInt(m, 10) - 1] || v;
              }}
            />
            <YAxis
              tick={{ fill: "var(--muted)", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
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
              wrapperStyle={{ fontSize: "0.75rem", color: "var(--muted)" }}
            />
            <Bar
              dataKey="free"
              name="Free"
              fill="rgba(var(--primary),0.6)"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="premium"
              name="Premium"
              fill="rgb(var(--warning))"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
