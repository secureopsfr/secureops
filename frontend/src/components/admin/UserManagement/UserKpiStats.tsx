"use client";

import { useMemo } from "react";
import {
  Users,
  TrendingUp,
  TrendingDown,
  CreditCard,
  AlertTriangle,
} from "lucide-react";
import type {
  UsersStatsResponse,
  SubscriptionStatsResponse,
} from "../../../services/admin";
import KpiGrid from "../KpiGrid";
import type { KpiItem } from "../KpiGrid";
import { useLanguage } from "../../LanguageProvider";

interface UserKpiStatsProps {
  stats: UsersStatsResponse | null;
  subStats: SubscriptionStatsResponse | null;
  loading: boolean;
}

export default function UserKpiStats({
  stats,
  subStats,
  loading,
}: UserKpiStatsProps) {
  const { t, language } = useLanguage();
  const loc = language === "en" ? "en-US" : "fr-FR";

  const kpiItems = useMemo<KpiItem[] | null>(() => {
    if (!stats && !subStats) return null;
    const items: KpiItem[] = [];

    if (stats) {
      items.push(
        {
          label: t("admin.users.kpiUsers"),
          value: stats.total_users.toLocaleString(loc),
          icon: <Users className="w-4 h-4 text-[rgb(var(--primary))]" />,
          bgColor: "rgba(var(--primary),0.15)",
        },
        {
          label: t("admin.users.kpiNew7d"),
          value: stats.recent_users_7d.toLocaleString(loc),
          icon: <TrendingUp className="w-4 h-4 text-[rgb(52,211,153)]" />,
          bgColor: "rgba(52,211,153,0.15)",
        },
      );
    }

    if (subStats) {
      items.push(
        {
          label: t("admin.users.kpiPremium"),
          value: subStats.premium_count.toLocaleString(loc),
          icon: <CreditCard className="w-4 h-4 text-[rgb(var(--warning))]" />,
          bgColor: "rgba(var(--warning),0.15)",
        },
        {
          label: t("admin.users.kpiConversion"),
          value: `${subStats.conversion_rate}%`,
          icon: <TrendingUp className="w-4 h-4 text-[rgb(96,165,250)]" />,
          bgColor: "rgba(96,165,250,0.15)",
        },
        {
          label: t("admin.users.kpiChurn"),
          value: `${subStats.churn_rate}%`,
          icon: <TrendingDown className="w-4 h-4 text-[rgb(var(--danger))]" />,
          bgColor: "rgba(var(--danger),0.15)",
        },
      );
    }

    if (stats) {
      items.push({
        label: t("admin.users.kpiSuspended"),
        value: (stats.statuses["suspended"] || 0).toLocaleString(loc),
        icon: <AlertTriangle className="w-4 h-4 text-[rgb(var(--danger))]" />,
        bgColor: "rgba(var(--danger),0.15)",
      });
    }

    return items.length > 0 ? items : null;
  }, [stats, subStats, t, loc]);

  if (!kpiItems || loading) return null;

  return <KpiGrid items={kpiItems} columns={6} />;
}
