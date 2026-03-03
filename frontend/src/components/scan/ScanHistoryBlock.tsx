"use client";

import React, { useCallback, useState } from "react";
import { FileDown, History, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
import LoadingScreen from "../LoadingScreen";
import PaginationBar from "../PaginationBar";
import { IconActionButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  getScanHistory,
  getScanDetail,
  deleteScan,
  downloadScanPdf,
  type ScanHistoryItem,
} from "../../services/scanHistoryService";
import type { ScanResult } from "../../services/scanService";
import { getScoreBadge } from "./scanConstants";
import { usePaginatedFetch } from "../../hooks/usePaginatedFetch";
import { showErrorToast } from "../../utils/toastNotifications";
import { formatDate } from "../../utils/dateFormat";
import { formatUrlDisplay } from "../../utils/urlFormat";

interface ScanHistoryBlockProps {
  onSelectScan: (result: ScanResult, scanId?: string) => void;
}

export default function ScanHistoryBlock({
  onSelectScan,
}: ScanHistoryBlockProps) {
  const { t, language } = useLanguage();
  const [loadingDetailId, setLoadingDetailId] = useState<string | null>(null);
  const [pdfLoadingId, setPdfLoadingId] = useState<string | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const onError = useCallback(
    () => showErrorToast(t("scanner.historyLoadError")),
    [t],
  );
  const {
    items,
    setItems,
    total,
    setTotal,
    page,
    setPage,
    loading,
    totalPages,
  } = usePaginatedFetch<ScanHistoryItem>({
    fetchFn: (p, perPage) => getScanHistory(p, perPage),
    perPage: 10,
    onError,
  });

  const handleDeleteClick = useCallback((id: string) => {
    setDeleteTargetId(id);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    const id = deleteTargetId;
    if (!id) return;
    setDeleteTargetId(null);
    try {
      await deleteScan(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch {
      showErrorToast(t("scanner.historyDeleteError"));
    }
  }, [deleteTargetId, t]);

  const handleSelectScan = useCallback(
    async (item: ScanHistoryItem) => {
      setLoadingDetailId(item.id);
      try {
        const detail = await getScanDetail(item.id);
        const result: ScanResult = {
          url: detail.url,
          timestamp: detail.timestamp,
          duration: detail.duration,
          score: detail.score ?? 0,
          findings: detail.findings,
        };
        onSelectScan(result, detail.id);
      } catch {
        showErrorToast(t("scanner.historyLoadError"));
      } finally {
        setLoadingDetailId(null);
      }
    },
    [onSelectScan, t],
  );

  const handleDeleteModalClose = useCallback(() => {
    setDeleteTargetId(null);
  }, []);

  const handlePdfClick = useCallback(
    async (e: React.MouseEvent, item: ScanHistoryItem) => {
      e.stopPropagation();
      setPdfLoadingId(item.id);
      try {
        await downloadScanPdf(item.id, language as "fr" | "en");
      } catch {
        showErrorToast(t("scanner.exportPdfDownload") + " — erreur");
      } finally {
        setPdfLoadingId(null);
      }
    },
    [language, t],
  );

  return (
    <>
      <Card disableHover>
        <div className="flex items-center gap-3 mb-4">
          <History className="w-6 h-6 text-[rgb(var(--primary))]" />
          <h2 className="text-xl font-bold text-[var(--text)]">
            {t("scanner.historyTitle")}
          </h2>
        </div>
        <div className="space-y-4">
          {loading ? (
            <LoadingScreen
              variant="section"
              message={t("scanner.historyLoading")}
            />
          ) : items.length === 0 ? (
            <p className="text-muted-theme">{t("scanner.historyEmpty")}</p>
          ) : (
            <>
              <ul className="divide-y divide-[var(--color-border)]">
                {items.map((item) => {
                  const displayUrl =
                    item.url.replace(/^https?:\/\//, "").replace(/\/$/, "") ||
                    item.url;
                  const badge = getScoreBadge(item.score ?? 0);
                  const isLoading = loadingDetailId === item.id;
                  const isPdfLoading = pdfLoadingId === item.id;
                  return (
                    <li
                      key={item.id}
                      className="py-3 flex items-center justify-between gap-4"
                    >
                      <button
                        type="button"
                        onClick={() => handleSelectScan(item)}
                        disabled={isLoading}
                        className="text-left flex-1 min-w-0 cursor-pointer disabled:opacity-50 disabled:cursor-wait"
                      >
                        <span className="font-medium text-[var(--text)] block truncate break-all">
                          {formatUrlDisplay(item.url)}
                        </span>
                        <span className="text-xs text-[var(--muted)]">
                          {formatDate(item.created_at)} · {item.score ?? "—"}
                          /100 · {t(badge.labelKey)}
                        </span>
                      </button>
                      <div className="flex items-center gap-1 shrink-0">
                        <IconActionButton
                          icon={FileDown}
                          ariaLabel={t("scanner.exportPdfDownload")}
                          onClick={(e) => handlePdfClick(e, item)}
                          disabled={isPdfLoading}
                        />
                        <IconActionButton
                          icon={Trash2}
                          ariaLabel={t("scanner.historyDelete")}
                          onClick={() => handleDeleteClick(item.id)}
                          variant="danger"
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
              <PaginationBar
                page={page}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            </>
          )}
        </div>
      </Card>

      <ConfirmModal
        isOpen={deleteTargetId !== null}
        onClose={handleDeleteModalClose}
        onConfirm={handleDeleteConfirm}
        title={t("scanner.historyDeleteModalTitle")}
        message={t("scanner.historyDeleteConfirm")}
        confirmText={t("scanner.historyDeleteBtn")}
        cancelText={t("common.cancel")}
        variant="danger"
        icon={Trash2}
      />
    </>
  );
}
