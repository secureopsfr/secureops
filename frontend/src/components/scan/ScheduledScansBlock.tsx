"use client";

import React, { useCallback, useEffect, useState } from "react";
import { CalendarClock, Mail, Pause, Play, Trash2 } from "lucide-react";
import Card from "../cards/Card";
import ConfirmModal from "../ConfirmModal";
import LoadingScreen from "../LoadingScreen";
import { GenericButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import {
  getScheduledScans,
  updateScheduledScan,
  deleteScheduledScan,
  type ScheduledScan,
} from "../../services/scheduledScanService";
import { formatDateTimeShort } from "../../utils/dateFormat";
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
  const [items, setItems] = useState<ScheduledScan[]>([]);
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
        const res = await getScheduledScans(p, perPage);
        setItems(res.items);
        setTotal(res.total);
        if (pageOverride !== undefined) setPage(pageOverride);
      } catch {
        showErrorToast(t("scheduledScans.loadError"));
      } finally {
        setLoading(false);
      }
    },
    [page, perPage, t],
  );

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

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

  const totalPages = Math.max(1, Math.ceil(total / perPage));

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
                          {item.url
                            .replace(/^https?:\/\//, "")
                            .replace(/\/$/, "") || item.url}
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
                        <button
                          type="button"
                          onClick={() => handleToggleAlerts(item)}
                          className={`p-2 shrink-0 cursor-pointer ${
                            item.scan_alerts_enabled !== false
                              ? "text-[rgb(var(--primary))]"
                              : "text-[var(--muted)]"
                          }`}
                          aria-label={
                            item.scan_alerts_enabled !== false
                              ? t("scheduledScans.alertsOn")
                              : t("scheduledScans.alertsOff")
                          }
                          title={
                            item.scan_alerts_enabled !== false
                              ? t("scheduledScans.alertsOn")
                              : t("scheduledScans.alertsOff")
                          }
                        >
                          <Mail className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleEnabled(item)}
                          className="p-2 text-[var(--muted)] hover:text-[rgb(var(--primary))] shrink-0 cursor-pointer"
                          aria-label={
                            item.enabled
                              ? t("scheduledScans.pause")
                              : t("scheduledScans.resume")
                          }
                        >
                          {item.enabled ? (
                            <Pause className="w-4 h-4" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteTargetId(item.id)}
                          className="p-2 text-[var(--muted)] hover:text-[rgb(var(--danger))] shrink-0 cursor-pointer"
                          aria-label={t("scheduledScans.delete")}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
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
