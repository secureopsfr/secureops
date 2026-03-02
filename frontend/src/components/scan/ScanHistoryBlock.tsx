"use client";

import React, { useCallback, useEffect, useState } from "react";
import { History, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
import LoadingScreen from "../LoadingScreen";
import { GenericButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  getScanHistory,
  getScanDetail,
  deleteScan,
  type ScanHistoryItem,
} from "../../services/scanHistoryService";
import type { ScanResult } from "../../services/scanService";
import { getScoreBadge } from "./scanConstants";
import { showErrorToast } from "../../utils/toastNotifications";
import { formatDate } from "../../utils/dateFormat";

interface ScanHistoryBlockProps {
  onSelectScan: (result: ScanResult, scanId?: string) => void;
}

export default function ScanHistoryBlock({
  onSelectScan,
}: ScanHistoryBlockProps) {
  const { t } = useLanguage();
  const [items, setItems] = useState<ScanHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingDetailId, setLoadingDetailId] = useState<string | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const perPage = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getScanHistory(page, perPage);
      setItems(res.items);
      setTotal(res.total);
    } catch {
      showErrorToast(t("scanner.historyLoadError"));
    } finally {
      setLoading(false);
    }
  }, [page, t]);

  useEffect(() => {
    load();
  }, [load]);

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

  const totalPages = Math.max(1, Math.ceil(total / perPage));

  return (
    <>
      <Card disableHover className="mt-6">
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
                          {displayUrl}
                        </span>
                        <span className="text-xs text-[var(--muted)]">
                          {formatDate(item.created_at)} · {item.score ?? "—"}
                          /100 · {t(badge.labelKey)}
                        </span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteClick(item.id)}
                        className="p-2 text-[var(--muted)] hover:text-[rgb(var(--danger))] shrink-0 cursor-pointer"
                        aria-label={t("scanner.historyDelete")}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </li>
                  );
                })}
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
                      onClick={() =>
                        setPage((p) => Math.min(totalPages, p + 1))
                      }
                      disabled={page >= totalPages}
                    />
                  </div>
                </div>
              )}
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
