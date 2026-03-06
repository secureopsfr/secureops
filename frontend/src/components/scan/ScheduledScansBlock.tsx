"use client";

import React, { useCallback } from "react";
import { CalendarClock, Mail, Pause, Play, Trash2 } from "lucide-react";
import { SectionCard } from "../ui/cards";
import LoadingScreen from "../LoadingScreen";
import PaginationBar from "../PaginationBar";
import { IconActionButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  getScheduledScans,
  updateScheduledScan,
  deleteScheduledScan,
  type ScheduledScan,
} from "../../services/scheduledScanService";
import { usePaginatedFetch } from "../../hooks/usePaginatedFetch";
import { useConfirmDelete } from "../../hooks/useConfirmDelete";
import { formatDateTimeShort } from "../../utils/dateFormat";
import { formatUrlDisplay } from "../../utils/urlFormat";
import {
  showErrorToast,
  showSuccessToast,
} from "../../utils/toastNotifications";

const FREQUENCY_OPTIONS = [
  { value: "daily" as const, labelKey: "scheduledScans.frequencyDaily" },
  { value: "weekly" as const, labelKey: "scheduledScans.frequencyWeekly" },
  { value: "monthly" as const, labelKey: "scheduledScans.frequencyMonthly" },
];

interface ScheduledScansBlockProps {
  refreshTrigger?: number;
}

export default function ScheduledScansBlock({
  refreshTrigger = 0,
}: ScheduledScansBlockProps) {
  const { t } = useLanguage();

  const onError = useCallback(
    () => showErrorToast(t("scheduledScans.loadError")),
    [t],
  );
  const { items, setItems, page, setPage, loading, load, totalPages } =
    usePaginatedFetch<ScheduledScan>({
      fetchFn: (p, perPage) => getScheduledScans(p, perPage),
      perPage: 10,
      onError,
      refreshTrigger,
    });

  const handleDeleteConfirm = useCallback(
    async (id: string) => {
      try {
        await deleteScheduledScan(id);
        await load(page > 1 ? 1 : undefined);
        showSuccessToast(t("scheduledScans.deleteSuccess"));
      } catch {
        showErrorToast(t("scheduledScans.deleteError"));
      }
    },
    [load, page, t],
  );

  const { openDeleteModal, ConfirmDeleteModal } = useConfirmDelete(
    handleDeleteConfirm,
    {
      title: t("scheduledScans.deleteConfirmTitle"),
      message: t("scheduledScans.deleteConfirmMessage"),
      confirmText: t("scheduledScans.deleteConfirmBtn"),
      cancelText: t("common.cancel"),
    },
  );

  const handleToggleAlerts = async (item: ScheduledScan) => {
    try {
      const updated = await updateScheduledScan(item.id, {
        scan_alerts_enabled: !item.scan_alerts_enabled,
      });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
      showSuccessToast(
        updated.scan_alerts_enabled !== false
          ? t("scheduledScans.alertsEnabled")
          : t("scheduledScans.alertsDisabled"),
      );
    } catch {
      showErrorToast(t("scheduledScans.updateError"));
    }
  };

  const handleToggleEnabled = async (item: ScheduledScan) => {
    try {
      const updated = await updateScheduledScan(item.id, {
        enabled: !item.enabled,
      });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
      showSuccessToast(
        updated.enabled
          ? t("scheduledScans.resumed")
          : t("scheduledScans.paused"),
      );
    } catch {
      showErrorToast(t("scheduledScans.updateError"));
    }
  };

  const getFrequencyLabel = (freq: string) => {
    const opt = FREQUENCY_OPTIONS.find((o) => o.value === freq);
    return opt ? t(opt.labelKey) : freq;
  };

  return (
    <>
      <SectionCard
        icon={CalendarClock}
        title={t("scheduledScans.title")}
        className="mt-6"
      >
        {loading ? (
          <LoadingScreen
            variant="section"
            message={t("scheduledScans.loading")}
          />
        ) : (
          <div className="space-y-4">
            {items.length === 0 ? (
              <p className="text-muted-theme">{t("scheduledScans.empty")}</p>
            ) : (
              <>
                <ul className="divide-y divide-[var(--color-border)]">
                  {items.map((item) => (
                    <li
                      key={item.id}
                      className="py-3 flex items-center justify-between gap-2"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-[var(--text)] truncate">
                          {formatUrlDisplay(item.url)}
                        </p>
                        <p className="text-xs text-[var(--muted)] mt-0.5">
                          {getFrequencyLabel(item.frequency)}
                          {item.enabled && (
                            <>
                              {" · "}
                              {t("scheduledScans.nextRun")}{" "}
                              {formatDateTimeShort(item.next_run_at)}
                            </>
                          )}
                        </p>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <IconActionButton
                          icon={Mail}
                          ariaLabel={
                            item.scan_alerts_enabled !== false
                              ? t("scheduledScans.alertsOn")
                              : t("scheduledScans.alertsOff")
                          }
                          onClick={() => handleToggleAlerts(item)}
                          variant={
                            item.scan_alerts_enabled !== false
                              ? "primary"
                              : "default"
                          }
                        />
                        <IconActionButton
                          icon={item.enabled ? Pause : Play}
                          ariaLabel={
                            item.enabled
                              ? t("scheduledScans.pause")
                              : t("scheduledScans.resume")
                          }
                          onClick={() => handleToggleEnabled(item)}
                        />
                        <IconActionButton
                          icon={Trash2}
                          ariaLabel={t("scheduledScans.delete")}
                          onClick={() => openDeleteModal(item.id)}
                          variant="danger"
                        />
                      </div>
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
        )}

        {ConfirmDeleteModal}
      </SectionCard>
    </>
  );
}
