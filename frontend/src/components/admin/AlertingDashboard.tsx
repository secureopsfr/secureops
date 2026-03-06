"use client";

import { useState, useMemo } from "react";
import useSWR from "swr";
import {
  Bell,
  Plus,
  Trash2,
  CheckCircle,
  AlertTriangle,
  AlertOctagon,
  Info,
  RefreshCw,
  ToggleLeft,
  ToggleRight,
  Zap,
  Activity,
  Shield,
} from "lucide-react";
import Card from "../ui/cards/Card";
import Table from "../Table";
import Badge from "../ui/Badge";
import Modal from "../ui/Modal";
import ConfirmModal from "../ConfirmModal";
import DropdownSelector from "../buttons/DropdownSelector";
import Checkbox from "../inputs/Checkbox";
import KpiGrid from "./KpiGrid";
import Pagination from "./Pagination";
import adminService from "../../services/admin";
import type {
  AlertRuleRecord,
  AlertEventRecord,
  AlertSummaryResponse,
} from "../../services/admin";
import { error as logError } from "../../utils/logger";
import { formatDateTime } from "../../utils/dateFormat";
import { AdminInlineLoading } from "./AdminSectionLoading";
import { useLanguage } from "../LanguageProvider";
import {
  adminAlertEventsKey,
  ADMIN_ALERT_RULES_KEY,
  ADMIN_ALERT_SUMMARY_KEY,
} from "../../hooks/swr/keys";

/* ─────────────────────── Helpers ─────────────────────── */

function getSeverityBadgeVariant(
  severity: string,
): "error" | "warning" | "info" | "default" {
  switch (severity) {
    case "critical":
      return "error";
    case "high":
      return "error";
    case "medium":
      return "warning";
    case "low":
      return "info";
    default:
      return "default";
  }
}

function getSeverityIcon(severity: string) {
  switch (severity) {
    case "critical":
      return <AlertOctagon className="w-3.5 h-3.5" />;
    case "high":
      return <AlertTriangle className="w-3.5 h-3.5" />;
    case "medium":
      return <Info className="w-3.5 h-3.5" />;
    default:
      return <Info className="w-3.5 h-3.5" />;
  }
}

function formatCondition(cond: string): string {
  const labels: Record<string, string> = {
    gt: ">",
    lt: "<",
    gte: "≥",
    lte: "≤",
    eq: "=",
  };
  return labels[cond] ?? cond;
}

function formatMetricStatic(
  metric: string,
  t: (key: string) => string,
): string {
  const labels: Record<string, string> = {
    error_rate: t("admin.alerts.errorRate"),
    response_time: t("admin.alerts.responseTime"),
    error_count: t("admin.alerts.errorCount"),
    request_count: t("admin.alerts.requestCount"),
  };
  return labels[metric] ?? metric;
}

const PAGE_SIZE = 20;

/* ─────────────────────── Types ─────────────────────── */

type DashboardTab = "events" | "rules";

/* ─────────────────────── Composant ─────────────────────── */

