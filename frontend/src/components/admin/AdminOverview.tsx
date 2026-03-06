"use client";

import { useMemo } from "react";
import useSWR from "swr";
import {
  Users,
  CreditCard,
  TrendingUp,
  Mail,
  Activity,
  Eye,
  Shield,
  Bell,
  Image as ImageLucide,
  FileText,
  Globe,
  RefreshCw,
  ArrowRight,
} from "lucide-react";
import Card from "../ui/cards/Card";
import Badge from "../ui/Badge";
import KpiGrid from "./KpiGrid";
import type { KpiItem } from "./KpiGrid";
import adminService from "../../services/admin";
import type {
  UsersStatsResponse,
  SubscriptionStatsResponse,
  AlertSummaryResponse,
  AuditStatsResponse,
  ImageGalleryStats,
  PageViewsSummaryResponse,
} from "../../services/admin";
import { formatFileSize } from "../../utils/numberFormatter";
import { computeApiKpis } from "../../utils/metricsHelpers";
import type { ApiKpis } from "../../utils/metricsHelpers";
import { GenericButton } from "../buttons";
import { AdminInlineLoading } from "./AdminSectionLoading";
import { ADMIN_OVERVIEW_KEY } from "../../hooks/swr/keys";
import { useLanguage } from "../LanguageProvider";

/* ─────────────────────── Types ─────────────────────── */

interface OverviewData {
  userStats: UsersStatsResponse | null;
  subStats: SubscriptionStatsResponse | null;
  alertSummary: AlertSummaryResponse | null;
  auditStats: AuditStatsResponse | null;
  imageStats: ImageGalleryStats | null;
  siteStats: PageViewsSummaryResponse | null;
  contactPending: number;
  contactTotal: number;
  apiMetrics: ApiKpis | null;
}

/* ─────────────────────── Props ─────────────────────── */

interface AdminOverviewProps {
  onNavigate: (tabId: string) => void;
}

/* ─────────────────────── Composant ─────────────────────── */

