"use client";

import { useMemo } from "react";
import {
  Mail,
  Calendar,
  Bell,
  ChevronRight,
  Shield,
  UserCheck,
  UserX,
  Edit,
} from "lucide-react";
import type { UserRecord } from "../../../services/admin";
import { formatDate, formatDateTime } from "../../../utils/dateFormat";
import {
  getPlanBadgeVariant,
  getStatusBadgeVariant,
  getStatusLabel,
  BooleanIcon,
} from "../../../utils/adminHelpers";
import Badge from "../../ui/Badge";
import { useLanguage } from "../../LanguageProvider";

interface UseUserColumnsProps {
  openUserDetail: (user: UserRecord) => void;
  openGroupModal: (user: UserRecord) => void;
  openSuspendModal: (user: UserRecord) => void;
  openEditSubscription: (user: UserRecord) => void;
}

export function useUserColumns({
  openUserDetail,
  openGroupModal,
  openSuspendModal,
  openEditSubscription,
}: UseUserColumnsProps) {
  const { t } = useLanguage();
  return useMemo(
    () => [
      {
        key: "email",
        header: t("admin.users.colEmail"),
        render: (item: Record<string, unknown>) => (
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-[var(--muted)] flex-shrink-0" />
            <span
              className="text-sm text-[var(--text)] font-medium cursor-pointer hover:text-[rgb(var(--primary))] transition-colors truncate"
              onClick={() => openUserDetail(item as unknown as UserRecord)}
              title={t("admin.users.viewDetail")}
              style={{ maxWidth: "16rem" }}
            >
              {String(item.email ?? "—")}
            </span>
          </div>
        ),
        align: "left" as const,
        sticky: true,
      },
      {
        key: "plan",
        header: t("admin.users.colPlan"),
        render: (item: Record<string, unknown>) => {
          const plan = String(item.plan ?? "free");
          return (
            <Badge variant={getPlanBadgeVariant(plan)}>
              {plan.charAt(0).toUpperCase() + plan.slice(1)}
            </Badge>
          );
        },
        align: "center" as const,
      },
      {
        key: "status",
        header: t("admin.users.colStatus"),
        render: (item: Record<string, unknown>) => {
          const status = String(item.status ?? "active");
          return (
            <Badge variant={getStatusBadgeVariant(status)}>
              {getStatusLabel(status)}
            </Badge>
          );
        },
        align: "center" as const,
      },
      {
        key: "stripe_customer_id",
        header: t("admin.users.colStripe"),
        render: (item: Record<string, unknown>) => (
          <span
            className={`text-xs ${item.stripe_customer_id ? "text-[rgb(var(--success))]" : "text-[var(--muted)] opacity-40"}`}
          >
            {item.stripe_customer_id ? "✓" : "—"}
          </span>
        ),
        align: "center" as const,
      },
      {
        key: "created_at",
        header: t("admin.users.colRegisteredAt"),
        render: (item: Record<string, unknown>) => (
          <div className="flex items-center gap-2 justify-center">
            <Calendar className="h-3.5 w-3.5 text-[var(--muted)]" />
            <span className="text-xs text-[var(--muted)]">
              {formatDate(item.created_at as string | null)}
            </span>
          </div>
        ),
        align: "center" as const,
      },
      {
        key: "newsletter_enabled",
        header: t("admin.users.colNL"),
        render: (item: Record<string, unknown>) => (
          <BooleanIcon
            icon={Mail}
            enabled={!!item.newsletter_enabled}
            titleOn={t("admin.users.subscribedNewsletter")}
            titleOff={t("admin.users.notSubscribed")}
          />
        ),
        align: "center" as const,
      },
      {
        key: "notifications_enabled",
        header: t("admin.users.colNotif"),
        render: (item: Record<string, unknown>) => (
          <BooleanIcon
            icon={Bell}
            enabled={!!item.notifications_enabled}
            titleOn={t("admin.users.notificationsEnabled")}
            titleOff={t("admin.users.notificationsDisabled")}
          />
        ),
        align: "center" as const,
      },
      {
        key: "actions",
        header: t("admin.users.colActions"),
        sortable: false,
        render: (item: Record<string, unknown>) => {
          const user = item as unknown as UserRecord;
          const isSuspended = user.status === "suspended";
          return (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => openUserDetail(user)}
                className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                title={t("admin.users.viewDetail")}
              >
                <ChevronRight className="w-4 h-4 text-[rgb(var(--primary))]" />
              </button>
              <button
                onClick={() => openGroupModal(user)}
                className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                title={t("admin.users.changeRole")}
              >
                <Shield className="w-4 h-4 text-[rgb(96,165,250)]" />
              </button>
              <button
                onClick={() => openEditSubscription(user)}
                className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                title={t("admin.users.editSubscription")}
              >
                <Edit className="w-4 h-4 text-[rgb(var(--primary))]" />
              </button>
              <button
                onClick={() => openSuspendModal(user)}
                className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                title={
                  isSuspended
                    ? t("admin.users.reactivate")
                    : t("admin.users.suspend")
                }
              >
                {isSuspended ? (
                  <UserCheck className="w-4 h-4 text-[rgb(var(--success))]" />
                ) : (
                  <UserX className="w-4 h-4 text-[rgb(var(--danger))]" />
                )}
              </button>
            </div>
          );
        },
        align: "center" as const,
      },
    ],
    [openUserDetail, openGroupModal, openSuspendModal, openEditSubscription, t],
  );
}

export function useHistoryColumns() {
  const { t } = useLanguage();
  return useMemo(
    () => [
      {
        key: "email",
        header: t("admin.users.colEmail"),
        render: (item: Record<string, unknown>) => (
          <span className="text-sm text-[var(--text)] font-medium truncate">
            {String(item.email ?? "—")}
          </span>
        ),
        align: "left" as const,
        sticky: true,
      },
      {
        key: "plan",
        header: t("admin.users.colPlan"),
        render: (item: Record<string, unknown>) => {
          const plan = String(item.plan ?? "free");
          return (
            <Badge variant={getPlanBadgeVariant(plan)}>
              {plan.charAt(0).toUpperCase() + plan.slice(1)}
            </Badge>
          );
        },
        align: "center" as const,
      },
      {
        key: "status",
        header: t("admin.users.colStatus"),
        render: (item: Record<string, unknown>) => {
          const status = String(item.status ?? "active");
          return (
            <Badge variant={getStatusBadgeVariant(status)}>
              {getStatusLabel(status)}
            </Badge>
          );
        },
        align: "center" as const,
      },
      {
        key: "updated_at",
        header: t("admin.users.colDateModified"),
        render: (item: Record<string, unknown>) => (
          <span className="text-xs text-[var(--muted)]">
            {formatDateTime(item.updated_at as string | null)}
          </span>
        ),
        align: "center" as const,
      },
    ],
    [t],
  );
}
