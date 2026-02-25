"use client";

import Image from "next/image";
import { GenericButton } from "../../../components/buttons";
import { PasswordInput } from "../../../components/inputs";

interface PasswordChangeFormProps {
  newPassword: string;
  confirmPassword: string;
  changingPassword: boolean;
  onNewPasswordChange: (value: string) => void;
  onConfirmPasswordChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  t: (key: string) => string;
}

export default function PasswordChangeForm({
  newPassword,
  confirmPassword,
  changingPassword,
  onNewPasswordChange,
  onConfirmPasswordChange,
  onSubmit,
  t,
}: PasswordChangeFormProps) {
  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <Image
            src="/logo.png"
            alt="Logo"
            width={80}
            height={80}
            className="auth-logo"
            priority
          />
          <h2 className="auth-title">{t("auth.login.changePasswordTitle")}</h2>
          <p className="auth-subtitle">
            {t("auth.login.changePasswordSubtitle")}
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-3 flex-1 overflow-y-auto">
          <div>
            <label htmlFor="newPassword" className="label-form">
              {t("auth.login.newPasswordLabel")}
            </label>
            <PasswordInput
              id="newPassword"
              value={newPassword}
              onChange={(e) => onNewPasswordChange(e.target.value)}
              placeholder={t("auth.login.newPasswordPlaceholder")}
              disabled={changingPassword}
              required
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="label-form">
              {t("auth.login.confirmPasswordLabel")}
            </label>
            <PasswordInput
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => onConfirmPasswordChange(e.target.value)}
              placeholder={t("auth.login.confirmPasswordPlaceholder")}
              disabled={changingPassword}
              required
            />
          </div>

          <div className="flex justify-center items-center mt-2 w-full">
            <GenericButton
              type="submit"
              label={t("auth.login.changePasswordBtn")}
              loading={changingPassword}
              loadingLabel={t("auth.login.changingPasswordBtn")}
              disabled={changingPassword}
              variant="primary"
              className="min-w-[200px]"
            />
          </div>
        </form>
      </div>
    </div>
  );
}
