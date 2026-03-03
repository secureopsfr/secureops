"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import Card from "../cards/Card";
import LoadingScreen from "../LoadingScreen";
import Table from "../Table";
import { useLanguage } from "../LanguageProvider";
import {
  getScanAlertHistory,
  type ScanAlertEvent,
} from "../../services/scheduledScanService";
import { formatDate } from "../../utils/dateFormat";
import { showErrorToast } from "../../utils/toastNotifications";

export default function AlertHistoryBlock() {
  const { t } = useLanguage();
  const [alertHistory, setAlertHistory] = useState<ScanAlertEvent[]>([]);
  const [loading, setLoading] = useState(true);

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

  const alertHistoryColumns = [
    {
      key: "url" as const,
      header: t("scheduledScans.alertHistoryUrl"),
      sortable: true,
      sticky: true,
      render: (e: ScanAlertEvent) => formatUrlDisplay(e.url),
    },
    {
      key: "alert_type" as const,
      header: t("scheduledScans.alertHistoryType"),
      sortable: true,
      render: (e: ScanAlertEvent) => getAlertTypeLabel(e.alert_type),
    },
    {
      key: "email_sent" as const,
      header: t("scheduledScans.alertHistoryEmailSent"),
      sortable: true,
      render: (e: ScanAlertEvent) =>
        e.email_sent ? t("scheduledScans.yes") : t("scheduledScans.no"),
    },
    {
      key: "triggered_at" as const,
      header: t("scheduledScans.alertHistoryDate"),
      sortable: true,
      render: (e: ScanAlertEvent) => formatDate(e.triggered_at),
    },
  ];

  return (
    <Card disableHover>
      <div className="flex items-center gap-3 mb-4">
        <Bell className="w-6 h-6 text-[rgb(var(--primary))]" />
        <h2 className="text-xl font-bold text-[var(--text)]">
          {t("scheduledScans.alertHistoryTitle")}
        </h2>
      </div>
      {loading ? (
        <LoadingScreen
          variant="section"
          message={t("scheduledScans.loading")}
        />
      ) : (
        <Table<ScanAlertEvent>
          data={alertHistory}
          columns={alertHistoryColumns}
          emptyMessage={t("scheduledScans.alertHistoryEmpty")}
          defaultSort={{ key: "triggered_at", direction: "desc" }}
        />
      )}
    </Card>
  );
}
