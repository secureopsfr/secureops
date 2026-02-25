"use client";

import React from "react";
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  UserX,
  Mail,
  Calendar,
  CreditCard,
  Bell,
  Edit,
} from "lucide-react";
import type { UserRecord } from "../../services/admin";
import { formatDate, formatDateTime } from "../../utils/dateFormat";
import {
  getPlanBadgeVariant,
  getStatusBadgeVariant,
  getStatusLabel,
} from "../../utils/adminHelpers";
import { GenericButton } from "../buttons";
import Badge from "../Badge";
import type { BadgeVariant } from "../Badge";
import Modal from "../Modal";
import LoadingScreen from "../LoadingScreen";
import { useLanguage } from "../LanguageProvider";

/* ─────────── Helpers locaux (spécifiques au détail) ─────────── */

function DetailField({
  icon: Icon,
  iconColor = "text-[var(--muted)]",
  label,
  children,
  align = "center",
}: {
  icon: React.ComponentType<{ className?: string }>;
  iconColor?: string;
  label: string;
  children: React.ReactNode;
  align?: "center" | "start";
}) {
  return (
    <div className={`flex items-${align} gap-3`}>
      <Icon
        className={`w-5 h-5 ${iconColor} ${align === "start" ? "mt-0.5" : ""}`}
      />
      <div>
        <p className="text-xs text-[var(--muted)] uppercase tracking-wider">
          {label}
        </p>
        {children}
      </div>
    </div>
  );
}

function BooleanIndicator({
  icon: Icon,
  enabled,
  labelOn,
  labelOff,
}: {
  icon: React.ComponentType<{ className?: string }>;
  enabled: boolean;
  labelOn: string;
  labelOff: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <Icon
        className={`w-4 h-4 ${enabled ? "text-[rgb(var(--success))]" : "text-[var(--muted)] opacity-30"}`}
      />
      <span className="text-sm text-[var(--text)]">
        {enabled ? labelOn : labelOff}
      </span>
    </div>
  );
}

function getGroupIcon(group: string) {
  switch (group) {
    case "admin":
      return <ShieldAlert className="w-3.5 h-3.5" />;
    case "beta":
      return <ShieldCheck className="w-3.5 h-3.5" />;
    default:
      return <Shield className="w-3.5 h-3.5" />;
  }
}

function getGroupBadgeVariant(group: string): BadgeVariant {
  switch (group) {
    case "admin":
      return "error";
    case "beta":
      return "info";
    default:
      return "default";
  }
}

/* ─────────── Composant ─────────── */

interface UserDetailModalProps {
  isOpen: boolean;
  loading: boolean;
  user: UserRecord | null;
  onClose: () => void;
  onOpenGroupModal: (user: UserRecord) => void;
  onOpenSuspendModal: (user: UserRecord) => void;
  onOpenEditSubscription: (user: UserRecord) => void;
}

