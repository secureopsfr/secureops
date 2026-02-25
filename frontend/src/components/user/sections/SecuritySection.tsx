"use client";

import React, { useState } from "react";
import { Lock, LogOut } from "lucide-react";
import SectionSkeleton from "../SectionSkeleton";
import { GenericButton } from "../../buttons";
import { PasswordInput } from "../../inputs";
import ConfirmModal from "../../ConfirmModal";
import { useLanguage } from "../../LanguageProvider";

interface SecuritySectionProps {
  authMethod: "email" | "google";
  showChangePassword: boolean;
  setShowChangePassword: (show: boolean) => void;
  passwordData: {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
  };
  setPasswordData: (data: {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
  }) => void;
  onChangePassword: () => void;
  onSignOut: () => void;
  onSignOutAll: () => void;
  saving: boolean;
}

const SecuritySection: React.FC<SecuritySectionProps> = ({
  authMethod,
  showChangePassword,
  setShowChangePassword,
  passwordData,
  setPasswordData,
  onChangePassword,
  onSignOut,
  onSignOutAll,
  saving,
}) => {
  const { t } = useLanguage();
  const [isSignOutAllDialogOpen, setIsSignOutAllDialogOpen] = useState(false);

  const handleSignOutAllClick = () => {
    setIsSignOutAllDialogOpen(true);
  };

  const handleSignOutAllConfirm = () => {
    setIsSignOutAllDialogOpen(false);
    onSignOutAll();
  };

  return (
    <SectionSkeleton id="security" icon={Lock} title={t("security.title")}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2">
            {t("security.authMethod")}
          </label>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] rounded-full text-sm font-medium">
              {authMethod === "google"
                ? t("security.google")
                : t("security.emailPassword")}
            </span>
          </div>
        </div>

        {authMethod === "email" && (
          <div>
            {!showChangePassword ? (
              <GenericButton
                label={t("security.changePassword")}
                onClick={() => setShowChangePassword(true)}
                variant="outline"
              />
            ) : (
              <div className="space-y-4 p-4 bg-[var(--color-surface-input)] rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-[var(--text)] mb-1">
                    {t("security.currentPassword")}
                  </label>
                  <PasswordInput
                    value={passwordData.currentPassword}
                    onChange={(e) =>
                      setPasswordData({
                        ...passwordData,
                        currentPassword: e.target.value,
                      })
                    }
                    placeholder=""
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text)] mb-1">
                    {t("security.newPassword")}
                  </label>
                  <PasswordInput
                    value={passwordData.newPassword}
                    onChange={(e) =>
                      setPasswordData({
                        ...passwordData,
                        newPassword: e.target.value,
                      })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text)] mb-1">
                    {t("security.confirmPassword")}
                  </label>
                  <PasswordInput
                    value={passwordData.confirmPassword}
                    onChange={(e) =>
                      setPasswordData({
                        ...passwordData,
                        confirmPassword: e.target.value,
                      })
                    }
                  />
                </div>
                <div className="flex gap-2">
                  <GenericButton
                    label={t("security.saveBtn")}
                    onClick={onChangePassword}
                    loading={saving}
                    loadingLabel={t("security.savingBtn")}
                    disabled={saving}
                    variant="primary"
                  />
                  <GenericButton
                    label={t("security.cancelBtn")}
                    onClick={() => {
                      setShowChangePassword(false);
                      setPasswordData({
                        currentPassword: "",
                        newPassword: "",
                        confirmPassword: "",
                      });
                    }}
                    disabled={saving}
                    variant="outline"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <div className="pt-4 border-t border-[var(--border)]">
          <h3 className="text-lg font-semibold text-[var(--text)] mb-2">
            {t("security.signOutTitle")}
          </h3>
          <div className="flex flex-row flex-wrap gap-2">
            <GenericButton
              label={t("security.signOutBtn")}
              onClick={onSignOut}
              variant="primary"
              icon={<LogOut className="w-4 h-4" />}
              iconPosition="left"
            />
            <GenericButton
              label={t("security.signOutAllBtn")}
              onClick={handleSignOutAllClick}
              variant="outline"
            />
          </div>
        </div>
      </div>

      <ConfirmModal
        isOpen={isSignOutAllDialogOpen}
        onClose={() => setIsSignOutAllDialogOpen(false)}
        onConfirm={handleSignOutAllConfirm}
        title={t("security.signOutAllTitle")}
        message={t("security.signOutAllMessage")}
        confirmText={t("security.signOutAllConfirm")}
        cancelText={t("common.cancel")}
        variant="danger"
      />
    </SectionSkeleton>
  );
};

export default SecuritySection;
