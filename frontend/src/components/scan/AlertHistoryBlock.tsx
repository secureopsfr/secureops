"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Bell, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
import LoadingScreen from "../LoadingScreen";
import { GenericButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  getScanAlertHistory,
  deleteScanAlertEvent,
  type ScanAlertEvent,
} from "../../services/scheduledScanService";
import { formatDate } from "../../utils/dateFormat";
import {
  showErrorToast,
  showSuccessToast,
} from "../../utils/toastNotifications";

export default function AlertHistoryBlock() {
  const { t } = useLanguage();
  const [items, setItems] = useState<ScanAlertEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const perPage = 10;

  const load = useCallback(
    async (pageOverride?: number) => {
      const p = pageOverride ?? page;
      setLoading(true);
      try {
        const res = await getScanAlertHistory(p, perPage);
        setItems(res.items);
        setTotal(res.total);
        if (pageOverride !== undefined) setPage(pageOverride);
      } catch {
        showErrorToast(t("scheduledScans.alertHistoryLoadError"));
      } finally {
        setLoading(false);
      }
    },
    [page, perPage, t],
  );

  useEffect(() => {
    load();
  }, [load]);

  const getAlertTypeLabel = (alertType: string) => {
    if (alertType === "regression")
      return t("scheduledScans.alertTypeRegression");
    if (alertType === "critical_finding")
      return t("scheduledScans.alertTypeCriticalFinding");
    return alertType;
  };

  const formatUrlDisplay = (url: string) =>
    url.replace(/^https?:\/\//, "").replace(/\/$/, "") || url;

  const handleDeleteClick = useCallback((id: string) => {
    setDeleteTargetId(id);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    const id = deleteTargetId;
    if (!id) return;
    setDeleteTargetId(null);
    try {
      await deleteScanAlertEvent(id);
      await load(page > 1 ? 1 : undefined);
      showSuccessToast(t("scheduledScans.alertHistoryDeleteSuccess"));
    } catch {
      showErrorToast(t("scheduledScans.alertHistoryDeleteError"));
    }
  }, [deleteTargetId, load, page, t]);

  const handleDeleteModalClose = useCallback(() => {
    setDeleteTargetId(null);
  }, []);

  const totalPages = Math.max(1, Math.ceil(total / perPage));

  return (
    <Card disableHover>
      <div className="flex items-center gap-3 mb-4">
        <Bell className="w-6 h-6 text-[rgb(var(--primary))]" />
        <h2 className="text-xl font-bold text-[var(--text)]">
          {t("scheduledScans.alertHistoryTitle")}
        </h2>
      </div>
      <div className="space-y-4">
        {loading ? (
          <LoadingScreen
            variant="section"
            message={t("scheduledScans.loading")}
          />
        ) : items.length === 0 ? (
          <p className="text-muted-theme">
            {t("scheduledScans.alertHistoryEmpty")}
          </p>
        ) : (
          <>
            <ul className="divide-y divide-[var(--color-border)]">
              {items.map((item) => (
                <li
                  key={item.id}
                  className="py-3 flex items-center justify-between gap-4"
                >
                  <div className="text-left flex-1 min-w-0">
                    <span className="font-medium text-[var(--text)] block truncate break-all">
                      {formatUrlDisplay(item.url)}
                    </span>
                    <span className="text-xs text-[var(--muted)]">
                      {formatDate(item.triggered_at)} ·{" "}
                      {getAlertTypeLabel(item.alert_type)} ·{" "}
                      {item.email_sent
                        ? t("scheduledScans.emailSent")
                        : t("scheduledScans.no")}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteClick(item.id)}
                    className="p-2 text-[var(--muted)] hover:text-[rgb(var(--danger))] shrink-0 cursor-pointer"
                    aria-label={t("scheduledScans.alertHistoryDelete")}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-2">
                <span className="text-sm text-[var(--muted)]">
                  {t("scanner.historyPageOf", { page, total: totalPages })}
                </span>
                <div className="flex gap-2">
                  <GenericButton
                    label="←"
                    variant="outline"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  />
                  <GenericButton
                    label="→"
                    variant="outline"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <ConfirmModal
        isOpen={deleteTargetId !== null}
        onClose={handleDeleteModalClose}
        onConfirm={handleDeleteConfirm}
        title={t("scheduledScans.alertHistoryDeleteModalTitle")}
        message={t("scheduledScans.alertHistoryDeleteConfirm")}
        confirmText={t("scheduledScans.alertHistoryDeleteBtn")}
        cancelText={t("common.cancel")}
        variant="danger"
        icon={Trash2}
      />
    </Card>
  );
}