export default function AdminOverview({ onNavigate }: AdminOverviewProps) {
  const { t, language } = useLanguage();
  const loc = language === "en" ? "en-US" : "fr-FR";

  /* ── SWR : chargement de toutes les données en un seul fetcher ── */
  const {
    data,
    isLoading: loading,
    mutate: revalidate,
  } = useSWR<OverviewData>(
    ADMIN_OVERVIEW_KEY,
    async () => {
      const [
        userStats,
        subStats,
        alertSummary,
        auditStats,
        imageStats,
        siteStatsRes,
        contacts,
        apiRes,
      ] = await Promise.allSettled([
        adminService.getUsersStats(),
        adminService.getSubscriptionStats(),
        adminService.getAlertSummary(),
        adminService.getAuditStats({}),
        adminService.getImageStats(),
        adminService.getPageViewsSummary({}),
        adminService.getContactMessages(null, 1000, 0),
        adminService.getPerformance({ windowMinutes: 1440, limit: 50 }),
      ]);

      // Parse site stats (retourne { success, data })
      let siteStats: PageViewsSummaryResponse | null = null;
      if (
        siteStatsRes.status === "fulfilled" &&
        siteStatsRes.value?.success &&
        siteStatsRes.value?.data
      ) {
        siteStats = siteStatsRes.value.data;
      }

      // Parse contact counts
      let contactPending = 0;
      let contactTotal = 0;
      if (contacts.status === "fulfilled" && contacts.value) {
        const contactData = contacts.value.data || [];
        contactTotal = contacts.value.total || contactData.length;
        contactPending = contactData.filter(
          (c: { status: string }) => c.status === "pending",
        ).length;
      }

      // Parse API metrics
      let apiMetrics: ApiKpis | null = null;
      if (apiRes.status === "fulfilled" && apiRes.value?.success) {
        const metrics = apiRes.value.metrics as Record<string, unknown>[];
        apiMetrics = computeApiKpis(metrics);
      }

      return {
        userStats: userStats.status === "fulfilled" ? userStats.value : null,
        subStats: subStats.status === "fulfilled" ? subStats.value : null,
        alertSummary:
          alertSummary.status === "fulfilled" ? alertSummary.value : null,
        auditStats: auditStats.status === "fulfilled" ? auditStats.value : null,
        imageStats: imageStats.status === "fulfilled" ? imageStats.value : null,
        siteStats,
        contactPending,
        contactTotal,
        apiMetrics,
      };
    },
    { dedupingInterval: 60_000 },
  );

  const loadAll = () => revalidate();

  /* ── fallback si pas encore chargé ── */
  const d: OverviewData = useMemo(
    () =>
      data ?? {
        userStats: null,
        subStats: null,
        alertSummary: null,
        auditStats: null,
        imageStats: null,
        siteStats: null,
        contactPending: 0,
        contactTotal: 0,
        apiMetrics: null,
      },
    [data],
  );

  /* ── KPI principale ── */
  const mainKpis = useMemo<KpiItem[]>(() => {
    const items: KpiItem[] = [];

    items.push({
      label: t("admin.overview.users"),
      value: d.userStats ? d.userStats.total_users.toLocaleString(loc) : "—",
      icon: <Users className="w-4 h-4 text-[rgb(var(--primary))]" />,
      bgColor: "rgba(var(--primary),0.15)",
    });

    items.push({
      label: t("admin.overview.premium"),
      value: d.subStats ? d.subStats.premium_count.toLocaleString(loc) : "—",
      icon: <CreditCard className="w-4 h-4 text-[rgb(var(--warning))]" />,
      bgColor: "rgba(var(--warning),0.15)",
    });

    items.push({
      label: t("admin.overview.pageViews"),
      value: d.siteStats ? d.siteStats.totalViews.toLocaleString(loc) : "—",
      icon: <Eye className="w-4 h-4 text-[rgb(96,165,250)]" />,
      bgColor: "rgba(96,165,250,0.15)",
    });

    items.push({
      label: t("admin.overview.uniqueVisitors"),
      value: d.siteStats
        ? d.siteStats.totalUniqueVisitors.toLocaleString(loc)
        : "—",
      icon: <Globe className="w-4 h-4 text-[rgb(52,211,153)]" />,
      bgColor: "rgba(52,211,153,0.15)",
    });

    items.push({
      label: t("admin.overview.apiRequests24h"),
      value: d.apiMetrics
        ? d.apiMetrics.totalRequests.toLocaleString(loc)
        : "—",
      icon: <Activity className="w-4 h-4 text-[rgb(168,85,247)]" />,
      bgColor: "rgba(168,85,247,0.15)",
    });

    items.push({
      label: t("admin.overview.activeAlerts"),
      value: d.alertSummary ? d.alertSummary.unacknowledged.toString() : "—",
      icon: <Bell className="w-4 h-4 text-[rgb(var(--danger))]" />,
      bgColor: "rgba(var(--danger),0.15)",
    });

    return items;
  }, [d, t, loc]);

  /* ── Sections résumées ── */
  const sections = useMemo(() => {
    const list: Array<{
      id: string;
      title: string;
      icon: React.ReactNode;
      items: Array<{ label: string; value: React.ReactNode }>;
      tabId: string;
      badgeCount?: number;
      badgeVariant?: "error" | "warning" | "success" | "info";
    }> = [];

    // Utilisateurs & Abonnements
    if (d.userStats || d.subStats) {
      list.push({
        id: "users",
        title: t("admin.overview.usersSubscriptions"),
        icon: <Users className="w-5 h-5 text-[rgb(var(--primary))]" />,
        tabId: "users",
        items: [
          {
            label: t("admin.overview.totalRegistered"),
            value: d.userStats?.total_users.toLocaleString(loc) ?? "—",
          },
          {
            label: t("admin.overview.new7d"),
            value: d.userStats?.recent_users_7d.toLocaleString(loc) ?? "—",
          },
          {
            label: t("admin.overview.premiumConversion"),
            value: d.subStats ? `${d.subStats.conversion_rate}%` : "—",
          },
          {
            label: t("admin.overview.churn"),
            value: d.subStats ? `${d.subStats.churn_rate}%` : "—",
          },
          {
            label: t("admin.overview.newsletter"),
            value:
              d.userStats?.newsletter_subscribers.toLocaleString(loc) ?? "—",
          },
          {
            label: t("admin.overview.suspended"),
            value: (d.userStats?.statuses["suspended"] ?? 0).toLocaleString(
              loc,
            ),
          },
        ],
      });
    }

    // API
    if (d.apiMetrics) {
      list.push({
        id: "api",
        title: t("admin.overview.apiPerformance24h"),
        icon: <Activity className="w-5 h-5 text-[rgb(168,85,247)]" />,
        tabId: "metrics",
        badgeCount:
          d.apiMetrics.totalErrors > 0 ? d.apiMetrics.totalErrors : undefined,
        badgeVariant: "error",
        items: [
          {
            label: t("admin.overview.requests"),
            value: d.apiMetrics.totalRequests.toLocaleString(loc),
          },
          {
            label: t("admin.overview.avgTime"),
            value:
              d.apiMetrics.avgMs != null
                ? `${Math.round(d.apiMetrics.avgMs)} ms`
                : "—",
          },
          {
            label: t("admin.overview.successRate"),
            value:
              d.apiMetrics.successRate != null
                ? `${(d.apiMetrics.successRate * 100).toFixed(1)}%`
                : "—",
          },
          {
            label: t("admin.overview.errors"),
            value: d.apiMetrics.totalErrors.toLocaleString(loc),
          },
        ],
      });
    }

    // Site analytics
    if (d.siteStats) {
      list.push({
        id: "analytics",
        title: t("admin.overview.siteAnalytics"),
        icon: <Eye className="w-5 h-5 text-[rgb(96,165,250)]" />,
        tabId: "analytics",
        items: [
          {
            label: t("admin.overview.pageViews"),
            value: d.siteStats.totalViews.toLocaleString(loc),
          },
          {
            label: t("admin.overview.uniqueVisitors"),
            value: d.siteStats.totalUniqueVisitors.toLocaleString(loc),
          },
          {
            label: t("admin.overview.pagesPerSession"),
            value: d.siteStats.avgPagesPerSession?.toFixed(1) ?? "—",
          },
          {
            label: t("admin.overview.avgSessionDuration"),
            value:
              d.siteStats.avgSessionDurationMs != null
                ? `${Math.round(d.siteStats.avgSessionDurationMs / 1000)}s`
                : "—",
          },
          {
            label: t("admin.overview.bounceRate"),
            value:
              d.siteStats.bounceRate != null
                ? `${d.siteStats.bounceRate.toFixed(1)}%`
                : "—",
          },
        ],
      });
    }

    // Contact
    list.push({
      id: "contact",
      title: t("admin.overview.contactMessages"),
      icon: <Mail className="w-5 h-5 text-[rgb(var(--warning))]" />,
      tabId: "contact",
      badgeCount: d.contactPending > 0 ? d.contactPending : undefined,
      badgeVariant: "warning",
      items: [
        {
          label: "Total",
          value: d.contactTotal.toLocaleString(loc),
        },
        {
          label: t("admin.overview.pending"),
          value: d.contactPending.toLocaleString(loc),
        },
      ],
    });

    // Alertes
    if (d.alertSummary) {
      list.push({
        id: "alerts",
        title: t("admin.overview.alertsMonitoring"),
        icon: <Bell className="w-5 h-5 text-[rgb(var(--danger))]" />,
        tabId: "alerts",
        badgeCount:
          d.alertSummary.unacknowledged > 0
            ? d.alertSummary.unacknowledged
            : undefined,
        badgeVariant: "error",
        items: [
          {
            label: t("admin.overview.unacknowledged"),
            value: d.alertSummary.unacknowledged.toString(),
          },
          {
            label: t("admin.overview.last24h"),
            value: d.alertSummary.recent_24h.toString(),
          },
          {
            label: t("admin.overview.critical"),
            value: d.alertSummary.critical.toString(),
          },
          {
            label: t("admin.overview.activeRules"),
            value: d.alertSummary.active_rules.toString(),
          },
        ],
      });
    }

    // Audit
    if (d.auditStats) {
      list.push({
        id: "audit",
        title: t("admin.overview.auditLog"),
        icon: <FileText className="w-5 h-5 text-[rgb(52,211,153)]" />,
        tabId: "audit",
        items: [
          {
            label: t("admin.overview.totalActions"),
            value: d.auditStats.total_actions.toLocaleString(loc),
          },
          {
            label: t("admin.overview.actionTypes"),
            value: Object.keys(d.auditStats.by_action).length.toString(),
          },
          {
            label: t("admin.overview.activeAdmins"),
            value: d.auditStats.top_admins.length.toString(),
          },
        ],
      });
    }

    // Galerie (Images + Templates)
    if (d.imageStats) {
      list.push({
        id: "gallery",
        title: t("admin.overview.imageGallery"),
        icon: <ImageLucide className="w-5 h-5 text-[rgb(236,72,153)]" />,
        tabId: "gallery",
        items: [
          {
            label: t("admin.overview.images"),
            value: d.imageStats.total.toLocaleString(loc),
          },
          {
            label: t("admin.overview.diskSpace"),
            value: formatFileSize(d.imageStats.total_size),
          },
          {
            label: t("admin.overview.formats"),
            value: Object.keys(d.imageStats.by_extension).length.toString(),
          },
        ],
      });
    }

    return list;
  }, [d, t, loc]);

  /* ── Indicateurs de santé ── */
  const healthIndicators = useMemo(() => {
    const items: Array<{
      label: string;
      status: "ok" | "warning" | "error";
      detail: string;
    }> = [];

    // API Success Rate
    if (d.apiMetrics?.successRate != null) {
      const rate = d.apiMetrics.successRate * 100;
      items.push({
        label: "API",
        status: rate >= 99 ? "ok" : rate >= 95 ? "warning" : "error",
        detail: t("admin.overview.apiSuccess", { rate: rate.toFixed(1) }),
      });
    }

    // Alertes non acquittées
    if (d.alertSummary) {
      items.push({
        label: t("admin.tabs.alerts"),
        status:
          d.alertSummary.unacknowledged === 0
            ? "ok"
            : d.alertSummary.critical > 0
              ? "error"
              : "warning",
        detail:
          d.alertSummary.unacknowledged === 0
            ? t("admin.overview.noAlerts")
            : t("admin.overview.unacknowledgedCount", {
                count: d.alertSummary.unacknowledged,
              }),
      });
    }

    // Messages en attente
    items.push({
      label: "Contact",
      status:
        d.contactPending === 0
          ? "ok"
          : d.contactPending >= 10
            ? "error"
            : "warning",
      detail:
        d.contactPending === 0
          ? t("admin.overview.allProcessed")
          : t("admin.overview.pendingCount", { count: d.contactPending }),
    });

    // Churn
    if (d.subStats) {
      items.push({
        label: "Churn",
        status:
          d.subStats.churn_rate <= 3
            ? "ok"
            : d.subStats.churn_rate <= 8
              ? "warning"
              : "error",
        detail: `${d.subStats.churn_rate}%`,
      });
    }

    return items;
  }, [d, t]);

  /* ─────────────────────── Rendu ─────────────────────── */

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <Card disableHover>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-[var(--text)]">
              {t("admin.overview.title")}
            </h2>
            <p className="text-[var(--muted)] mt-1">
              {t("admin.overview.subtitle")}
            </p>
          </div>
          <GenericButton
            label={t("admin.common.refresh")}
            onClick={loadAll}
            disabled={loading}
            variant="secondary"
            icon={
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
            }
            iconPosition="left"
          />
        </div>
      </Card>

      {/* Indicateurs de santé */}
      {healthIndicators.length > 0 && (
        <Card disableHover>
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-[rgb(var(--primary))]" />
            <h3
              className="text-base font-semibold text-[var(--text)]"
              style={{ margin: 0 }}
            >
              {t("admin.overview.platformHealth")}
            </h3>
          </div>
          <div className="flex flex-wrap gap-3">
            {healthIndicators.map((indicator) => (
              <div
                key={indicator.label}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)]"
              >
                <div
                  className={`w-2.5 h-2.5 rounded-full ${
                    indicator.status === "ok"
                      ? "bg-[rgb(var(--success))]"
                      : indicator.status === "warning"
                        ? "bg-[rgb(var(--warning))]"
                        : "bg-[rgb(var(--danger))]"
                  }`}
                />
                <span className="text-sm font-medium text-[var(--text)]">
                  {indicator.label}
                </span>
                <span className="text-xs text-[var(--muted)]">
                  {indicator.detail}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* KPIs principales */}
      {loading ? (
        <AdminInlineLoading message={t("admin.overview.loading")} />
      ) : (
        <>
          <KpiGrid items={mainKpis} columns={6} />

          {/* Grille des sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {sections.map((section) => (
              <Card key={section.id} disableHover>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    {section.icon}
                    <h3
                      className="text-sm font-semibold text-[var(--text)]"
                      style={{ margin: 0 }}
                    >
                      {section.title}
                    </h3>
                    {section.badgeCount != null && section.badgeCount > 0 && (
                      <Badge variant={section.badgeVariant ?? "error"}>
                        {section.badgeCount}
                      </Badge>
                    )}
                  </div>
                  <button
                    onClick={() => onNavigate(section.tabId)}
                    className="flex items-center gap-1 text-xs text-[rgb(var(--primary))] hover:underline transition-colors"
                  >
                    {t("admin.common.view")}
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
                <div className="space-y-2">
                  {section.items.map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center justify-between py-1.5 border-b border-[var(--border)] last:border-0"
                    >
                      <span className="text-xs text-[var(--muted)]">
                        {item.label}
                      </span>
                      <span className="text-sm font-semibold text-[var(--text)]">
                        {item.value}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>

          {/* Abonnements — répartition mensuelle (mini) */}
          {d.subStats && d.subStats.monthly_history.length > 0 && (
            <Card disableHover>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-[rgb(var(--primary))]" />
                  <h3
                    className="text-sm font-semibold text-[var(--text)]"
                    style={{ margin: 0 }}
                  >
                    {t("admin.overview.registrationsEvolution")}
                  </h3>
                </div>
                <button
                  onClick={() => onNavigate("users")}
                  className="flex items-center gap-1 text-xs text-[rgb(var(--primary))] hover:underline transition-colors"
                >
                  {t("admin.common.details")}
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
              <div className="flex items-end gap-1 h-24">
                {d.subStats.monthly_history.slice(-6).map((month, idx) => {
                  const total = month.free + month.premium;
                  const maxVal = Math.max(
                    ...d
                      .subStats!.monthly_history.slice(-6)
                      .map((m) => m.free + m.premium),
                  );
                  const heightPct = maxVal > 0 ? (total / maxVal) * 100 : 0;
                  const premiumPct =
                    total > 0 ? (month.premium / total) * 100 : 0;

                  return (
                    <div
                      key={idx}
                      className="flex-1 flex flex-col items-center gap-1"
                    >
                      <div
                        className="w-full rounded-t relative overflow-hidden"
                        style={{
                          height: `${Math.max(heightPct, 4)}%`,
                          minHeight: "4px",
                        }}
                      >
                        <div
                          className="absolute bottom-0 w-full bg-[rgb(var(--primary))]"
                          style={{ height: `${premiumPct}%` }}
                        />
                        <div
                          className="absolute top-0 w-full bg-[rgba(var(--primary),0.3)]"
                          style={{ height: `${100 - premiumPct}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-[var(--muted)]">
                        {month.month.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center gap-4 mt-3 text-xs text-[var(--muted)]">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded bg-[rgba(var(--primary),0.3)]" />
                  {t("admin.users.free")}
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded bg-[rgb(var(--primary))]" />
                  Premium
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
