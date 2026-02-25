"use client";

import { useEffect, useMemo } from "react";
import useSWR from "swr";
import {
  Shield,
  User,
  Mail,
  CreditCard,
  MessageSquare,
  RefreshCw,
  FileText,
  Clock,
  Activity,
} from "lucide-react";
import Card from "../cards/Card";
import Table from "../Table";
import Badge from "../Badge";
import KpiGrid from "./KpiGrid";
import Pagination from "./Pagination";
import DropdownSelector from "../buttons/DropdownSelector";
import adminService from "../../services/admin";
import type { AuditLogEntry, AuditStatsResponse } from "../../services/admin";
import { formatDateTime } from "../../utils/dateFormat";
import { AdminInlineLoading } from "./AdminSectionLoading";
import { useLanguage } from "../LanguageProvider";
import { usePagination } from "../../hooks/usePagination";
import { useFilters } from "../../hooks/useFilters";
import { adminAuditLogsKey, adminAuditStatsKey } from "../../hooks/swr/keys";

/* ─────────────────────── Helpers ─────────────────────── */

function getActionBadgeVariant(
  action: string,
): "success" | "warning" | "error" | "info" | "default" {
  if (action.includes("ban") || action.includes("delete")) return "error";
  if (action.includes("unban") || action.includes("create")) return "success";
  if (
    action.includes("update") ||
    action.includes("change") ||
    action.includes("status")
  )
    return "warning";
  if (action.includes("reply") || action.includes("send")) return "info";
  return "default";
}

function getEntityIcon(entityType: string) {
  switch (entityType) {
    case "user":
      return <User className="w-3.5 h-3.5" />;
    case "contact":
      return <MessageSquare className="w-3.5 h-3.5" />;
    case "newsletter":
      return <Mail className="w-3.5 h-3.5" />;
    case "subscription":
      return <CreditCard className="w-3.5 h-3.5" />;
    default:
      return <FileText className="w-3.5 h-3.5" />;
  }
}

function formatAction(action: string, t: (key: string) => string): string {
  const labels: Record<string, string> = {
    "user.ban": t("admin.audit.actionBan"),
    "user.unban": t("admin.audit.actionUnban"),
    "user.group_change": t("admin.audit.actionGroupChange"),
    "contact.status_change": t("admin.audit.actionStatusChange"),
    "contact.delete": t("admin.audit.actionDelete"),
    "contact.reply": t("admin.audit.actionReply"),
    "subscription.update": t("admin.audit.actionSubUpdate"),
    "newsletter.send": t("admin.audit.actionNewsletterSend"),
    "newsletter.create": t("admin.audit.actionNewsletterCreate"),
    "newsletter.schedule": t("admin.audit.actionSchedule"),
  };
  return labels[action] ?? action;
}

const PAGE_SIZE = 25;

/* ─────────────────────── Composant ─────────────────────── */

