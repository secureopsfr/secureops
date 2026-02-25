"use client";

import { useState, useEffect } from "react";
import { signIn, confirmSignIn, getCurrentUser } from "aws-amplify/auth";
import { useRouter } from "next/navigation";
import {
  showErrorToast,
  showSuccessToast,
} from "../../../utils/toastNotifications";
import { debug } from "../../../utils/logger";
import { useLanguage } from "../../../components/LanguageProvider";
import { AuthFormSkeleton } from "../../../components/skeletons";

import { translateAuthError } from "./translateAuthError";
import PasswordChangeForm from "./PasswordChangeForm";
import LoginForm from "./LoginForm";

export default function LoginPage() {
  const router = useRouter();
  const { t, lp, setLanguage } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [changingPassword, setChangingPassword] = useState(false);
  const [needsPasswordChange, setNeedsPasswordChange] = useState(false);
  const [, setSession] = useState<unknown>(null);
  const [, setUser] = useState<unknown>(null);

  /* ── vérification de session existante ── */
  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        router.push(lp("/"));
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err || "");
        debug("No user signed in:", errMsg);

        const errorLower = errMsg.toLowerCase();
        if (
          errorLower.includes("expired") ||
          errorLower.includes("token") ||
          errorLower.includes("session") ||
          errorLower.includes("refresh")
        ) {
          Object.keys(localStorage).forEach((key) => {
            if (
              key.startsWith("CognitoIdentityServiceProvider") ||
              key.includes("amplify") ||
              key.includes("aws-amplify")
            ) {
              localStorage.removeItem(key);
            }
          });

          Object.keys(sessionStorage).forEach((key) => {
            if (
              key.startsWith("CognitoIdentityServiceProvider") ||
              key.includes("amplify") ||
              key.includes("aws-amplify")
            ) {
              sessionStorage.removeItem(key);
            }
          });
        }
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

  /* ── connexion classique ── */
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      Object.keys(localStorage).forEach((key) => {
        if (
          key.startsWith("CognitoIdentityServiceProvider") ||
          key.includes("amplify") ||
          key.includes("aws-amplify")
        ) {
          localStorage.removeItem(key);
        }
      });

      Object.keys(sessionStorage).forEach((key) => {
        if (
          key.startsWith("CognitoIdentityServiceProvider") ||
          key.includes("amplify") ||
          key.includes("aws-amplify")
        ) {
          sessionStorage.removeItem(key);
        }
      });

      try {
        const existingUser = await getCurrentUser();
        if (existingUser) {
          setUser(existingUser);
          setLoading(false);
          return;
        }
      } catch {
        // No user signed in or expired tokens, continue with new sign in
      }

      const result = await signIn({
        username: email,
        password: password,
      });

      if (
        result.nextStep?.signInStep ===
        "CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED"
      ) {
        setNeedsPasswordChange(true);
        setSession(result);
        return;
      }

      if (result.nextStep?.signInStep === "CONFIRM_SIGN_UP") {
        showErrorToast(t("auth.errors.accountNotConfirmed"));
        router.push(
          `${lp("/confirmation")}?email=${encodeURIComponent(email)}`,
        );
        return;
      }

      if (result.isSignedIn) {
        sessionStorage.setItem("justLoggedIn", "true");
        window.dispatchEvent(new CustomEvent("auth:signIn"));
        localStorage.setItem("auth:signIn", Date.now().toString());
        localStorage.removeItem("auth:signIn");

        setTimeout(async () => {
          try {
            const userService = (await import("../../../services/userService"))
              .default;
            const initResult = await userService.initUser();
            if (initResult.success && initResult.dark_mode !== undefined) {
              const theme = initResult.dark_mode ? "dark" : "light";
              localStorage.setItem("theme", theme);
              document.documentElement.setAttribute("data-theme", theme);
            }
            if (initResult.success && initResult.language) {
              const lang = initResult.language as "fr" | "en";
              setLanguage(lang);
            }
          } catch (err) {
            debug("Error during user initialization (non-blocking):", err);
          }
        }, 100);

        showSuccessToast(t("auth.login.successToast"));
        router.push(lp("/"));
      } else {
        showErrorToast(t("auth.login.errorToast"));
      }
    } catch (err: unknown) {
      const errObj = err instanceof Error ? err : null;
      const errName = (err as { name?: string })?.name;
      if (
        errObj?.message?.includes("already a signed in user") ||
        errName === "AlreadySignedInError"
      ) {
        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        } catch {
          showErrorToast(translateAuthError(err, t));
        }
      } else {
        const errorMessage = errObj?.message || String(err || "");
        const errorLower = errorMessage.toLowerCase();

        if (
          errorLower.includes("user is not confirmed") ||
          errorLower.includes("not confirmed") ||
          errorLower.includes("user not confirmed") ||
          errorLower.includes("confirmation required")
        ) {
          showErrorToast(t("auth.errors.accountNotConfirmed"));
          router.push(
            `${lp("/confirmation")}?email=${encodeURIComponent(email)}`,
          );
        } else {
          showErrorToast(translateAuthError(err, t));
        }
      }
    } finally {
      setLoading(false);
    }
  };

  /* ── changement de mot de passe (premier login admin) ── */
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      showErrorToast(t("auth.errors.passwordsMismatch"));
      return;
    }

    if (newPassword.length < 8) {
      showErrorToast(t("auth.errors.passwordTooShort"));
      return;
    }

    setChangingPassword(true);

    try {
      await confirmSignIn({
        challengeResponse: newPassword,
      });

      setNeedsPasswordChange(false);
      sessionStorage.setItem("justLoggedIn", "true");
      window.dispatchEvent(new CustomEvent("auth:signIn"));
      localStorage.setItem("auth:signIn", Date.now().toString());
      localStorage.removeItem("auth:signIn");
      showSuccessToast(t("auth.login.passwordChangedSuccess"));
      router.push(lp("/"));
    } catch (err: unknown) {
      showErrorToast(
        translateAuthError(err, t) || t("auth.login.passwordChangeError"),
      );
    } finally {
      setChangingPassword(false);
    }
  };

  /* ── rendu ── */
  if (isCheckingSession) {
    return <AuthFormSkeleton />;
  }

  if (needsPasswordChange) {
    return (
      <PasswordChangeForm
        newPassword={newPassword}
        confirmPassword={confirmPassword}
        changingPassword={changingPassword}
        onNewPasswordChange={setNewPassword}
        onConfirmPasswordChange={setConfirmPassword}
        onSubmit={handlePasswordChange}
        t={t}
      />
    );
  }

  return (
    <LoginForm
      email={email}
      password={password}
      loading={loading}
      onEmailChange={setEmail}
      onPasswordChange={setPassword}
      onSubmit={handleSignIn}
      t={t}
    />
  );
}
