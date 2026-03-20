"use client";

import { useState, useEffect } from "react";
import { signUp, getCurrentUser } from "aws-amplify/auth";
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
import { AuthFormSkeleton } from "../../../components/ui/skeletons";

export default function SignUpPage() {
  const router = useRouter();
  const { t, lp } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

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

  const translateError = (error: unknown) => {
    const errorMessage =
      error instanceof Error
        ? error.message
        : typeof error === "string"
          ? error
          : "";
    const errorLower = errorMessage.toLowerCase();

    if (
      errorLower.includes("username exists") ||
      errorLower.includes("user already exists")
    ) {
      return t("auth.errors.usernameExists");
    }
    if (
      errorLower.includes("invalid password") ||
      errorLower.includes("password")
    ) {
      return t("auth.errors.invalidPassword");
    }
    if (errorLower.includes("invalid email")) {
      return t("auth.errors.invalidEmail");
    }
    if (errorLower.includes("network") || errorLower.includes("fetch")) {
      return t("auth.errors.networkError");
    }

    return errorMessage || t("auth.errors.defaultRegisterError");
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      showErrorToast(t("auth.errors.passwordsMismatch"));
      return;
    }

    if (password.length < 8) {
      showErrorToast(t("auth.errors.passwordTooShort"));
      return;
    }

    setLoading(true);

    try {
      const { nextStep } = await signUp({
        username: email,
        password: password,
        options: {
          userAttributes: {
            email: email,
          },
        },
      });

      if (nextStep.signUpStep === "CONFIRM_SIGN_UP") {
        showSuccessToast(t("auth.register.confirmationCodeSent"));
        router.push(
          `${lp("/confirmation")}?email=${encodeURIComponent(email)}`,
        );
      }
    } catch (err: unknown) {
      showErrorToast(translateError(err));
    } finally {
      setLoading(false);
    }
  };

  if (isCheckingSession) {
    return (
      <>
        <h1 className="sr-only">{t("auth.register.title")}</h1>
        <h2 className="sr-only">{t("auth.register.formSectionTitle")}</h2>
        <AuthFormSkeleton />
      </>
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
          <h1 className="auth-title">{t("auth.register.title")}</h1>
          <p className="auth-subtitle">{t("auth.register.subtitle")}</p>
        </div>

        <div className="space-y-4 flex-1 overflow-y-auto">
          <h2 className="sr-only">{t("auth.register.formSectionTitle")}</h2>
          <form onSubmit={handleSignUp} className="space-y-3">
            <div>
              <label htmlFor="email" className="label-form">
                {t("auth.register.emailLabel")}
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
                placeholder={t("auth.register.emailPlaceholder")}
                disabled={loading}
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="label-form">
                {t("auth.register.passwordLabel")}
              </label>
              <PasswordInput
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                required
              />
              <p className="input-hint mt-1">
                {t("auth.register.passwordHint")}
              </p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="label-form">
                {t("auth.register.confirmPasswordLabel")}
              </label>
              <PasswordInput
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                required
              />
            </div>

            <div className="flex justify-center items-center mt-2 w-full">
              <GenericButton
                type="submit"
                label={t("auth.register.submitBtn")}
                loading={loading}
                loadingLabel={t("auth.register.loadingBtn")}
                disabled={loading}
                variant="primary"
                className="min-w-[200px]"
              />
            </div>
          </form>
        </div>

        <div className="auth-footer">
          <p>
            {t("auth.register.hasAccount")}{" "}
            <Link
              href={lp("/connexion")}
              className="hover:opacity-80 transition-opacity font-medium text-accent"
            >
              {t("auth.register.signInLink")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
