"use client";

import { useState } from "react";
import { Users, CheckCircle, Clock, Trash2 } from "lucide-react";
import { formatDateTime } from "../../../utils/dateFormat";
import Table from "../../Table";
import Badge from "../../Badge";
import Card from "../../cards/Card";
import { GenericButton } from "../../buttons";
import { AdminInlineLoading } from "../AdminSectionLoading";
import { useLanguage } from "../../LanguageProvider";

interface SubscriberRecord {
  email: string;
  is_verified?: boolean;
  created_at?: string;
  [key: string]: unknown;
}

interface SubscribersListProps {
  subscribers: SubscriberRecord[];
  loading: boolean;
  error: string | null;
  onDelete: (email: string) => void;
  onRetry: () => void;
  sending: number | string | null;
  subscribersLabel: string;
}

export default function SubscribersList({
  subscribers,
  loading,
  error,
  onDelete,
  onRetry,
  sending,
  subscribersLabel,
}: SubscribersListProps) {
  const { t } = useLanguage();
  const [showAll, setShowAll] = useState(false);

  const displayed = showAll ? subscribers : subscribers.slice(0, 10);

  return (
    <Card disableHover>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-4 h-4 text-[rgb(var(--primary))] shrink-0" />
          <h3 className="text-lg font-semibold text-[var(--text)] m-0">
            {t("admin.emails.subscribersList", { label: subscribersLabel })}
          </h3>
        </div>
        <p className="text-sm text-[var(--muted)]">
          {t("admin.emails.subscriberCount", {
            count: subscribers.length,
            label: subscribersLabel,
          })}
        </p>
      </div>

      {/* Statistiques */}
      <div className="mb-6 p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)]">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[rgba(var(--primary),0.15)]">
              <Users className="w-5 h-5 text-[rgb(var(--primary))]" />
            </div>
            <div>
              <p className="text-xs font-medium text-[var(--muted)]">
                {t("admin.common.total")}
              </p>
              <p className="text-lg font-bold text-[var(--text)]">
                {subscribers.length}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[rgba(var(--success),0.15)]">
              <CheckCircle className="w-5 h-5 text-[rgb(var(--success))]" />
            </div>
            <div>
              <p className="text-xs font-medium text-[var(--muted)]">
                {t("admin.emails.verified")}
              </p>
              <p className="text-lg font-bold text-[var(--text)]">
                {subscribers.filter((sub) => sub.is_verified).length}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[rgba(var(--warning),0.15)]">
              <Clock className="w-5 h-5 text-[rgb(var(--warning))]" />
            </div>
            <div>
              <p className="text-xs font-medium text-[var(--muted)]">
                {t("admin.emails.unverified")}
              </p>
              <p className="text-lg font-bold text-[var(--text)]">
                {subscribers.filter((sub) => !sub.is_verified).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <AdminInlineLoading message={t("admin.emails.loadingSubscribers")} />
      ) : error ? (
        <div className="p-6 text-center">
          <p className="text-[rgb(var(--danger))]">{error}</p>
          <GenericButton
            label={t("admin.common.retry")}
            onClick={onRetry}
            variant="primary"
            className="mt-4"
          />
        </div>
      ) : (
        <>
          <Table
            data={displayed}
            columns={[
              {
                key: "email",
                header: t("admin.emails.subscriberEmail"),
                render: (subscriber) => (
                  <span className="text-sm text-[var(--text)]">
                    {subscriber.email}
                  </span>
                ),
                align: "left",
                sticky: true,
              },
              {
                key: "is_verified",
                header: t("admin.emails.subscriberStatus"),
                render: (subscriber) => (
                  <Badge
                    variant={subscriber.is_verified ? "verified" : "unverified"}
                  >
                    {subscriber.is_verified
                      ? t("admin.emails.subscriberVerified")
                      : t("admin.emails.subscriberUnverified")}
                  </Badge>
                ),
                align: "left",
              },
              {
                key: "created_at",
                header: t("admin.emails.subscriberDate"),
                render: (subscriber) => (
                  <span className="text-sm text-[var(--muted)]">
                    {formatDateTime(subscriber.created_at, "N/A")}
                  </span>
                ),
                align: "left",
              },
              {
                key: "actions",
                header: t("admin.emails.colActions"),
                sortable: false,
                render: (subscriber) => (
                  <button
                    onClick={() => onDelete(subscriber.email)}
                    disabled={sending === subscriber.email}
                    className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title={t("admin.emails.deleteSubscriberTooltip")}
                  >
                    <Trash2 className="w-4 h-4 text-[rgb(var(--danger))]" />
                  </button>
                ),
                align: "center",
              },
            ]}
            emptyMessage={t("admin.emails.noSubscriberFound", {
              label: subscribersLabel,
            })}
          />
          {subscribers.length > 10 && (
            <div className="mt-6 pt-4 border-t border-[var(--border)] text-center">
              <button
                onClick={() => setShowAll(!showAll)}
                className="text-[rgb(var(--primary))] hover:text-[rgba(var(--primary),0.8)] font-medium transition-colors"
              >
                {showAll
                  ? t("admin.emails.showLess")
                  : t("admin.emails.showAll", {
                      count: subscribers.length,
                      label: subscribersLabel,
                    })}
              </button>
            </div>
          )}
        </>
      )}
    </Card>
  );
}
