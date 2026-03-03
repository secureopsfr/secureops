"use client";

import React, { useCallback, useState } from "react";
import { CalendarClock, Mail, Pause, Play, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
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
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

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

  const handleDeleteConfirm = async () => {
    const id = deleteTargetId;
    if (!id) return;
    setDeleteTargetId(null);
    try {
      await deleteScheduledScan(id);
      await load(page > 1 ? 1 : undefined);
      showSuccessToast(t("scheduledScans.deleteSuccess"));
    } catch {
      showErrorToast(t("scheduledScans.deleteError"));
    }
  };

  const getFrequencyLabel = (freq: string) => {
    const opt = FREQUENCY_OPTIONS.find((o) => o.value === freq);
    return opt ? t(opt.labelKey) : freq;
  };

  return (
    <>
      <Card disableHover className="mt-6">
        <div className="flex items-center gap-3 mb-4">
          <CalendarClock className="w-6 h-6 text-[rgb(var(--primary))]" />
          <h2 className="text-xl font-bold text-[var(--text)]">
            {t("scheduledScans.title")}
          </h2>
        </div>

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
                          onClick={() => setDeleteTargetId(item.id)}
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

        <ConfirmModal
          isOpen={deleteTargetId !== null}
          onClose={() => setDeleteTargetId(null)}
          onConfirm={handleDeleteConfirm}
          title={t("scheduledScans.deleteConfirmTitle")}
          message={t("scheduledScans.deleteConfirmMessage")}
          confirmText={t("scheduledScans.deleteConfirmBtn")}
        />
      </Card>
    </>
  );
}
