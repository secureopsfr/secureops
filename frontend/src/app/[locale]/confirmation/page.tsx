"use client";

import { useState, useEffect } from "react";
import {
  confirmSignUp,
  getCurrentUser,
  resendSignUpCode,
} from "aws-amplify/auth";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  showErrorToast,
  showSuccessToast,
} from "../../../utils/toastNotifications";
import { debug } from "../../../utils/logger";
import { GenericButton } from "../../../components/buttons";
import { useLanguage } from "../../../components/LanguageProvider";
import { AuthFormSkeleton } from "../../../components/ui/skeletons";

export default function ConfirmSignUpPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t, lp } = useLanguage();
  const email = searchParams.get("email") || "";
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [resendLoading, setResendLoading] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [canResend, setCanResend] = useState(true);

  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        await getCurrentUser();
        router.push(lp("/"));
      } catch (err: unknown) {
        debug("No user signed in:", err instanceof Error ? err.message : err);
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

  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setTimeout(() => {
        setTimeRemaining(timeRemaining - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (timeRemaining === 0 && !canResend) {
      setCanResend(true);
    }
  }, [timeRemaining, canResend]);

  const translateError = (error: unknown) => {
    const errorMessage =
      error instanceof Error
        ? error.message
        : typeof error === "string"
          ? error
          : "";
    const errorLower = errorMessage.toLowerCase();

    if (
      errorLower.includes("invalid verification code") ||
      errorLower.includes("code mismatch")
    ) {
      return t("auth.errors.invalidVerificationCode");
    }
    if (errorLower.includes("code expired")) {
      return t("auth.errors.codeExpired");
    }
    if (errorLower.includes("network") || errorLower.includes("fetch")) {
      return t("auth.errors.networkError");
    }

    return errorMessage || t("auth.errors.defaultConfirmError");
  };

  const handleConfirmSignUp = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!code) {
      showErrorToast(t("auth.confirmation.enterCodeError"));
      return;
    }

    setLoading(true);

    try {
      await confirmSignUp({
        username: email,
        confirmationCode: code,
      });

      showSuccessToast(t("auth.confirmation.successToast"));
      router.push(lp("/connexion"));
    } catch (err: unknown) {
      showErrorToast(translateError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!canResend || resendLoading) return;

    setResendLoading(true);

    try {
      await resendSignUpCode({
        username: email,
      });
      showSuccessToast(t("auth.confirmation.codeSentSuccess"));
      setTimeRemaining(300);
      setCanResend(false);
    } catch (err: unknown) {
      showErrorToast(translateError(err) || t("auth.confirmation.resendError"));
    } finally {
      setResendLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (isCheckingSession) {
    return <AuthFormSkeleton />;
  }

  if (!email) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="text-center">
            <p className="mb-4 text-muted-theme">
              {t("auth.confirmation.missingEmail")}
            </p>
            <button
              onClick={() => router.push(lp("/inscription"))}
              className="btn btn-secondary"
            >
              {t("auth.confirmation.backToRegister")}
            </button>
          </div>
        </div>
      </div>
    );
  }

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
          <h2 className="auth-title">{t("auth.confirmation.title")}</h2>
          <p className="auth-subtitle">
            {t("auth.confirmation.subtitle")}{" "}
            <strong className="text-theme">{email}</strong>
          </p>
        </div>

        <form onSubmit={handleConfirmSignUp} className="space-y-4">
          <div>
            <label htmlFor="code" className="label-form">
              {t("auth.confirmation.codeLabel")}
            </label>
            <input
              type="text"
              id="code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="auth-input text-center text-lg tracking-widest"
              placeholder="000000"
              disabled={loading}
              required
              maxLength={6}
            />
          </div>

          <div className="flex justify-center items-center mt-2 w-full">
            <GenericButton
              type="submit"
              label={t("auth.confirmation.confirmBtn")}
              loading={loading}
              loadingLabel={t("auth.confirmation.confirmingBtn")}
              disabled={loading}
              variant="primary"
              className="min-w-[200px]"
            />
          </div>
        </form>

        <div className="mt-4">
          {!canResend ? (
            <div className="text-center">
              <p className="text-xs mb-2 text-muted-theme">
                {t("auth.confirmation.resendTimer", {
                  time: formatTime(timeRemaining),
                })}
              </p>
              <button
                type="button"
                disabled
                className="btn btn-secondary w-full opacity-50 cursor-not-allowed"
              >
                {t("auth.confirmation.resendCode")}
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleResendCode}
              disabled={resendLoading}
              className="btn btn-secondary w-full"
            >
              {resendLoading
                ? t("auth.confirmation.sendingCode")
                : t("auth.confirmation.resendCode")}
            </button>
          )}
        </div>

        <div className="auth-footer">
          <p>
            <Link
              href={lp("/connexion")}
              className="hover:opacity-80 transition-opacity font-medium text-accent"
            >
              {t("auth.confirmation.backToLogin")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
