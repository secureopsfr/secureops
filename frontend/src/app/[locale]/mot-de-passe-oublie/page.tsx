"use client";

import { useState, useEffect } from "react";
import {
  resetPassword,
  confirmResetPassword,
  getCurrentUser,
} from "aws-amplify/auth";
import Image from "next/image";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  showErrorToast,
  showSuccessToast,
} from "../../../utils/toastNotifications";
import { debug } from "../../../utils/logger";
import { GenericButton } from "../../../components/buttons";
import { PasswordInput } from "../../../components/inputs";
import { useLanguage } from "../../../components/LanguageProvider";
import { AuthFormSkeleton } from "../../../components/skeletons";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const { t, lp } = useLanguage();
  const [email, setEmail] = useState("");
  const [hasRequestedReset, setHasRequestedReset] = useState(false);
  const [resetCode, setResetCode] = useState("");
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [resetConfirmPassword, setResetConfirmPassword] = useState("");
  const [resetLoading, setResetLoading] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        await getCurrentUser();
        router.push(lp("/"));
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err || "");
        debug("No user signed in:", errMsg);
      } finally {
        setIsCheckingSession(false);
      }
    };

    checkCurrentUser();
  }, [router, lp]);

  useEffect(() => {
    document.body.style.paddingTop = "0";
    return () => {
      document.body.style.paddingTop = "";
    };
  }, []);

  const translateError = (error: unknown) => {
    const errorMessage =
      error instanceof Error
        ? error.message
        : typeof error === "string"
          ? error
          : "";
    const errorLower = errorMessage.toLowerCase();

    if (
      errorLower.includes("incorrect username or password") ||
      errorLower.includes("invalid credentials")
    ) {
      return t("auth.errors.incorrectCredentials");
    }
    if (errorLower.includes("user does not exist")) {
      return t("auth.errors.userNotExist");
    }
    if (errorLower.includes("user is disabled")) {
      return t("auth.errors.userDisabled");
    }
    if (
      errorLower.includes("password attempts exceeded") ||
      errorLower.includes("attempt limit exceeded")
    ) {
      return t("auth.errors.attemptsExceeded");
    }
    if (errorLower.includes("network") || errorLower.includes("fetch")) {
      return t("auth.errors.networkError");
    }
    if (
      errorLower.includes("invalid verification code") ||
      errorLower.includes("code mismatch")
    ) {
      return t("auth.errors.invalidVerificationCode");
    }
    if (errorLower.includes("code expired")) {
      return t("auth.errors.codeExpired");
    }
    if (errorLower.includes("limit exceeded")) {
      return t("auth.errors.limitExceeded");
    }

    return errorMessage || t("auth.errors.defaultResetError");
  };

  const handleRequestPasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetLoading(true);

    try {
      await resetPassword({ username: email });
      setHasRequestedReset(true);
      showSuccessToast(t("auth.forgotPassword.codeSentSuccess"));
    } catch (err: unknown) {
      showErrorToast(translateError(err) || t("auth.errors.defaultResetError"));
    } finally {
      setResetLoading(false);
    }
  };

  const handleConfirmPasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();

    if (resetNewPassword !== resetConfirmPassword) {
      showErrorToast(t("auth.errors.passwordsMismatch"));
      return;
    }

    if (resetNewPassword.length < 8) {
      showErrorToast(t("auth.errors.passwordTooShort"));
      return;
    }

    setResetLoading(true);

    try {
      await confirmResetPassword({
        username: email,
        confirmationCode: resetCode,
        newPassword: resetNewPassword,
      });
      showSuccessToast(t("auth.forgotPassword.resetSuccess"));
      router.push(lp("/connexion"));
    } catch (err: unknown) {
      showErrorToast(translateError(err) || t("auth.errors.defaultResetError"));
    } finally {
      setResetLoading(false);
    }
  };

  if (isCheckingSession) {
    return <AuthFormSkeleton />;
  }

  // Step 1: Request email for reset code
  if (!hasRequestedReset) {
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
            <h2 className="auth-title">{t("auth.forgotPassword.title")}</h2>
            <p className="auth-subtitle">{t("auth.forgotPassword.subtitle")}</p>
          </div>

          <form
            onSubmit={handleRequestPasswordReset}
            className="space-y-4 flex-1 overflow-y-auto"
          >
            <div>
              <label htmlFor="resetEmail" className="label-form">
                {t("auth.forgotPassword.emailLabel")}
              </label>
              <input
                type="email"
                id="resetEmail"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
                placeholder={t("auth.forgotPassword.emailPlaceholder")}
                disabled={resetLoading}
                required
              />
            </div>

            <GenericButton
              type="submit"
              label={t("auth.forgotPassword.submitBtn")}
              loading={resetLoading}
              loadingLabel={t("auth.forgotPassword.loadingBtn")}
              disabled={resetLoading}
              variant="primary"
              className="w-full min-w-[200px]"
            />
          </form>

          <div className="auth-footer">
            <p>
              <Link
                href={lp("/connexion")}
                className="hover:opacity-80 transition-opacity font-medium text-accent"
              >
                {t("auth.forgotPassword.backToLogin")}
              </Link>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Step 2: Enter code and new password
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
          <h2 className="auth-title">{t("auth.forgotPassword.resetTitle")}</h2>
          <p className="auth-subtitle">
            {t("auth.forgotPassword.resetSubtitle")}
          </p>
        </div>

        <form
          onSubmit={handleConfirmPasswordReset}
          className="space-y-3 flex-1 overflow-y-auto"
        >
          <div>
            <label htmlFor="resetCode" className="label-form">
              {t("auth.forgotPassword.codeLabel")}
            </label>
            <input
              type="text"
              id="resetCode"
              value={resetCode}
              onChange={(e) => setResetCode(e.target.value)}
              className="auth-input"
              placeholder={t("auth.forgotPassword.codePlaceholder")}
              disabled={resetLoading}
              required
            />
          </div>

          <div>
            <label htmlFor="resetNewPassword" className="label-form">
              {t("auth.forgotPassword.newPasswordLabel")}
            </label>
            <PasswordInput
              id="resetNewPassword"
              value={resetNewPassword}
              onChange={(e) => setResetNewPassword(e.target.value)}
              placeholder="••••••••"
              disabled={resetLoading}
              required
            />
          </div>

          <div>
            <label htmlFor="resetConfirmPassword" className="label-form">
              {t("auth.forgotPassword.confirmPasswordLabel")}
            </label>
            <PasswordInput
              id="resetConfirmPassword"
              value={resetConfirmPassword}
              onChange={(e) => setResetConfirmPassword(e.target.value)}
              placeholder="••••••••"
              disabled={resetLoading}
              required
            />
          </div>

          <GenericButton
            type="submit"
            label={t("auth.forgotPassword.resetBtn")}
            loading={resetLoading}
            loadingLabel={t("auth.forgotPassword.resettingBtn")}
            disabled={resetLoading}
            variant="primary"
            className="w-full min-w-[200px]"
          />
        </form>

        <div className="auth-footer">
          <p>
            <Link
              href={lp("/connexion")}
              className="hover:opacity-80 transition-opacity font-medium text-accent"
            >
              {t("auth.forgotPassword.backToLogin")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
