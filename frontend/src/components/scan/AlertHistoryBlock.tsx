"use client";

import React, { useCallback, useState } from "react";
import { Bell, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
import LoadingScreen from "../LoadingScreen";
import PaginationBar from "../PaginationBar";
import { IconActionButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  getScanAlertHistory,
  deleteScanAlertEvent,
  type ScanAlertEvent,
} from "../../services/scheduledScanService";
import { usePaginatedFetch } from "../../hooks/usePaginatedFetch";
import { formatDate } from "../../utils/dateFormat";
import { formatUrlDisplay } from "../../utils/urlFormat";
import {
  showErrorToast,
  showSuccessToast,
} from "../../utils/toastNotifications";

export default function AlertHistoryBlock() {
  const { t } = useLanguage();
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const onError = useCallback(
    () => showErrorToast(t("scheduledScans.alertHistoryLoadError")),
    [t],
  );
  const { items, page, setPage, loading, load, totalPages } =
    usePaginatedFetch<ScanAlertEvent>({
      fetchFn: (p, perPage) => getScanAlertHistory(p, perPage),
      perPage: 10,
      onError,
    });

  const getAlertTypeLabel = (alertType: string) => {
    if (alertType === "regression")
      return t("scheduledScans.alertTypeRegression");
    if (alertType === "critical_finding")
      return t("scheduledScans.alertTypeCriticalFinding");
    return alertType;
  };

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
            <PaginationBar
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
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
