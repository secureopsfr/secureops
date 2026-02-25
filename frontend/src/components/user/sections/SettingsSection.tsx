"use client";

import React, { useState, useEffect, useRef } from "react";
import { Settings, Mail, Bell, Sun, Moon, Globe } from "lucide-react";
import SectionSkeleton from "../SectionSkeleton";
import userService from "../../../services/userService";
import {
  showSuccessToast,
  showErrorToast,
} from "../../../utils/toastNotifications";
import { ToggleSwitch } from "../../inputs";
import { useTheme } from "../../ThemeProvider";
import { useLanguage } from "../../LanguageProvider";
import type { Language } from "../../LanguageProvider";

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "fr", label: "Français" },
  { value: "en", label: "English" },
];

interface SettingsSectionProps {
  subscription: {
    newsletter_enabled?: boolean;
    new_features_notifications_enabled?: boolean;
    [key: string]: unknown;
  } | null;
  initialLanguage?: Language;
}

const SettingsSection: React.FC<SettingsSectionProps> = ({
  subscription,
  initialLanguage = "en",
}) => {
  const { theme, toggleTheme } = useTheme();
  const { setLanguage: setContextLanguage, t } = useLanguage();
  const [newsletterEnabled, setNewsletterEnabled] = useState(
    subscription?.newsletter_enabled || false,
  );
  const [newFeaturesNotificationsEnabled, setNewFeaturesNotificationsEnabled] =
    useState(subscription?.new_features_notifications_enabled || false);
  const [updatingPreferences, setUpdatingPreferences] = useState(false);
  const [updatingTheme, setUpdatingTheme] = useState(false);
  const [language, setLanguage] = useState<Language>(initialLanguage);
  const [updatingLanguage, setUpdatingLanguage] = useState(false);
  const hasShownLanguageToastRef = useRef(false);

  // Sync local states with props when subscription changes
  useEffect(() => {
    if (subscription) {
      setNewsletterEnabled(subscription.newsletter_enabled || false);
      setNewFeaturesNotificationsEnabled(
        subscription.new_features_notifications_enabled || false,
      );
    }
  }, [subscription]);

  // Sync language from initialLanguage (reset toast guard so next change can show toast)
  useEffect(() => {
    if (initialLanguage) {
      setLanguage(initialLanguage);
      hasShownLanguageToastRef.current = false;
    }
  }, [initialLanguage]);

  const handleNewsletterToggle = async () => {
    const newValue = !newsletterEnabled;
    setUpdatingPreferences(true);
    try {
      const result = await userService.updateSubscriptionPreferences({
        newsletter_enabled: newValue,
      });
      if (result.success) {
        setNewsletterEnabled(newValue);
        showSuccessToast(t("settings.newsletterUpdated"));
      } else {
        showErrorToast(result.error || t("settings.updateError"));
      }
    } catch {
      showErrorToast(t("settings.newsletterError"));
    } finally {
      setUpdatingPreferences(false);
    }
  };

  const handleNewFeaturesToggle = async () => {
    const newValue = !newFeaturesNotificationsEnabled;
    setUpdatingPreferences(true);
    try {
      const result = await userService.updateSubscriptionPreferences({
        new_features_notifications_enabled: newValue,
      });
      if (result.success) {
        setNewFeaturesNotificationsEnabled(newValue);
        showSuccessToast(t("settings.newFeaturesUpdated"));
      } else {
        showErrorToast(result.error || t("settings.updateError"));
      }
    } catch {
      showErrorToast(t("settings.newFeaturesError"));
    } finally {
      setUpdatingPreferences(false);
    }
  };

  const handleThemeToggle = async () => {
    const newDarkMode = theme === "light";
    setUpdatingTheme(true);
    try {
      toggleTheme();
      const result = await userService.updateThemePreference(newDarkMode);
      if (result.success) {
        showSuccessToast(
          newDarkMode
            ? t("settings.darkModeEnabled")
            : t("settings.lightModeEnabled"),
        );
      } else {
        toggleTheme();
        showErrorToast(result.error || t("settings.themeError"));
      }
    } catch {
      toggleTheme();
      showErrorToast(t("settings.themeError"));
    } finally {
      setUpdatingTheme(false);
    }
  };

  const handleLanguageChange = async (newLang: Language) => {
    if (newLang === language) return;
    setUpdatingLanguage(true);
    try {
      const result = await userService.updateLanguagePreference(newLang);
      if (result.success) {
        if (!hasShownLanguageToastRef.current) {
          hasShownLanguageToastRef.current = true;
          showSuccessToast(
            newLang === "fr"
              ? t("settings.languageChangedFr")
              : t("settings.languageChangedEn"),
          );
        }
        setLanguage(newLang);
        setContextLanguage(newLang); // Navigate after toast
      } else {
        showErrorToast(result.error || t("settings.languageError"));
      }
    } catch {
      showErrorToast(t("settings.languageError"));
    } finally {
      setUpdatingLanguage(false);
    }
  };

  return (
    <SectionSkeleton id="settings" icon={Settings} title={t("settings.title")}>
      <div className="space-y-6">
        {/* Theme */}
        <div>
          <h3 className="text-lg font-semibold text-[var(--text)] mb-4">
            {t("settings.appearance")}
          </h3>
          <div className="space-y-4">
            <div
              className="flex items-center justify-between p-4 bg-[var(--color-surface-input)] border border-[var(--border)] rounded-lg cursor-pointer"
              onClick={!updatingTheme ? handleThemeToggle : undefined}
            >
              <div className="flex items-center gap-3">
                {theme === "dark" ? (
                  <Moon className="w-5 h-5 text-[var(--muted)] flex-shrink-0" />
                ) : (
                  <Sun className="w-5 h-5 text-[var(--muted)] flex-shrink-0" />
                )}
                <div>
                  <p className="text-sm font-medium text-[var(--text)]">
                    {theme === "dark"
                      ? t("settings.darkMode")
                      : t("settings.lightMode")}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    {theme === "dark"
                      ? t("settings.darkModeDesc")
                      : t("settings.lightModeDesc")}
                  </p>
                </div>
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <ToggleSwitch
                  checked={theme === "dark"}
                  onChange={handleThemeToggle}
                  disabled={updatingTheme}
                />
              </div>
            </div>

            {/* Language */}
            <div className="flex items-center justify-between p-4 bg-[var(--color-surface-input)] border border-[var(--border)] rounded-lg">
              <div className="flex items-center gap-3">
                <Globe className="w-5 h-5 text-[var(--muted)] flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-[var(--text)]">
                    {t("settings.language")}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    {t("settings.languageDesc")}
                  </p>
                </div>
              </div>
              <div
                className={`flex gap-1 rounded-lg border border-[var(--border)] p-1 bg-[var(--color-surface-subtle)] ${updatingLanguage ? "opacity-50" : ""}`}
              >
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.value}
                    type="button"
                    onClick={() => handleLanguageChange(lang.value)}
                    disabled={updatingLanguage}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-all cursor-pointer ${
                      language === lang.value
                        ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                        : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                    }`}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Communications */}
        <div>
          <h3 className="text-lg font-semibold text-[var(--text)] mb-4">
            {t("settings.communications")}
          </h3>
          <div className="space-y-4">
            <div
              className="flex items-center justify-between p-4 bg-[var(--color-surface-input)] border border-[var(--border)] rounded-lg cursor-pointer"
              onClick={
                !updatingPreferences ? handleNewsletterToggle : undefined
              }
            >
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5 text-[var(--muted)] flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-[var(--text)]">
                    {t("settings.newsletter")}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    {t("settings.newsletterDesc")}
                  </p>
                </div>
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <ToggleSwitch
                  checked={newsletterEnabled}
                  onChange={handleNewsletterToggle}
                  disabled={updatingPreferences}
                />
              </div>
            </div>

            <div
              className="flex items-center justify-between p-4 bg-[var(--color-surface-input)] border border-[var(--border)] rounded-lg cursor-pointer"
              onClick={
                !updatingPreferences ? handleNewFeaturesToggle : undefined
              }
            >
              <div className="flex items-center gap-3">
                <Bell className="w-5 h-5 text-[var(--muted)] flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-[var(--text)]">
                    {t("settings.newFeatures")}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    {t("settings.newFeaturesDesc")}
                  </p>
                </div>
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <ToggleSwitch
                  checked={newFeaturesNotificationsEnabled}
                  onChange={handleNewFeaturesToggle}
                  disabled={updatingPreferences}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionSkeleton>
  );
};

export default SettingsSection;
