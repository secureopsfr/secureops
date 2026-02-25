"use client";

import React from "react";
import { User, Save } from "lucide-react";
import SectionSkeleton from "../SectionSkeleton";
import { GenericButton } from "../../buttons";
import { useLanguage } from "../../LanguageProvider";

interface ProfileSectionProps {
  profile: {
    givenName: string;
    familyName: string;
    email: string;
    phoneNumber: string;
  };
  setProfile: (profile: {
    givenName: string;
    familyName: string;
    email: string;
    phoneNumber: string;
  }) => void;
  onSave: () => void;
  saving: boolean;
}

const ProfileSection: React.FC<ProfileSectionProps> = ({
  profile,
  setProfile,
  onSave,
  saving,
}) => {
  const { t } = useLanguage();

  return (
    <SectionSkeleton id="profile" icon={User} title={t("profile.title")}>
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-1">
              {t("profile.emailLabel")}
            </label>
            <input
              type="email"
              value={profile.email}
              disabled
              className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--color-surface-input)] text-[var(--muted)] cursor-not-allowed"
            />
            <p className="text-xs text-[var(--muted)] mt-1">
              {t("profile.emailHint")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="givenName"
              className="block text-xs font-medium mb-1"
              style={{ color: "var(--text)" }}
            >
              {t("profile.givenNameLabel")}
            </label>
            <input
              type="text"
              id="givenName"
              value={profile.givenName}
              onChange={(e) =>
                setProfile({ ...profile, givenName: e.target.value })
              }
              className="auth-input"
              placeholder={t("profile.givenNamePlaceholder")}
            />
          </div>
          <div>
            <label
              htmlFor="familyName"
              className="block text-xs font-medium mb-1"
              style={{ color: "var(--text)" }}
            >
              {t("profile.familyNameLabel")}
            </label>
            <input
              type="text"
              id="familyName"
              value={profile.familyName}
              onChange={(e) =>
                setProfile({ ...profile, familyName: e.target.value })
              }
              className="auth-input"
              placeholder={t("profile.familyNamePlaceholder")}
            />
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <GenericButton
            label={t("profile.saveBtn")}
            onClick={onSave}
            loading={saving}
            loadingLabel={t("profile.savingBtn")}
            disabled={saving}
            variant="primary"
            icon={<Save className="w-4 h-4" />}
            iconPosition="left"
          />
        </div>
      </div>
    </SectionSkeleton>
  );
};

export default ProfileSection;
