"use client";

import React, { useCallback } from "react";
import { Bell, Trash2 } from "lucide-react";
import { SectionCard } from "../ui/cards";
import LoadingScreen from "../LoadingScreen";
import PaginationBar from "../PaginationBar";
import { useLanguage } from "../LanguageProvider";
import {
  getScanAlertHistory,
  deleteScanAlertEvent,
  type ScanAlertEvent,
} from "../../services/scheduledScanService";
import { usePaginatedFetch } from "../../hooks/usePaginatedFetch";
import { useConfirmDelete } from "../../hooks/useConfirmDelete";
import { formatDate } from "../../utils/dateFormat";
import { formatUrlDisplay } from "../../utils/urlFormat";
import {
  showErrorToast,
  showSuccessToast,
} from "../../utils/toastNotifications";

export default function AlertHistoryBlock() {
  const { t } = useLanguage();

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

  const handleDeleteConfirm = useCallback(
    async (id: string) => {
      try {
        await deleteScanAlertEvent(id);
        await load(page > 1 ? 1 : undefined);
        showSuccessToast(t("scheduledScans.alertHistoryDeleteSuccess"));
      } catch {
        showErrorToast(t("scheduledScans.alertHistoryDeleteError"));
      }
    },
    [load, page, t],
  );

  const { openDeleteModal, ConfirmDeleteModal } = useConfirmDelete(
    handleDeleteConfirm,
    {
      title: t("scheduledScans.alertHistoryDeleteModalTitle"),
      message: t("scheduledScans.alertHistoryDeleteConfirm"),
      confirmText: t("scheduledScans.alertHistoryDeleteBtn"),
      cancelText: t("common.cancel"),
    },
  );

  const getAlertTypeLabel = (alertType: string) => {
    if (alertType === "regression")
      return t("scheduledScans.alertTypeRegression");
    if (alertType === "critical_finding")
      return t("scheduledScans.alertTypeCriticalFinding");
    return alertType;
  };

  const getScanTypeLabel = (scanType: string) => {
    if (scanType === "backend") return t("scanner.scanTypeBackend");
    if (scanType === "custom") return t("scanner.scanTypeCustom");
    return t("scanner.scanTypeFrontend");
  };

  return (
    <SectionCard icon={Bell} title={t("scheduledScans.alertHistoryTitle")}>
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
                      <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-[rgba(var(--primary),0.12)] text-[rgb(var(--primary))] mr-1">
                        {getScanTypeLabel(item.scan_type ?? "frontend")}
                      </span>
                      {formatDate(item.triggered_at)} ·{" "}
                      {getAlertTypeLabel(item.alert_type)} ·{" "}
                      {item.email_sent
                        ? t("scheduledScans.emailSent")
                        : t("scheduledScans.no")}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => openDeleteModal(item.id)}
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

      {ConfirmDeleteModal}
    </SectionCard>
  );
}
