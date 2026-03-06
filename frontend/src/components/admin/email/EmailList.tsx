"use client";

import { Clock, Send, Edit, Trash2, X, History } from "lucide-react";
import { formatDateTime } from "../../../utils/dateFormat";
import Table from "../../Table";
import Badge, { BadgeVariant } from "../../ui/Badge";
import Card from "../../ui/cards/Card";
import { AdminInlineLoading } from "../AdminSectionLoading";
import { useLanguage } from "../../LanguageProvider";

interface EmailRecord {
  id: number;
  subject: string;
  content: string;
  status?: string;
  created_at?: string;
  sent_at?: string;
  scheduled_at?: string;
  recipients_count?: number;
  template_name?: string;
  [key: string]: unknown;
}

interface EmailListProps {
  emails: EmailRecord[];
  loading: boolean;
  onEdit: (email: EmailRecord) => void;
  onDelete: (emailId: number) => void;
  onSend: (email: EmailRecord) => void;
  onCancelSchedule: (emailId: number) => void;
  sending: number | string | null;
  subscribersLabel: string;
  emailLabel: string;
  /** Si fourni, remplace l’en-tête par défaut (titre history + sent and draft) */
  headerSlot?: React.ReactNode;
}

export default function EmailList({
  emails,
  loading,
  onEdit,
  onDelete,
  onSend,
  onCancelSchedule,
  sending,
  subscribersLabel,
  emailLabel,
  headerSlot,
}: EmailListProps) {
  const { t } = useLanguage();

  const STATUS_LABELS: Record<string, string> = {
    draft: t("admin.emails.draft"),
    sent: t("admin.emails.sent"),
    failed: t("admin.emails.failed"),
    scheduled: t("admin.emails.scheduled"),
  };

  return (
    <Card disableHover>
      <div className="mb-6">
        {headerSlot ?? (
          <>
            <div className="flex items-center gap-3 mb-2">
              <History className="w-4 h-4 text-[rgb(var(--primary))] shrink-0" />
              <h3 className="text-lg font-semibold text-[var(--text)] m-0">
                {t("admin.emails.history", { label: emailLabel })}
              </h3>
            </div>
            <p className="text-sm text-[var(--muted)]">
              {t("admin.emails.sentAndDraft", {
                label: emailLabel.charAt(0).toUpperCase() + emailLabel.slice(1),
              })}
            </p>
          </>
        )}
      </div>

      {loading && emails.length === 0 ? (
        <AdminInlineLoading message={t("admin.emails.loadingEmails")} />
      ) : (
        <Table
          data={emails}
          columns={[
            {
              key: "subject",
              header: t("admin.emails.colSubject"),
              render: (email) => (
                <div
                  className="text-sm font-medium text-[var(--text)] max-w-[250px] overflow-hidden text-ellipsis whitespace-nowrap"
                  title={email.subject as string}
                >
                  {email.subject}
                </div>
              ),
              align: "left",
              sticky: true,
            },
            {
              key: "status",
              header: t("admin.emails.colStatus"),
              render: (email) => {
                const statusVariant: BadgeVariant =
                  email.status === "sent"
                    ? "success"
                    : email.status === "failed"
                      ? "error"
                      : email.status === "scheduled"
                        ? "warning"
                        : "default";
                return (
                  <div className="flex flex-col items-center gap-1">
                    <Badge variant={statusVariant}>
                      {STATUS_LABELS[email.status ?? "draft"] ||
                        t("admin.emails.draft")}
                    </Badge>
                    {email.status === "scheduled" && email.scheduled_at && (
                      <span className="text-xs flex items-center gap-1 text-[rgb(var(--warning))]">
                        <Clock className="w-3 h-3" />
                        {new Date(email.scheduled_at).toLocaleString(
                          t("locale"),
                          {
                            day: "numeric",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          },
                        )}
                      </span>
                    )}
                  </div>
                );
              },
              align: "left",
            },
            {
              key: "recipients_count",
              header: t("admin.emails.colRecipients"),
              render: (email) => (
                <span className="text-sm text-[var(--text)]">
                  {email.recipients_count || 0} {subscribersLabel}
                </span>
              ),
              align: "left",
            },
            {
              key: "created_at",
              header: t("admin.emails.colDate"),
              sortValue: (email) => email.sent_at || email.created_at || "",
              render: (email) => (
                <span className="text-sm text-[var(--muted)]">
                  {formatDateTime(email.sent_at || email.created_at, "N/A")}
                </span>
              ),
              align: "left",
            },
            {
              key: "actions",
              header: t("admin.emails.colActions"),
              sortable: false,
              render: (email) => (
                <div className="flex items-center justify-center gap-2">
                  {email.status !== "sent" && (
                    <button
                      onClick={() => onEdit(email)}
                      disabled={sending === email.id}
                      className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title={t("admin.emails.editTooltip", {
                        label: emailLabel,
                      })}
                    >
                      <Edit className="w-4 h-4 text-[rgb(var(--primary))]" />
                    </button>
                  )}
                  {(email.status === "draft" ||
                    email.status === "scheduled") && (
                    <button
                      onClick={() => onSend(email)}
                      disabled={sending === email.id}
                      className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title={t("admin.emails.sendTooltip", {
                        label: emailLabel,
                      })}
                    >
                      <Send className="w-4 h-4 text-[rgb(var(--success))]" />
                    </button>
                  )}
                  {email.status === "scheduled" && (
                    <button
                      onClick={() => onCancelSchedule(email.id)}
                      disabled={sending === email.id}
                      className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title={t("admin.emails.cancelSchedule")}
                    >
                      <X className="w-4 h-4 text-[rgb(var(--warning))]" />
                    </button>
                  )}
                  <button
                    onClick={() => onDelete(email.id)}
                    disabled={sending === email.id}
                    className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title={t("admin.emails.deleteTooltip", {
                      label: emailLabel,
                    })}
                  >
                    <Trash2 className="w-4 h-4 text-[rgb(var(--danger))]" />
                  </button>
                </div>
              ),
              align: "center",
            },
          ]}
          emptyMessage={t("admin.emails.noEmailFound", { label: emailLabel })}
        />
      )}
    </Card>
  );
}
