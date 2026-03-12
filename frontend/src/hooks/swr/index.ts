/**
 * Export des clés SWR et des hooks SWR dédiés (admin).
 */

export * from "./keys";
export { useAdminUsers, useAdminUsersStats } from "./useAdminUsers";
export { useAdminContacts } from "./useAdminContacts";
export { useAdminAuditLogs, useAdminAuditStats } from "./useAdminAudit";
export { useAdminImages, useAdminImageStats } from "./useAdminImages";
export {
  useAdminTemplates,
  useAdminTemplateContent,
} from "./useAdminTemplates";
export {
  useAdminAlertRules,
  useAdminAlertEvents,
  useAdminAlertSummary,
} from "./useAdminAlerts";
export { useAdminEmails, useAdminSubscribers } from "./useAdminEmails";
export type { AdminEmailType } from "./useAdminEmails";
export { useAdminOverview } from "./useAdminOverview";
export type { OverviewData } from "./useAdminOverview";
