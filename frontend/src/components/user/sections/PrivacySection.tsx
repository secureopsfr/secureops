"use client";

import React, { useState } from "react";
import { Shield, Download, Trash2 } from "lucide-react";
import SectionSkeleton from "../SectionSkeleton";
import ConfirmModal from "../../ConfirmModal";
import { GenericButton } from "../../buttons";
import { useLanguage } from "../../LanguageProvider";

interface PrivacySectionProps {
  onExportData: () => void;
  onDeleteAccount: () => void;
  onDeleteHistory: () => void;
}

const PrivacySection: React.FC<PrivacySectionProps> = ({
  onExportData,
  onDeleteAccount,
  onDeleteHistory,
}) => {
  const { t } = useLanguage();
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleteHistoryDialogOpen, setIsDeleteHistoryDialogOpen] =
    useState(false);

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
            {t("privacy.favoritesTitle")}
          </h3>
          <p className="text-sm text-[var(--muted)] mb-3">
            {t("privacy.favoritesDesc")}
          </p>
          <GenericButton
            label={t("privacy.deleteFavoritesBtn")}
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
        title={t("privacy.deleteFavoritesModalTitle")}
        message={t("privacy.deleteFavoritesModalMessage")}
        confirmText={t("privacy.deleteFavoritesConfirm")}
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