export default function UserDetailModal({
  isOpen,
  loading,
  user,
  onClose,
  onOpenGroupModal,
  onOpenSuspendModal,
  onOpenEditSubscription,
}: UserDetailModalProps) {
  const { t } = useLanguage();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("admin.userDetail.title")}
      maxWidth="600px"
    >
      {loading ? (
        <LoadingScreen
          variant="section"
          message={t("admin.userDetail.loading")}
        />
      ) : user ? (
        <div className="space-y-5">
          {/* Email */}
          <DetailField
            icon={Mail}
            iconColor="text-[rgb(var(--primary))]"
            label={t("admin.userDetail.email")}
          >
            <p className="text-sm font-medium text-[var(--text)]">
              {user.email}
            </p>
          </DetailField>

          {/* Cognito Sub */}
          <DetailField icon={Shield} label={t("admin.userDetail.cognitoSub")}>
            <p className="text-xs font-mono text-[var(--muted)]">
              {user.cognito_sub}
            </p>
          </DetailField>

          {/* Groupes Cognito */}
          {user.cognito_groups && (
            <DetailField
              icon={ShieldCheck}
              iconColor="text-[rgb(96,165,250)]"
              label={t("admin.userDetail.rolesGroups")}
              align="start"
            >
              <div className="flex flex-wrap gap-2 mt-1">
                {user.cognito_groups.length > 0 ? (
                  user.cognito_groups.map((group) => (
                    <Badge key={group} variant={getGroupBadgeVariant(group)}>
                      <span className="flex items-center gap-1">
                        {getGroupIcon(group)}
                        {group}
                      </span>
                    </Badge>
                  ))
                ) : (
                  <Badge variant="default">
                    <span className="flex items-center gap-1">
                      <Shield className="w-3.5 h-3.5" />
                      user
                    </span>
                  </Badge>
                )}
              </div>
            </DetailField>
          )}

          {/* Plan et Statut */}
          <div className="grid grid-cols-2 gap-4">
            <DetailField
              icon={CreditCard}
              iconColor="text-[rgb(var(--warning))]"
              label={t("admin.userDetail.plan")}
            >
              <Badge variant={getPlanBadgeVariant(user.plan)}>
                {user.plan.charAt(0).toUpperCase() + user.plan.slice(1)}
              </Badge>
            </DetailField>
            <DetailField
              icon={UserCheck}
              iconColor="text-[rgb(52,211,153)]"
              label={t("admin.userDetail.status")}
            >
              <Badge variant={getStatusBadgeVariant(user.status)}>
                {getStatusLabel(user.status)}
              </Badge>
            </DetailField>
          </div>

          {/* Cognito Status & Enabled */}
          {user.cognito_status && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-[var(--muted)] uppercase tracking-wider">
                  {t("admin.userDetail.cognitoStatus")}
                </p>
                <p className="text-sm text-[var(--text)]">
                  {user.cognito_status}
                </p>
              </div>
              <div>
                <p className="text-xs text-[var(--muted)] uppercase tracking-wider">
                  {t("admin.userDetail.accountActive")}
                </p>
                <Badge variant={user.cognito_enabled ? "success" : "error"}>
                  {user.cognito_enabled
                    ? t("admin.userDetail.yes")
                    : t("admin.userDetail.no")}
                </Badge>
              </div>
            </div>
          )}

          {/* Dates */}
          <div className="grid grid-cols-2 gap-4">
            <DetailField
              icon={Calendar}
              label={t("admin.userDetail.registeredAt")}
            >
              <p className="text-sm text-[var(--text)]">
                {formatDateTime(user.created_at)}
              </p>
            </DetailField>
            {user.current_period_end && (
              <DetailField
                icon={Calendar}
                label={t("admin.userDetail.periodEnd")}
              >
                <p className="text-sm text-[var(--text)]">
                  {formatDate(user.current_period_end)}
                </p>
              </DetailField>
            )}
          </div>

          {/* Stripe */}
          {user.stripe_customer_id && (
            <DetailField
              icon={CreditCard}
              label={t("admin.userDetail.stripeCustomer")}
            >
              <p className="text-xs font-mono text-[var(--muted)]">
                {user.stripe_customer_id}
              </p>
            </DetailField>
          )}

          {/* Abonnements */}
          <div className="flex items-center gap-4 pt-2 border-t border-[var(--border)]">
            <BooleanIndicator
              icon={Mail}
              enabled={user.newsletter_enabled}
              labelOn={t("admin.userDetail.newsletterYes")}
              labelOff={t("admin.userDetail.newsletterNo")}
            />
            <BooleanIndicator
              icon={Bell}
              enabled={user.notifications_enabled}
              labelOn={t("admin.userDetail.notificationsYes")}
              labelOff={t("admin.userDetail.notificationsNo")}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-4 border-t border-[var(--border)] flex-wrap">
            <GenericButton
              label={t("admin.userDetail.changeRole")}
              onClick={() => {
                onClose();
                onOpenGroupModal(user);
              }}
              variant="secondary"
              icon={<Shield className="w-4 h-4" />}
              iconPosition="left"
            />
            <GenericButton
              label={t("admin.userDetail.editSubscription")}
              onClick={() => {
                onClose();
                onOpenEditSubscription(user);
              }}
              variant="secondary"
              icon={<Edit className="w-4 h-4" />}
              iconPosition="left"
            />
            <GenericButton
              label={
                user.status === "suspended"
                  ? t("admin.userDetail.reactivate")
                  : t("admin.userDetail.suspend")
              }
              onClick={() => {
                onClose();
                onOpenSuspendModal(user);
              }}
              variant={user.status === "suspended" ? "primary" : "danger"}
              icon={
                user.status === "suspended" ? (
                  <UserCheck className="w-4 h-4" />
                ) : (
                  <UserX className="w-4 h-4" />
                )
              }
              iconPosition="left"
            />
          </div>
        </div>
      ) : null}
    </Modal>
  );
}