export default function AuditLog() {
  const { t } = useLanguage();
  /* ── hooks personnalisés ── */
  const pagination = usePagination(PAGE_SIZE);
  const { filters, updateFilter } = useFilters({
    entity: "",
    action: "",
  });

  /* ── SWR : logs d'audit ── */
  const logsSwrKey = adminAuditLogsKey({
    entity: filters.entity || null,
    action: filters.action || null,
    limit: pagination.limit,
    offset: pagination.offset,
  });

  const {
    data: logsData,
    isLoading: logsLoading,
    mutate: mutateLogs,
  } = useSWR(logsSwrKey, () =>
    adminService.getAuditLogs({
      entityType: filters.entity || null,
      action: filters.action || null,
      limit: pagination.limit,
      offset: pagination.offset,
    }),
  );

  const logs = (logsData?.logs as AuditLogEntry[]) ?? [];
  const total = logsData?.total ?? 0;

  /* ── SWR : stats d'audit ── */
  const { data: stats } = useSWR<AuditStatsResponse>(
    adminAuditStatsKey(),
    () => adminService.getAuditStats(),
    { dedupingInterval: 60_000 },
  );

  const loading = logsLoading;
  const loadData = () => mutateLogs();

  /* ── réinitialiser page si filtre change ── */
  useEffect(() => {
    pagination.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.entity, filters.action]);

  /* ── colonnes table ── */
  const columns = useMemo(
    () => [
      {
        key: "entity_id",
        header: t("admin.audit.colId"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span
            className="font-mono text-xs text-[var(--muted)]"
            title={String(item.entity_id ?? "")}
            style={{
              maxWidth: "8rem",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              display: "inline-block",
              minWidth: "1rem",
            }}
          >
            {item.entity_id
              ? String(item.entity_id).length > 12
                ? String(item.entity_id).slice(0, 12) + "…"
                : String(item.entity_id)
              : "—"}
          </span>
        ),
      },
      {
        key: "created_at",
        header: t("admin.audit.colDate"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="text-xs text-[var(--muted)]">
            {formatDateTime(item.created_at as string | null)}
          </span>
        ),
      },
      {
        key: "admin_email",
        header: t("admin.audit.colAdmin"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="text-xs font-medium text-[var(--text)]">
            {(item.admin_email as string) || "—"}
          </span>
        ),
      },
      {
        key: "action",
        header: t("admin.audit.colAction"),
        align: "center" as const,
        sortable: false,
        render: (item: Record<string, unknown>) => (
          <Badge variant={getActionBadgeVariant(item.action as string)}>
            {formatAction(item.action as string, t)}
          </Badge>
        ),
      },
      {
        key: "entity_type",
        header: t("admin.audit.colEntity"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <div className="flex items-center justify-center gap-1.5">
            {getEntityIcon(item.entity_type as string)}
            <span className="text-xs capitalize">
              {item.entity_type as string}
            </span>
          </div>
        ),
      },
      {
        key: "details",
        header: t("admin.audit.colDetails"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => {
          const details = item.details;
          if (!details)
            return <span className="text-xs text-[var(--muted)]">—</span>;
          const str =
            typeof details === "string" ? details : JSON.stringify(details);
          return (
            <span
              className="font-mono text-xs text-[var(--muted)]"
              title={str}
              style={{
                maxWidth: "12rem",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                display: "inline-block",
              }}
            >
              {str.length > 40 ? str.slice(0, 40) + "…" : str}
            </span>
          );
        },
      },
    ],
    [t],
  );

  /* ── entité types uniques pour le filtre ── */
  const entityTypes = ["user", "contact", "newsletter", "subscription"];
  const actionTypes = [
    "user.ban",
    "user.unban",
    "user.group_change",
    "contact.status_change",
    "contact.delete",
    "contact.reply",
    "subscription.update",
    "newsletter.send",
  ];

  /* ─────────────────────── Rendu ─────────────────────── */

  return (
    <div className="space-y-6">
      {/* En-tête : titre, description, refresh et filtres dans la même carte */}
      <Card disableHover>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-[var(--text)]">
                {t("admin.audit.title")}
              </h2>
              <p className="text-[var(--muted)] mt-1">
                {t("admin.audit.description")}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <DropdownSelector
                selectedValue={filters.entity}
                onChange={(value) => updateFilter("entity", value)}
                options={[
                  { value: "", label: t("admin.audit.allEntities") },
                  ...entityTypes.map((e) => ({ value: e, label: e })),
                ]}
                width="11rem"
                triggerClassName="h-9"
              />
              <DropdownSelector
                selectedValue={filters.action}
                onChange={(value) => updateFilter("action", value)}
                options={[
                  { value: "", label: t("admin.audit.allActions") },
                  ...actionTypes.map((a) => ({
                    value: a,
                    label: formatAction(a, t),
                  })),
                ]}
                width="13rem"
                triggerClassName="h-9"
              />
              {(filters.entity || filters.action) && (
                <button
                  onClick={() => {
                    updateFilter("entity", "");
                    updateFilter("action", "");
                  }}
                  className="flex h-9 items-center px-3 py-2 rounded-lg text-sm text-[rgb(var(--danger))] hover:bg-[rgba(var(--danger),0.1)] transition-colors"
                >
                  {t("admin.audit.reset")}
                </button>
              )}
              <button
                onClick={loadData}
                className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] text-sm hover:bg-[rgba(var(--primary),0.3)] transition-colors"
              >
                <RefreshCw
                  className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
                />
                {t("admin.common.refresh")}
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* KPI Stats */}
      {stats && (
        <KpiGrid
          columns={4}
          items={[
            {
              label: t("admin.audit.totalActions"),
              value: stats.total_actions.toLocaleString(t("locale")),
              icon: <Activity className="w-4 h-4 text-[rgb(var(--primary))]" />,
              bgColor: "rgba(var(--primary),0.15)",
            },
            {
              label: t("admin.audit.actionTypes"),
              value: Object.keys(stats.by_action).length,
              icon: <FileText className="w-4 h-4 text-[rgb(96,165,250)]" />,
              bgColor: "rgba(96,165,250,0.15)",
            },
            {
              label: t("admin.audit.entityTypes"),
              value: Object.keys(stats.by_entity).length,
              icon: <Shield className="w-4 h-4 text-[rgb(52,211,153)]" />,
              bgColor: "rgba(52,211,153,0.15)",
            },
            {
              label: t("admin.audit.activeAdmins"),
              value: stats.top_admins.length,
              icon: <Clock className="w-4 h-4 text-[rgb(var(--warning))]" />,
              bgColor: "rgba(var(--warning),0.15)",
            },
          ]}
        />
      )}

      {/* Tableau des logs */}
      <Card disableHover style={{ overflow: "visible" }}>
        {loading && logs.length === 0 ? (
          <AdminInlineLoading message={t("admin.audit.loadingAudit")} />
        ) : (
          <>
            <Table
              data={logs as unknown as Record<string, unknown>[]}
              columns={columns}
              emptyMessage={t("admin.audit.noEntries")}
              cellClassName="text-xs"
            />

            <Pagination
              mode="page"
              page={pagination.page}
              pageSize={PAGE_SIZE}
              total={total}
              onPageChange={pagination.setPage}
            />
          </>
        )}
      </Card>
    </div>
  );
}
