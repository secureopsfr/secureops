"use client";

import React, { useCallback, useState } from "react";
import { FileDown, History, Trash2 } from "lucide-react";
import { SectionCard } from "../ui/cards";
import LoadingScreen from "../LoadingScreen";
import PaginationBar from "../PaginationBar";
import { IconActionButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  getScanHistory,
  getScanDetail,
  deleteScan,
  downloadScanPdf,
  type ScanHistoryDetail,
  type ScanHistoryItem,
  type ScanHistorySelection,
} from "../../services/scanHistoryService";
import { getScoreBadge } from "./scanConstants";
import { usePaginatedFetch } from "../../hooks/usePaginatedFetch";
import { useConfirmDelete } from "../../hooks/useConfirmDelete";
import { showErrorToast } from "../../utils/toastNotifications";
import { formatDate } from "../../utils/dateFormat";
import { formatUrlDisplay } from "../../utils/urlFormat";

interface ScanHistoryBlockProps {
  onSelectScan: (selection: ScanHistorySelection) => void;
  /** Filtre optionnel par URL (historique limité à cette URL). */
  filterUrl?: string | null;
  /** Filtre optionnel par type de scan (frontend, backend, both). */
  filterScanType?: string | null;
  /** Filtre optionnel par mode de scan (passive, intrusive, destructive, custom). */
  filterScanMode?: string | null;
  /** Filtre optionnel date de début (ISO string). */
  filterDateFrom?: string | null;
  /** Filtre optionnel date de fin (ISO string). */
  filterDateTo?: string | null;
}

export default function ScanHistoryBlock({
  onSelectScan,
  filterUrl,
  filterScanType,
  filterScanMode,
  filterDateFrom,
  filterDateTo,
}: ScanHistoryBlockProps) {
  const { t, language } = useLanguage();
  const [loadingDetailId, setLoadingDetailId] = useState<string | null>(null);
  const [pdfLoadingId, setPdfLoadingId] = useState<string | null>(null);

  const onError = useCallback(
    () => showErrorToast(t("scanner.historyLoadError")),
    [t],
  );
  const { items, setItems, setTotal, page, setPage, loading, totalPages } =
    usePaginatedFetch<ScanHistoryItem>({
      fetchFn: (p, perPage) =>
        getScanHistory(
          p,
          perPage,
          filterUrl ?? undefined,
          filterScanType ?? undefined,
          filterDateFrom ?? undefined,
          filterDateTo ?? undefined,
          filterScanMode ?? undefined,
        ),
      perPage: 10,
      onError,
      refreshTrigger: `${filterUrl ?? ""}_${filterScanType ?? ""}_${filterScanMode ?? ""}_${filterDateFrom ?? ""}_${filterDateTo ?? ""}`,
    });

  const handleDeleteConfirm = useCallback(
    async (id: string) => {
      try {
        await deleteScan(id);
        setItems((prev) => prev.filter((item) => item.id !== id));
        setTotal((prev) => Math.max(0, prev - 1));
      } catch {
        showErrorToast(t("scanner.historyDeleteError"));
      }
    },
    [setItems, setTotal, t],
  );

  const { openDeleteModal, ConfirmDeleteModal } = useConfirmDelete(
    handleDeleteConfirm,
    {
      title: t("scanner.historyDeleteModalTitle"),
      message: t("scanner.historyDeleteConfirm"),
      confirmText: t("scanner.historyDeleteBtn"),
      cancelText: t("common.cancel"),
    },
  );

  const handleSelectScan = useCallback(
    async (item: ScanHistoryItem) => {
      setLoadingDetailId(item.id);
      try {
        const detail = await getScanDetail(item.id);
        const selection = buildSelectionFromDetail(detail);
        onSelectScan(selection);
      } catch {
        showErrorToast(t("scanner.historyLoadError"));
      } finally {
        setLoadingDetailId(null);
      }
    },
    [onSelectScan, t],
  );

  const handlePdfClick = useCallback(
    async (e: React.MouseEvent, item: ScanHistoryItem) => {
      e.stopPropagation();
      setPdfLoadingId(item.id);
      try {
        await downloadScanPdf(item.id, language as "fr" | "en");
      } catch (err) {
        showErrorToast(
          err instanceof Error
            ? err.message
            : t("scanner.exportPdfDownload") + " — erreur",
        );
      } finally {
        setPdfLoadingId(null);
      }
    },
    [language, t],
  );

  return (
    <>
      <SectionCard icon={History} title={t("scanner.historyTitle")}>
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
                  const badge = getScoreBadge(item.score ?? 0);
                  const scanTypeKey =
                    item.scan_type === "backend"
                      ? "scanner.scanTypeBackend"
                      : "scanner.scanTypeFrontend";
                  const scanModeKey =
                    item.scan_mode === "intrusive"
                      ? "scanner.modeIntrusive"
                      : item.scan_mode === "destructive"
                        ? "scanner.modeDestructive"
                        : item.scan_mode === "custom"
                          ? "scanner.modeCustom"
                          : "scanner.modePassive";
                  const isLoading = loadingDetailId === item.id;
                  const isPdfLoading = pdfLoadingId === item.id;
                  const modeKey =
                    item.result_mode === "multi"
                      ? "scanner.scanResultModeMulti"
                      : "scanner.scanResultModeSingle";
                  const modeBadgeClass =
                    item.result_mode === "multi"
                      ? "bg-[rgba(14,165,233,0.22)] text-white/70 border border-[rgba(14,165,233,0.40)]"
                      : "bg-[rgba(168,85,247,0.22)] text-white/70 border border-[rgba(168,85,247,0.40)]";
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
                          {!filterScanMode && (
                            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-[rgba(16,185,129,0.18)] text-[rgb(16,185,129)] mr-1">
                              {t(scanModeKey)}
                            </span>
                          )}
                          <span
                            className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium mr-1 ${modeBadgeClass}`}
                          >
                            {t(modeKey)}
                          </span>
                          {!filterScanType && (
                            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-[rgba(var(--primary),0.12)] text-[rgb(var(--primary))] mr-1">
                              {t(scanTypeKey)}
                            </span>
                          )}
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
                          onClick={() => openDeleteModal(item.id)}
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
      </SectionCard>

      {ConfirmDeleteModal}
    </>
  );
}

function buildSelectionFromDetail(
  detail: ScanHistoryDetail,
): ScanHistorySelection {
  if (detail.result_mode === "multi") {
    return {
      result_mode: "multi",
      scan_id: detail.id,
      result: {
        result_mode: "multi",
        base_url: detail.url,
        urls: Array.isArray(detail.urls) ? detail.urls : [],
        score_global: detail.score ?? 0,
        page_results: Array.isArray(detail.page_results)
          ? detail.page_results
          : [],
        timestamp: detail.timestamp,
        duration: detail.duration,
        scan_type: detail.scan_type ?? "frontend",
        scan_mode: detail.scan_mode ?? "passive",
        status: detail.status ?? "success",
      },
    };
  }

  return {
    result_mode: "single",
    scan_id: detail.id,
    result: {
      url: detail.url,
      timestamp: detail.timestamp,
      duration: detail.duration,
      score: detail.score ?? 0,
      scan_mode: detail.scan_mode ?? "passive",
      findings: detail.findings,
      category_summaries: detail.category_summaries,
      total_tests_count: detail.total_tests_count,
    },
  };
}
