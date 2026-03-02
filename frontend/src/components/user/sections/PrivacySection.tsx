"use client";

import React, { useState } from "react";
import { Shield, Download, Trash2 } from "lucide-react";
import SectionSkeleton from "../SectionSkeleton";
import ConfirmModal from "../../ConfirmModal";
import { DropdownSelector, GenericButton } from "../../buttons";
import { useLanguage } from "../../LanguageProvider";

const RETENTION_OPTIONS = [
  { value: "none", labelKey: "privacy.retentionNone" },
  { value: "7", labelKey: "privacy.retention7" },
  { value: "30", labelKey: "privacy.retention30" },
  { value: "90", labelKey: "privacy.retention90" },
  { value: "365", labelKey: "privacy.retention365" },
] as const;

const RETENTION_ORDER: Record<string, number> = {
  none: 0,
  "7": 7,
  "30": 30,
  "90": 90,
  "365": 365,
};

function willReduceRetention(newVal: string, currentVal: string): boolean {
  return (
    RETENTION_ORDER[newVal] < RETENTION_ORDER[currentVal] || newVal === "none"
  );
}

interface PrivacySectionProps {
  onExportData: () => void;
  onDeleteAccount: () => void;
  onDeleteHistory: () => void;
  historyRetention: string;
  onHistoryRetentionChange: (value: string) => void;
}

const PrivacySection: React.FC<PrivacySectionProps> = ({
  onExportData,
  onDeleteAccount,
  onDeleteHistory,
  historyRetention,
  onHistoryRetentionChange,
}) => {
  const { t } = useLanguage();
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleteHistoryDialogOpen, setIsDeleteHistoryDialogOpen] =
    useState(false);
  const [pendingRetention, setPendingRetention] = useState<string | null>(null);

  const handleDeleteClick = () => {
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    onDeleteAccount();
  };

  const handleDeleteHistoryClick = () => {
    setIsDeleteHistoryDialogOpen(true);
  };

  const handleDeleteHistoryConfirm = () => {
    onDeleteHistory();
  };

  const handleRetentionChange = (value: string) => {
    const current = historyRetention || "30";
    if (willReduceRetention(value, current)) {
      setPendingRetention(value);
    } else {
      onHistoryRetentionChange(value);
    }
  };

  const handleRetentionConfirm = () => {
    if (pendingRetention !== null) {
      onHistoryRetentionChange(pendingRetention);
      setPendingRetention(null);
    }
  };

  const handleRetentionModalClose = () => {
    setPendingRetention(null);
  };

  return (
    <SectionSkeleton id="privacy" icon={Shield} title={t("privacy.title")}>
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-[var(--text)] mb-2">
            {t("privacy.downloadTitle")}
          </h3>
          <p className="text-sm text-[var(--muted)] mb-3">
            {t("privacy.downloadDesc")}
          </p>
          <GenericButton
            label={t("privacy.downloadBtn")}
            onClick={onExportData}
            variant="outline"
            icon={<Download className="w-4 h-4" />}
            iconPosition="left"
          />
        </div>

        <div className="pt-4 border-t border-[var(--border)]">
          <h3 className="text-lg font-semibold text-[var(--text)] mb-2">
            {t("privacy.retentionTitle")}
          </h3>
          <p className="text-sm text-[var(--muted)] mb-3">
            {t("privacy.retentionDesc")}
          </p>
          <DropdownSelector
            selectedValue={historyRetention || "30"}
            onChange={handleRetentionChange}
            options={RETENTION_OPTIONS.map((opt) => ({
              value: opt.value,
              label: t(opt.labelKey),
            }))}
            width="100%"
            className="max-w-xs"
          />
        </div>

        <div className="pt-4 border-t border-[var(--border)]">
          <h3 className="text-lg font-semibold text-[var(--text)] mb-2">
            {t("privacy.historyTitle")}
          </h3>
          <p className="text-sm text-[var(--muted)] mb-3">
            {t("privacy.historyDesc")}
          </p>
          <GenericButton
            label={t("privacy.deleteHistoryBtn")}
            onClick={handleDeleteHistoryClick}
            variant="outline"
            icon={<Trash2 className="w-4 h-4" />}
            iconPosition="left"
          />
        </div>

        <div className="pt-4 border-t border-[var(--border)]">
          <h3 className="text-lg font-semibold text-[rgb(var(--danger))] mb-2">
            {t("privacy.dangerZone")}
          </h3>
          <p className="text-sm text-[var(--muted)] mb-4">
            {t("privacy.deleteAccountDesc")}
          </p>
          <GenericButton
            label={t("privacy.deleteAccountBtn")}
            onClick={handleDeleteClick}
            variant="danger"
            icon={<Trash2 className="w-4 h-4" />}
            iconPosition="left"
          />
        </div>
      </div>

      <ConfirmModal
        isOpen={isDeleteHistoryDialogOpen}
        onClose={() => setIsDeleteHistoryDialogOpen(false)}
        onConfirm={handleDeleteHistoryConfirm}
        title={t("privacy.deleteHistoryModalTitle")}
        message={t("privacy.deleteHistoryModalMessage")}
        confirmText={t("privacy.deleteHistoryConfirm")}
        cancelText={t("common.cancel")}
        variant="danger"
      />

      <ConfirmModal
        isOpen={pendingRetention !== null}
        onClose={handleRetentionModalClose}
        onConfirm={handleRetentionConfirm}
        title={t("privacy.retentionModalTitle")}
        message={t("privacy.retentionModalMessage")}
        confirmText={t("privacy.retentionConfirm")}
        cancelText={t("common.cancel")}
        variant="danger"
      />

      <ConfirmModal
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        title={t("privacy.deleteAccountModalTitle")}
        message={t("privacy.deleteAccountModalMessage")}
        confirmText={t("privacy.deleteAccountConfirm")}
        cancelText={t("common.cancel")}
        variant="danger"
        confirmationText={t("privacy.deleteConfirmationText")}
      />
    </SectionSkeleton>
  );
};

export default PrivacySection;
