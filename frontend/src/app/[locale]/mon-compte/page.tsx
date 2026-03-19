"use client";

import { lazy } from "react";
import { useAccountPage } from "../../../hooks/useAccountPage";
import AccountLayout from "../../../components/user/AccountLayout";
import Loading from "./loading";

// Lazy-loaded sections (loaded after the initial skeleton)
const ProfileSection = lazy(
  () => import("../../../components/user/sections/ProfileSection"),
);
const SecuritySection = lazy(
  () => import("../../../components/user/sections/SecuritySection"),
);
const SettingsSection = lazy(
  () => import("../../../components/user/sections/SettingsSection"),
);
const SubscriptionSection = lazy(
  () => import("../../../components/user/sections/SubscriptionSection"),
);
const PrivacySection = lazy(
  () => import("../../../components/user/sections/PrivacySection"),
);

export default function MonComptePage() {
  const {
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
    handleProfileSave,
    handleChangePassword,
    handleExportData,
    handleDeleteHistory,
    handleHistoryRetentionChange,
    handleDeleteAccount,
    handleSignOutAll,
    handleSignOut,
  } = useAccountPage();

  if (loading) {
    return <Loading />;
  }

  // AuthGuard en layout garantit que user est défini ; ce bloc reste en secours
  if (!user) {
    return null;
  }

  return (
    <AccountLayout>
      <ProfileSection
        profile={profile}
        setProfile={setProfile}
        onSave={handleProfileSave}
        saving={saving}
      />

      <SecuritySection
        authMethod={authMethod}
        showChangePassword={showChangePassword}
        setShowChangePassword={setShowChangePassword}
        passwordData={passwordData}
        setPasswordData={setPasswordData}
        onChangePassword={handleChangePassword}
        onSignOut={handleSignOut}
        onSignOutAll={handleSignOutAll}
        saving={saving}
      />

      <SettingsSection
        subscription={subscription}
        initialLanguage={userLanguage}
      />

      <SubscriptionSection subscription={subscription} />

      <PrivacySection
        onExportData={handleExportData}
        onDeleteAccount={handleDeleteAccount}
        onDeleteHistory={handleDeleteHistory}
        historyRetention={String(subscription?.history_retention ?? "30")}
        onHistoryRetentionChange={handleHistoryRetentionChange}
      />
    </AccountLayout>
  );
}
