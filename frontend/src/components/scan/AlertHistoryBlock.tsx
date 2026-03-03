"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Bell, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
import LoadingScreen from "../LoadingScreen";
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
  const [alertHistory, setAlertHistory] = useState<ScanAlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const history = await getScanAlertHistory();
      setAlertHistory(history);
    } catch {
      showErrorToast(t("scheduledScans.alertHistoryLoadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

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

  const sortedItems = useMemo(
    () =>
      [...alertHistory].sort(
        (a, b) =>
          new Date(b.triggered_at).getTime() -
          new Date(a.triggered_at).getTime(),
      ),
    [alertHistory],
  );

  const handleDeleteClick = useCallback((id: string) => {
    setDeleteTargetId(id);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    const id = deleteTargetId;
    if (!id) return;
    setDeleteTargetId(null);
    try {
      await deleteScanAlertEvent(id);
      setAlertHistory((prev) => prev.filter((e) => e.id !== id));
      showSuccessToast(t("scheduledScans.alertHistoryDeleteSuccess"));
    } catch {
      showErrorToast(t("scheduledScans.alertHistoryDeleteError"));
    }
  }, [deleteTargetId, t]);

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
        ) : sortedItems.length === 0 ? (
          <p className="text-muted-theme">
            {t("scheduledScans.alertHistoryEmpty")}
          </p>
        ) : (
          <ul className="divide-y divide-[var(--color-border)]">
            {sortedItems.map((item) => (
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
