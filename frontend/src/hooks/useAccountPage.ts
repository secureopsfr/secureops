"use client";

import { useState, useEffect, useRef } from "react";
import { fetchAuthSession, signOut } from "aws-amplify/auth";
import { useRouter } from "next/navigation";
import { showErrorToast, showSuccessToast } from "../utils/toastNotifications";
import { log, error } from "../utils/logger";
import userService from "../services/userService";
import { deleteAllScans } from "../services/scanHistoryService";
import { useLanguage } from "../components/LanguageProvider";
import { useAuthUser } from "./useAuthUser";

/* ─── Types ─────────────────────────────────────────────── */

export interface Profile {
  givenName: string;
  familyName: string;
  email: string;
  phoneNumber: string;
}

export interface PasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface Subscription {
  plan?: string;
  status?: string;
  newsletter_enabled?: boolean;
  new_features_notifications_enabled?: boolean;
  [key: string]: unknown;
}

/* ─── Helper: decode ID token payload ───────────────────── */

function decodeTokenPayload(token: {
  payload: Record<string, unknown>;
  decodePayload?: () => Record<string, unknown>;
}): Record<string, unknown> {
  if (typeof token.decodePayload === "function") {
    return token.decodePayload();
  }
  return token.payload;
}

/* ─── Helper: detect auth method from token + user ──────── */

function detectAuthMethod(
  loginId: string | undefined,
  identities?: unknown,
): "email" | "google" {
  if (
    loginId?.includes("google") ||
    loginId?.includes("Google") ||
    identities
  ) {
    return "google";
  }
  return "email";
}

/* ─── Hook ──────────────────────────────────────────────── */

