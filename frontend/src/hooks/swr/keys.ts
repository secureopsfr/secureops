/**
 * Clés de cache SWR centralisées.
 *
 * Chaque clé est soit une constante (données fixes), soit une fonction
 * retournant un tuple incluant les paramètres de requête.
 * Cela garantit la déduplication et la révalidation ciblée.
 */

/* ─────────────────── Admin Users ─────────────────── */

export const adminUsersKey = (params: {
  search: string | null;
  plan: string | null;
  status: string | null;
  limit: number;
  offset: number;
}) => ["admin-users", params] as const;

export const ADMIN_USER_STATS_KEY = "admin-user-stats";
export const ADMIN_SUB_STATS_KEY = "admin-sub-stats";

export const adminSubHistoryKey = (limit: number) =>
  ["admin-sub-history", limit] as const;

/* ─────────────────── Admin Contacts ─────────────────── */

export const adminContactsKey = (params: {
  status: string | null;
  limit: number;
  offset: number;
}) => ["admin-contacts", params] as const;

/* ─────────────────── Admin Audit ─────────────────── */

export const adminAuditLogsKey = (params: {
  entity: string | null;
  action: string | null;
  limit: number;
  offset: number;
}) => ["admin-audit-logs", params] as const;

export const adminAuditStatsKey = (params?: Record<string, unknown>) =>
  ["admin-audit-stats", params ?? {}] as const;

/* ─────────────────── Admin Images ─────────────────── */

export const adminImagesKey = (sortBy: string, sortOrder: string) =>
  ["admin-images", sortBy, sortOrder] as const;

export const ADMIN_IMAGE_STATS_KEY = "admin-image-stats";

/* ─────────────────── Admin Templates ─────────────────── */

export const ADMIN_TEMPLATES_KEY = "admin-templates";

export const adminTemplateContentKey = (filename: string) =>
  ["admin-template-content", filename] as const;

/* ─────────────────── Admin Alerts ─────────────────── */

export const adminAlertEventsKey = (params: {
  limit: number;
  offset: number;
}) => ["admin-alert-events", params] as const;

export const ADMIN_ALERT_RULES_KEY = "admin-alert-rules";
export const ADMIN_ALERT_SUMMARY_KEY = "admin-alert-summary";

/* ─────────────────── Admin Analytics ─────────────────── */

export const adminAnalyticsKey = (windowMinutes: number | null) =>
  ["admin-analytics", windowMinutes] as const;

export const adminTimeSeriesKey = (
  windowMinutes: number | null,
  bucketMinutes: number,
) => ["admin-analytics-ts", windowMinutes, bucketMinutes] as const;

/* ─────────────────── Admin Metrics ─────────────────── */

export const adminPerfMetricsKey = (windowMinutes: number | null) =>
  ["admin-perf-metrics", windowMinutes] as const;

/* ─────────────────── Admin Emails ─────────────────── */

export const adminEmailsKey = (type: "newsletter" | "notification") =>
  ["admin-emails", type] as const;

export const adminSubscribersKey = (type: "newsletter" | "notification") =>
  ["admin-subscribers", type] as const;

/* ─────────────────── Admin Overview ─────────────────── */

export const ADMIN_OVERVIEW_KEY = "admin-overview";
