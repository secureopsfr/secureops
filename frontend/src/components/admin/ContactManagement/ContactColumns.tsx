"use client";

import { useMemo } from "react";
import {
  Mail,
  User,
  FileText,
  Calendar,
  Reply,
  Trash2,
  CheckCircle,
} from "lucide-react";
import { formatDateTime } from "../../../utils/dateFormat";
import Badge from "../../Badge";
import type { ContactMessage } from "./hooks/useContactManagement";
import { useLanguage } from "../../LanguageProvider";

interface UseContactColumnsProps {
  updatingStatusId: number | null;
  handleUpdateStatus: (messageId: number, newStatus: string) => void;
  openReplyModal: (message: ContactMessage) => void;
  openDeleteModal: (message: ContactMessage) => void;
}

export function useContactColumns({
  updatingStatusId,
  handleUpdateStatus,
  openReplyModal,
  openDeleteModal,
}: UseContactColumnsProps) {
  const { t } = useLanguage();
  return useMemo(
    () => [
      {
        key: "created_at",
        header: t("admin.contact.colDate"),
        render: (message: Record<string, unknown>) => (
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-[var(--muted)]" />
            <span className="text-sm">
              {formatDateTime(message.created_at as string)}
            </span>
          </div>
        ),
        align: "left" as const,
        sticky: true,
      },
      {
        key: "first_name",
        header: t("admin.contact.colSender"),
        render: (message: Record<string, unknown>) => (
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-[var(--muted)]" />
            <span className="text-sm text-[var(--text)]">
              {String(message.first_name)} {String(message.last_name)}
            </span>
          </div>
        ),
        align: "left" as const,
      },
      {
        key: "email",
        header: t("admin.contact.colEmail"),
        render: (message: Record<string, unknown>) => (
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-[var(--muted)]" />
            <a
              href={`mailto:${message.email}`}
              className="text-sm text-[rgb(var(--primary))] hover:underline"
            >
              {String(message.email)}
            </a>
          </div>
        ),
        align: "left" as const,
      },
      {
        key: "subject",
        header: t("admin.contact.colSubject"),
        render: (message: Record<string, unknown>) => (
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-[var(--muted)]" />
            <span className="text-sm text-[var(--text)] font-medium">
              {String(message.subject)}
            </span>
          </div>
        ),
        align: "left" as const,
      },
      {
        key: "message",
        header: t("admin.contact.colMessage"),
        render: (message: Record<string, unknown>) => {
          const msg = String(message.message);
          return (
            <div className="max-w-md">
              <p className="text-sm text-[var(--muted)] line-clamp-2">
                {msg.length > 100 ? `${msg.substring(0, 100)}...` : msg}
              </p>
            </div>
          );
        },
        align: "left" as const,
      },
      {
        key: "status",
        header: t("admin.contact.colStatus"),
        render: (message: Record<string, unknown>) => {
          const status = String(message.status);
          return (
            <Badge
              variant={
                status === "pending"
                  ? "pending"
                  : status === "in_progress"
                    ? "in_progress"
                    : "processed"
              }
            >
              {status === "pending"
                ? t("admin.contact.pending")
                : status === "in_progress"
                  ? t("admin.contact.inProgress")
                  : t("admin.contact.processed")}
            </Badge>
          );
        },
        align: "center" as const,
      },
      {
        key: "actions",
        header: t("admin.contact.colActions"),
        sortable: false,
        render: (message: Record<string, unknown>) => {
          const msg = message as unknown as ContactMessage;
          const isUpdating = updatingStatusId === msg.id;
          return (
            <div className="flex items-center justify-center gap-2">
              {msg.status !== "processed" && (
                <button
                  onClick={() =>
                    handleUpdateStatus(
                      msg.id,
                      msg.status === "pending" ? "in_progress" : "processed",
                    )
                  }
                  disabled={isUpdating}
                  className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title={
                    msg.status === "pending"
                      ? t("admin.contact.markInProgress")
                      : t("admin.contact.markProcessed")
                  }
                >
                  <CheckCircle className="w-4 h-4 text-[rgb(var(--success))]" />
                </button>
              )}
              <button
                onClick={() => openReplyModal(msg)}
                className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                title={t("admin.contact.replyTooltip")}
              >
                <Reply className="w-4 h-4 text-[rgb(var(--primary))]" />
              </button>
              <button
                onClick={() => openDeleteModal(msg)}
                className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                title={t("admin.contact.deleteTooltip")}
              >
                <Trash2 className="w-4 h-4 text-[rgb(var(--danger))]" />
              </button>
              {isUpdating && (
                <div
                  className="animate-spin rounded-full h-4 w-4 border-2 border-[rgb(var(--primary))] border-t-transparent shrink-0"
                  aria-hidden
                />
              )}
            </div>
          );
        },
        align: "center" as const,
      },
    ],
    [updatingStatusId, handleUpdateStatus, openReplyModal, openDeleteModal, t],
  );
}