export default function AlertingDashboard() {
  const { t } = useLanguage();
  const [tab, setTab] = useState<DashboardTab>("events");
  const [page, setPage] = useState(0);

  /* ── modals ── */
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteRule, setDeleteRule] = useState<AlertRuleRecord | null>(null);

  /* ── form state ── */
  const [formName, setFormName] = useState("");
  const [formMetric, setFormMetric] = useState("error_rate");
  const [formCondition, setFormCondition] = useState("gt");
  const [formThreshold, setFormThreshold] = useState(5);
  const [formWindow, setFormWindow] = useState(5);
  const [formCooldown, setFormCooldown] = useState(30);
  const [formService, setFormService] = useState("");
  const [formNotify, setFormNotify] = useState(true);
  const [formSubmitting, setFormSubmitting] = useState(false);

  /* ── SWR : règles d'alerte ── */
  const { data: rules = [], mutate: mutateRules } = useSWR<AlertRuleRecord[]>(
    ADMIN_ALERT_RULES_KEY,
    () => adminService.getAlertRules(),
  );

  /* ── SWR : événements d'alerte ── */
  const eventsSwrKey = adminAlertEventsKey({
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  });
  const {
    data: eventsData,
    isLoading: eventsLoading,
    mutate: mutateEvents,
  } = useSWR(eventsSwrKey, () =>
    adminService.getAlertEvents({ limit: PAGE_SIZE, offset: page * PAGE_SIZE }),
  );
  const events = (eventsData?.events as AlertEventRecord[]) ?? [];
  const eventsTotal = eventsData?.total ?? 0;

  /* ── SWR : résumé alertes ── */
  const { data: summary = null, mutate: mutateSummary } =
    useSWR<AlertSummaryResponse | null>(
      ADMIN_ALERT_SUMMARY_KEY,
      () => adminService.getAlertSummary(),
      { dedupingInterval: 60_000 },
    );

  const loading = eventsLoading;

  const loadData = () => {
    mutateRules();
    mutateEvents();
    mutateSummary();
  };

  /* ── actions ── */
  const handleToggleRule = async (rule: AlertRuleRecord) => {
    try {
      await adminService.toggleAlertRule(rule.id);
      loadData();
    } catch (err) {
      logError("[AlertingDashboard] Toggle error:", err);
    }
  };

  const handleDeleteRule = async () => {
    if (!deleteRule) return;
    try {
      await adminService.deleteAlertRule(deleteRule.id);
      setDeleteRule(null);
      loadData();
    } catch (err) {
      logError("[AlertingDashboard] Delete error:", err);
    }
  };

  const handleAcknowledge = async (eventId: string) => {
    try {
      await adminService.acknowledgeAlert(eventId, "admin");
      loadData();
    } catch (err) {
      logError("[AlertingDashboard] Ack error:", err);
    }
  };

  const handleAcknowledgeAll = async () => {
    try {
      await adminService.acknowledgeAllAlerts("admin");
      loadData();
    } catch (err) {
      logError("[AlertingDashboard] Ack all error:", err);
    }
  };

  const handleCheckAlerts = async () => {
    try {
      await adminService.checkAlerts();
      loadData();
    } catch (err) {
      logError("[AlertingDashboard] Check error:", err);
    }
  };

  const handleCreateRule = async () => {
    setFormSubmitting(true);
    try {
      await adminService.createAlertRule({
        name: formName,
        metric: formMetric,
        condition: formCondition,
        threshold: formThreshold,
        window_minutes: formWindow,
        service_filter: formService || null,
        notify_email: formNotify,
        enabled: true,
        cooldown_minutes: formCooldown,
      } as Omit<AlertRuleRecord, "id" | "created_at" | "updated_at">);
      setShowCreateModal(false);
      resetForm();
      loadData();
    } catch (err) {
      logError("[AlertingDashboard] Create error:", err);
    } finally {
      setFormSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormName("");
    setFormMetric("error_rate");
    setFormCondition("gt");
    setFormThreshold(5);
    setFormWindow(5);
    setFormCooldown(30);
    setFormService("");
    setFormNotify(true);
  };

  /* ── colonnes events ── */
  const eventColumns = useMemo(
    () => [
      {
        key: "created_at",
        header: t("admin.alerts.colDate"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="text-xs text-[var(--muted)]">
            {formatDateTime(item.created_at as string | null)}
          </span>
        ),
      },
      {
        key: "severity",
        header: t("admin.alerts.colSeverity"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <div className="flex items-center justify-center gap-1.5">
            {getSeverityIcon(item.severity as string)}
            <Badge variant={getSeverityBadgeVariant(item.severity as string)}>
              {item.severity as string}
            </Badge>
          </div>
        ),
      },
      {
        key: "rule_name",
        header: t("admin.alerts.colRule"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="text-xs font-medium text-[var(--text)]">
            {(item.rule_name as string) || "—"}
          </span>
        ),
      },
      {
        key: "message",
        header: t("admin.alerts.colMessage"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span
            className="text-xs text-[var(--muted)]"
            title={String(item.message ?? "")}
            style={{
              maxWidth: "16rem",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              display: "inline-block",
            }}
          >
            {item.message as string}
          </span>
        ),
      },
      {
        key: "current_value",
        header: t("admin.alerts.colValue"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="font-mono text-xs text-[var(--text)]">
            {(item.current_value as number)?.toFixed(2) ?? "—"}
          </span>
        ),
      },
      {
        key: "acknowledged",
        header: t("admin.alerts.colStatus"),
        align: "center" as const,
        render: (item: Record<string, unknown>) =>
          item.acknowledged ? (
            <Badge variant="success">{t("admin.alerts.acknowledged")}</Badge>
          ) : (
            <button
              onClick={() => handleAcknowledge(item.id as string)}
              className="flex items-center gap-1 px-2 py-1 text-xs rounded-lg bg-[rgba(var(--warning),0.1)] text-[rgb(var(--warning))] hover:bg-[rgba(var(--warning),0.2)] transition-colors"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              {t("admin.alerts.acknowledge")}
            </button>
          ),
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t],
  );

  /* ── colonnes rules ── */
  const ruleColumns = useMemo(
    () => [
      {
        key: "name",
        header: t("admin.alerts.colName"),
        align: "center" as const,
        sticky: true,
        render: (item: Record<string, unknown>) => (
          <span className="text-xs font-medium text-[var(--text)]">
            {item.name as string}
          </span>
        ),
      },
      {
        key: "metric",
        header: t("admin.alerts.colMetric"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <Badge variant="info">
            {formatMetricStatic(item.metric as string, t)}
          </Badge>
        ),
      },
      {
        key: "condition",
        header: t("admin.alerts.colCondition"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="font-mono text-xs text-[var(--text)]">
            {formatCondition(item.condition as string)}{" "}
            {(item.threshold as number)?.toString() ?? "—"}
          </span>
        ),
      },
      {
        key: "window_minutes",
        header: t("admin.alerts.colWindow"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="text-xs text-[var(--muted)]">
            {item.window_minutes as number} min
          </span>
        ),
      },
      {
        key: "service_filter",
        header: t("admin.alerts.colService"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <span className="text-xs text-[var(--muted)]">
            {(item.service_filter as string) || t("admin.alerts.allServices")}
          </span>
        ),
      },
      {
        key: "enabled",
        header: t("admin.alerts.colActive"),
        align: "center" as const,
        render: (item: Record<string, unknown>) => (
          <button
            onClick={() => handleToggleRule(item as unknown as AlertRuleRecord)}
            className="text-[var(--text)] hover:opacity-70 transition-opacity"
            title={
              item.enabled
                ? t("admin.alerts.disable")
                : t("admin.alerts.enable")
            }
          >
            {item.enabled ? (
              <ToggleRight className="w-5 h-5 text-[rgb(var(--success))]" />
            ) : (
              <ToggleLeft className="w-5 h-5 text-[var(--muted)]" />
            )}
          </button>
        ),
      },
      {
        key: "actions",
        header: "",
        align: "center" as const,
        sortable: false,
        render: (item: Record<string, unknown>) => (
          <button
            onClick={() => setDeleteRule(item as unknown as AlertRuleRecord)}
            className="p-1.5 rounded-lg text-[rgb(var(--danger))] hover:bg-[rgba(var(--danger),0.1)] transition-colors"
            title={t("admin.common.delete")}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        ),
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t],
  );

  /* ─────────────────────── Rendu ─────────────────────── */

  return (
    <div className="space-y-6">
      {/* En-tête : titre, description, boutons et toggle Events/Rules dans la même carte */}
      <Card disableHover>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-[var(--text)]">
                {t("admin.alerts.title")}
              </h2>
              <p className="text-[var(--muted)] mt-1">
                {t("admin.alerts.description")}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <div className="flex h-9 items-stretch gap-0.5 rounded-lg border border-[var(--border)] p-0.5 bg-[var(--color-surface-subtle)]">
                <button
                  onClick={() => setTab("events")}
                  className={`h-full min-h-0 px-4 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                    tab === "events"
                      ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                      : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                  }`}
                >
                  <Bell className="w-4 h-4 shrink-0" />
                  {t("admin.alerts.eventsTab")}
                  {summary && summary.unacknowledged > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-[rgba(var(--danger),0.2)] text-[rgb(var(--danger))]">
                      {summary.unacknowledged}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setTab("rules")}
                  className={`h-full min-h-0 px-4 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                    tab === "rules"
                      ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                      : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                  }`}
                >
                  <Shield className="w-4 h-4 shrink-0" />
                  {t("admin.alerts.rulesTab")} ({rules.length})
                </button>
              </div>
              <button
                onClick={handleCheckAlerts}
                className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[var(--color-surface-input)] transition-colors"
                title={t("admin.alerts.checkTooltip")}
              >
                <Zap className="w-4 h-4" />
                {t("admin.alerts.check")}
              </button>
              {summary && summary.unacknowledged > 0 && (
                <button
                  onClick={handleAcknowledgeAll}
                  className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg border border-[rgba(var(--warning),0.3)] text-[rgb(var(--warning))] text-sm hover:bg-[rgba(var(--warning),0.1)] transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  {t("admin.alerts.acknowledgeAll")} ({summary.unacknowledged})
                </button>
              )}
              <button
                onClick={loadData}
                className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] text-sm hover:bg-[rgba(var(--primary),0.3)] transition-colors"
              >
                <RefreshCw
                  className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
                />
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* KPI */}
      {summary && (
        <KpiGrid
          columns={4}
          items={[
            {
              label: t("admin.alerts.unacknowledged"),
              value: summary.unacknowledged,
              icon: <Bell className="w-4 h-4 text-[rgb(var(--danger))]" />,
              bgColor: "rgba(var(--danger),0.15)",
            },
            {
              label: t("admin.alerts.last24h"),
              value: summary.recent_24h,
              icon: <Activity className="w-4 h-4 text-[rgb(var(--primary))]" />,
              bgColor: "rgba(var(--primary),0.15)",
            },
            {
              label: t("admin.alerts.critical"),
              value: summary.critical,
              icon: (
                <AlertOctagon className="w-4 h-4 text-[rgb(var(--warning))]" />
              ),
              bgColor: "rgba(var(--warning),0.15)",
            },
            {
              label: t("admin.alerts.activeRules"),
              value: summary.active_rules,
              icon: <Shield className="w-4 h-4 text-[rgb(52,211,153)]" />,
              bgColor: "rgba(52,211,153,0.15)",
            },
          ]}
        />
      )}

      {/* Contenu */}
      {loading && events.length === 0 && rules.length === 0 ? (
        <AdminInlineLoading message={t("admin.alerts.loadingAlerts")} />
      ) : tab === "events" ? (
        <Card disableHover style={{ overflow: "visible" }}>
          <div className="flex items-center gap-2 mb-4">
            <Bell className="w-4 h-4 text-[rgb(var(--primary))] shrink-0" />
            <h3 className="text-lg font-semibold text-[var(--text)] m-0">
              {t("admin.alerts.eventsCardTitle")}
            </h3>
          </div>
          <Table
            data={events as unknown as Record<string, unknown>[]}
            columns={eventColumns}
            emptyMessage={t("admin.alerts.noEvents")}
            cellClassName="text-xs"
          />

          <Pagination
            mode="page"
            page={page}
            pageSize={PAGE_SIZE}
            total={eventsTotal}
            onPageChange={setPage}
            totalLabel={t("admin.alerts.events")}
          />
        </Card>
      ) : (
        <Card disableHover style={{ overflow: "visible" }}>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[rgb(var(--primary))] shrink-0" />
              <h3 className="text-lg font-semibold text-[var(--text)] m-0">
                {t("admin.alerts.rulesCardTitle")}
              </h3>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 transition-opacity w-fit"
            >
              <Plus className="w-4 h-4" />
              {t("admin.alerts.newRule")}
            </button>
          </div>
          <Table
            data={rules as unknown as Record<string, unknown>[]}
            columns={ruleColumns}
            emptyMessage={t("admin.alerts.noRules")}
            cellClassName="text-xs"
          />
        </Card>
      )}

      {/* Modal Création Règle */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={t("admin.alerts.createRuleTitle")}
        maxWidth="32rem"
      >
        <div className="space-y-4 min-w-0 overflow-x-hidden">
          <div className="min-w-0">
            <label className="block text-sm font-medium text-[var(--text)] mb-1">
              {t("admin.alerts.ruleName")}
            </label>
            <input
              type="text"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder={t("admin.alerts.ruleNamePlaceholder")}
              className="w-full min-w-0 px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-sm text-[var(--text)] transition-colors focus:outline-none focus:border-[rgba(var(--primary),0.5)] focus:ring-2 focus:ring-[rgba(var(--primary),0.1)]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4 min-w-0">
            <div className="min-w-0">
              <label className="block text-sm font-medium text-[var(--text)] mb-1">
                {t("admin.alerts.metric")}
              </label>
              <DropdownSelector
                selectedValue={formMetric}
                onChange={(value) => setFormMetric(value)}
                options={[
                  { value: "error_rate", label: t("admin.alerts.errorRate") },
                  {
                    value: "response_time",
                    label: t("admin.alerts.responseTime"),
                  },
                  { value: "error_count", label: t("admin.alerts.errorCount") },
                  {
                    value: "request_count",
                    label: t("admin.alerts.requestCount"),
                  },
                ]}
                width="100%"
              />
            </div>
            <div className="min-w-0">
              <label className="block text-sm font-medium text-[var(--text)] mb-1">
                {t("admin.alerts.condition")}
              </label>
              <div className="flex gap-2 min-w-0">
                <DropdownSelector
                  selectedValue={formCondition}
                  onChange={(value) => setFormCondition(value)}
                  options={[
                    { value: "gt", label: ">" },
                    { value: "gte", label: "≥" },
                    { value: "lt", label: "<" },
                    { value: "lte", label: "≤" },
                    { value: "eq", label: "=" },
                  ]}
                  width="5rem"
                />
                <input
                  type="number"
                  value={formThreshold}
                  onChange={(e) => setFormThreshold(Number(e.target.value))}
                  className="flex-1 min-w-0 px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-sm text-[var(--text)] transition-colors focus:outline-none focus:border-[rgba(var(--primary),0.5)] focus:ring-2 focus:ring-[rgba(var(--primary),0.1)]"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 min-w-0">
            <div className="min-w-0">
              <label className="block text-sm font-medium text-[var(--text)] mb-1">
                {t("admin.alerts.windowMinutes")}
              </label>
              <input
                type="number"
                value={formWindow}
                onChange={(e) => setFormWindow(Number(e.target.value))}
                min={1}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-sm text-[var(--text)] min-w-0 transition-colors focus:outline-none focus:border-[rgba(var(--primary),0.5)] focus:ring-2 focus:ring-[rgba(var(--primary),0.1)]"
              />
            </div>
            <div className="min-w-0">
              <label className="block text-sm font-medium text-[var(--text)] mb-1">
                {t("admin.alerts.cooldownMinutes")}
              </label>
              <input
                type="number"
                value={formCooldown}
                onChange={(e) => setFormCooldown(Number(e.target.value))}
                min={1}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-sm text-[var(--text)] min-w-0 transition-colors focus:outline-none focus:border-[rgba(var(--primary),0.5)] focus:ring-2 focus:ring-[rgba(var(--primary),0.1)]"
              />
            </div>
          </div>

          <div className="min-w-0">
            <label className="block text-sm font-medium text-[var(--text)] mb-1">
              {t("admin.alerts.serviceFilter")}
            </label>
            <input
              type="text"
              value={formService}
              onChange={(e) => setFormService(e.target.value)}
              placeholder={t("admin.alerts.serviceFilterPlaceholder")}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-sm text-[var(--text)] min-w-0 transition-colors focus:outline-none focus:border-[rgba(var(--primary),0.5)] focus:ring-2 focus:ring-[rgba(var(--primary),0.1)]"
            />
          </div>

          <Checkbox
            label={t("admin.alerts.notifyEmail")}
            checked={formNotify}
            onChange={setFormNotify}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border)]">
            <button
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text)] hover:bg-[var(--color-surface-input)] transition-colors"
            >
              {t("admin.common.cancel")}
            </button>
            <button
              onClick={handleCreateRule}
              disabled={!formName.trim() || formSubmitting}
              className="px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {formSubmitting
                ? t("admin.alerts.creating")
                : t("admin.alerts.createRule")}
            </button>
          </div>
        </div>
      </Modal>

      {/* Modal Confirmation Suppression */}
      <ConfirmModal
        isOpen={!!deleteRule}
        title={t("admin.alerts.deleteRuleTitle")}
        message={t("admin.alerts.deleteRuleMessage", {
          name: deleteRule?.name ?? "",
        })}
        confirmText={t("admin.common.delete")}
        variant="danger"
        onConfirm={handleDeleteRule}
        onClose={() => setDeleteRule(null)}
      />
    </div>
  );
}