export function useAccountPage() {
  const router = useRouter();
  const { t, lp, setLanguage: setContextLanguage } = useLanguage();
  const { user, isLoading: authLoading } = useAuthUser();
  const tRef = useRef(t);
  const setContextLanguageRef = useRef(setContextLanguage);
  tRef.current = t;
  setContextLanguageRef.current = setContextLanguage;

  // Data-loading flag (profile + subscription)
  const [dataLoading, setDataLoading] = useState(true);
  const loading = authLoading || dataLoading;

  const [saving, setSaving] = useState(false);
  const [subscription, setSubscription] = useState<Subscription | null>(null);

  const [profile, setProfile] = useState<Profile>({
    givenName: "",
    familyName: "",
    email: "",
    phoneNumber: "",
  });

  const [userLanguage, setUserLanguage] = useState<"fr" | "en">("en");

  const [authMethod, setAuthMethod] = useState<"email" | "google">("email");
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [passwordData, setPasswordData] = useState<PasswordData>({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  /* ── Redirect if not authenticated ────────────────────── */
  useEffect(() => {
    if (!authLoading && !user) {
      router.push(lp("/connexion"));
    }
  }, [authLoading, user, router, lp]);

  /* ── Load user data once authenticated ────────────────── */
  useEffect(() => {
    if (authLoading || !user) return;
    const currentUser = user;

    const loadUserData = async () => {
      try {
        // Fetch profile attributes from session token
        try {
          const session = await fetchAuthSession();
          const idToken = session.tokens?.idToken;
          if (idToken) {
            const payload = decodeTokenPayload(
              idToken as Parameters<typeof decodeTokenPayload>[0],
            );
            setProfile({
              givenName: (payload.given_name as string) || "",
              familyName: (payload.family_name as string) || "",
              email: (payload.email as string) || currentUser.username || "",
              phoneNumber: (payload.phone_number as string) || "",
            });
            setAuthMethod(
              detectAuthMethod(
                currentUser.signInDetails?.loginId,
                payload.identities,
              ),
            );
          } else {
            setProfile({
              givenName: "",
              familyName: "",
              email: currentUser.username || "",
              phoneNumber: "",
            });
            setAuthMethod(detectAuthMethod(currentUser.signInDetails?.loginId));
          }
        } catch (err) {
          log("Impossible de récupérer les attributs depuis le token:", err);
          setProfile({
            givenName: "",
            familyName: "",
            email: currentUser.username || "",
            phoneNumber: "",
          });
          setAuthMethod(detectAuthMethod(currentUser.signInDetails?.loginId));
        }

        // Load subscription & user preferences
        try {
          const [subscriptionResult, initResult] = await Promise.all([
            userService.getSubscription(),
            userService.initUser(),
          ]);
          if (subscriptionResult.success && subscriptionResult.subscription) {
            setSubscription(subscriptionResult.subscription);
          } else {
            setSubscription({ plan: "free", status: "active" });
          }
          if (initResult.success && initResult.language) {
            const lang = initResult.language as "fr" | "en";
            setUserLanguage(lang);
            setContextLanguageRef.current(lang);
          }
        } catch (subscriptionErr) {
          log("Erreur lors du chargement de l'abonnement:", subscriptionErr);
          setSubscription({ plan: "free", status: "active" });
        }
      } catch (err) {
        error("Erreur lors du chargement des données utilisateur:", err);
        showErrorToast(tRef.current("account.loadError"));
        router.push(lp("/connexion"));
      } finally {
        setDataLoading(false);
      }
    };

    loadUserData();
  }, [authLoading, user, router, lp]);

  /* ── Handlers ─────────────────────────────────────────── */

  const handleProfileSave = async () => {
    setSaving(true);
    try {
      const profileData: { given_name?: string; family_name?: string } = {};
      if (profile.givenName) profileData.given_name = profile.givenName;
      if (profile.familyName) profileData.family_name = profile.familyName;

      if (Object.keys(profileData).length === 0) {
        showErrorToast(t("account.noChanges"));
        setSaving(false);
        return;
      }

      const result = await userService.updateProfile(profileData);

      if (result.success) {
        showSuccessToast(result.message || t("account.profileUpdated"));
        try {
          const session = await fetchAuthSession({ forceRefresh: true });
          const idToken = session.tokens?.idToken;
          if (idToken) {
            const payload = decodeTokenPayload(
              idToken as Parameters<typeof decodeTokenPayload>[0],
            );
            setProfile({
              ...profile,
              givenName: (payload.given_name as string) || "",
              familyName: (payload.family_name as string) || "",
            });
          }
        } catch (sessionErr) {
          log(
            "Impossible de rafraîchir la session après mise à jour:",
            sessionErr,
          );
        }
      } else {
        showErrorToast(result.error || t("account.profileUpdateError"));
      }
    } catch (err) {
      error("Error updating profile:", err);
      showErrorToast(t("account.profileUpdateError"));
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      showErrorToast(t("auth.errors.passwordsMismatch"));
      return;
    }
    if (passwordData.newPassword.length < 8) {
      showErrorToast(t("auth.errors.passwordTooShort"));
      return;
    }
    if (!passwordData.currentPassword) {
      showErrorToast(t("account.currentPasswordRequired"));
      return;
    }

    setSaving(true);
    try {
      const result = await userService.changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
      });

      if (result.success) {
        showSuccessToast(result.message || t("account.passwordChanged"));
        setPasswordData({
          currentPassword: "",
          newPassword: "",
          confirmPassword: "",
        });
        setShowChangePassword(false);
      } else {
        showErrorToast(result.error || t("account.passwordChangeError"));
      }
    } catch (err) {
      error("Error changing password:", err);
      showErrorToast(t("account.passwordChangeError"));
    } finally {
      setSaving(false);
    }
  };

  const handleExportData = async () => {
    try {
      const result = await userService.exportUserData();
      if (!result.success) {
        showErrorToast(result.error || t("account.exportError"));
        return;
      }

      const blob = new Blob([result.data || ""], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `immosphere-data-${new Date().toISOString().split("T")[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showSuccessToast(t("account.exportSuccess"));
    } catch (err) {
      error("Error exporting data:", err);
      showErrorToast(t("account.exportError"));
    }
  };

  const handleDeleteHistory = async () => {
    try {
      const { deletedCount } = await deleteAllScans();
      showSuccessToast(
        deletedCount > 0
          ? t("account.historyDeleted", { count: deletedCount })
          : t("account.noHistory"),
      );
    } catch (err) {
      error("Error deleting scan history:", err);
      showErrorToast(t("account.historyDeleteError"));
    }
  };

  const handleHistoryRetentionChange = async (value: string) => {
    setSaving(true);
    try {
      const result = await userService.updateSubscriptionPreferences({
        history_retention: value,
      });
      if (result.success && result.subscription) {
        setSubscription(result.subscription);
        showSuccessToast(t("account.preferencesSaved"));
      } else {
        showErrorToast(result.error || t("account.preferencesError"));
      }
    } catch (err) {
      error("Error updating history retention:", err);
      showErrorToast(t("account.preferencesError"));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      const result = await userService.deleteAccount();
      if (result.success) {
        showSuccessToast(t("account.accountDeleted"));
        setTimeout(async () => {
          await signOut();
          router.push(lp("/"));
        }, 2000);
      } else {
        showErrorToast(result.error || t("account.accountDeleteError"));
      }
    } catch (err) {
      error("Error deleting account:", err);
      showErrorToast(t("account.accountDeleteError"));
    }
  };

  const handleSignOutAll = async () => {
    try {
      const result = await userService.logoutAllDevices();
      if (result.success) {
        showSuccessToast(t("account.signOutAllSuccess"));
        setTimeout(async () => {
          await signOut();
          router.push(lp("/"));
        }, 1000);
      } else {
        showErrorToast(result.error || t("account.signOutAllError"));
      }
    } catch (err) {
      error("Error logging out all devices:", err);
      showErrorToast(t("account.signOutAllError"));
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      showSuccessToast(t("account.signOutSuccess"));
      router.push(lp("/"));
    } catch (err) {
      error("Error logging out:", err);
      showErrorToast(t("account.signOutError"));
    }
  };

  return {
    // State
    user,
    loading,
    saving,
    profile,
    setProfile,
    subscription,
    userLanguage,
    authMethod,
    showChangePassword,
    setShowChangePassword,
    passwordData,
    setPasswordData,

    // Handlers
    handleProfileSave,
    handleChangePassword,
    handleExportData,
    handleDeleteHistory,
    handleHistoryRetentionChange,
    handleDeleteAccount,
    handleSignOutAll,
    handleSignOut,

    // Navigation helpers
    lp,
    t,
  };
}

export default useAccountPage;
