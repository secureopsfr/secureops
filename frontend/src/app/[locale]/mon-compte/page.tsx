"use client";

import { lazy } from "react";
import Link from "next/link";
import Image from "next/image";
import { useLanguage } from "../../../components/LanguageProvider";
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
  const { t } = useLanguage();

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
    handleDeleteAccount,
    handleSignOutAll,
    handleSignOut,
    lp,
  } = useAccountPage();

  if (loading) {
    return <Loading />;
  }

  if (!user) {
    return (
      <>
        <div className="fixed-logo">
          <Link href={lp("/")} className="logo">
            <Image
              src="/logo.png"
              alt="SecureOps Logo"
              width={40}
              height={40}
            />
            <span className="logo-brand hidden md:inline">
              Secure<span>Ops</span>
            </span>
          </Link>
        </div>
        <div className="fixed inset-0 bg-theme flex items-center justify-center">
          <div className="text-center">
            <p className="text-theme">{t("account.mustBeLoggedIn")}</p>
          </div>
        </div>
      </>
    );
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

      <SubscriptionSection
        subscription={subscription}
        onManageSubscription={() => {
          const stripePortalUrl =
            process.env.NEXT_PUBLIC_STRIPE_CUSTOMER_PORTAL_URL ||
            "https://billing.stripe.com";
          window.open(stripePortalUrl, "_blank");
        }}
      />

      <PrivacySection
        onExportData={handleExportData}
        onDeleteAccount={handleDeleteAccount}
        onDeleteHistory={handleDeleteHistory}
      />
    </AccountLayout>
  );
}
