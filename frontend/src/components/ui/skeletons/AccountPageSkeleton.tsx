"use client";

import React from "react";
import Card from "../cards/Card";
import Skeleton, {
  SkeletonInput,
  SkeletonButton,
  SkeletonToggleRow,
  SkeletonText,
} from "./Skeleton";

/**
 * Skeleton wrapper mimant le SectionSkeleton (icône + titre + contenu)
 */
const SectionSkeletonLoader: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => (
  <section>
    <Card disableHover>
      {/* Icon w-6 h-6 + titre text-2xl bold (line-height 2rem = h-8) */}
      <div className="flex items-center gap-3 mb-6">
        <Skeleton width="w-6" height="h-6" rounded="md" />
        <Skeleton width="w-40" height="h-8" rounded="md" />
      </div>
      {children}
    </Card>
  </section>
);

/**
 * Skeleton pour la section Profil
 */
export const ProfileSectionSkeleton: React.FC = () => (
  <SectionSkeletonLoader>
    <div className="space-y-7">
      {/* Email (disabled) — label text-sm (h-3.5) + input + hint text-xs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Skeleton width="w-16" height="h-3.5" className="mb-1" />
          <Skeleton width="w-full" height="h-10" rounded="lg" />
          <Skeleton width="w-52" height="h-3" className="mt-1" />
        </div>
      </div>
      {/* First name + Last name — label text-xs (h-3) + input */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonInput />
        <SkeletonInput />
      </div>
      {/* Save button */}
      <div className="flex justify-end pt-4">
        <SkeletonButton />
      </div>
    </div>
  </SectionSkeletonLoader>
);

/**
 * Skeleton pour la section Sécurité
 */
export const SecuritySectionSkeleton: React.FC = () => (
  <SectionSkeletonLoader>
    <div className="space-y-7">
      {/* Auth method label + badge */}
      <div>
        <Skeleton width="w-36" height="h-4" className="mb-2" />
        <Skeleton width="w-40" height="h-7" rounded="full" />
      </div>
      {/* Change password button */}
      <SkeletonButton width="w-48" />
      {/* Sign out section — h3 text-lg (line-height 1.75rem = h-7) mb-2 */}
      <div className="pt-4 border-t border-[var(--border)]">
        <Skeleton width="w-32" height="h-5" className="mb-2" />
        <div className="flex flex-row flex-wrap gap-2">
          <SkeletonButton />
          <SkeletonButton width="w-56" />
        </div>
      </div>
    </div>
  </SectionSkeletonLoader>
);

/**
 * Skeleton pour la section Paramètres
 */
export const SettingsSectionSkeleton: React.FC = () => (
  <SectionSkeletonLoader>
    <div className="space-y-6">
      {/* Appearance — h3 text-lg mb-4 */}
      <div>
        <Skeleton width="w-28" height="h-5" className="mb-4" />
        <div className="space-y-4">
          {/* Theme toggle row */}
          <SkeletonToggleRow />
          {/* Language selector row (même container, contrôle = boutons) */}
          <div className="flex items-center justify-between p-4 bg-[var(--color-surface-input)] border border-[var(--border)] rounded-lg">
            <div className="flex items-center gap-3">
              <Skeleton width="w-5" height="h-5" rounded="md" />
              <div className="space-y-1.5">
                <Skeleton width="w-20" height="h-3.5" />
                <Skeleton width="w-44" height="h-3" />
              </div>
            </div>
            {/* Language button group */}
            <div className="flex gap-1 rounded-lg border border-[var(--border)] p-1 bg-[var(--color-surface-subtle)]">
              <Skeleton width="w-20" height="h-9" rounded="md" />
              <Skeleton width="w-16" height="h-9" rounded="md" />
            </div>
          </div>
        </div>
      </div>
      {/* Communications — h3 text-lg mb-4 */}
      <div>
        <Skeleton width="w-52" height="h-5" className="mb-4" />
        <div className="space-y-4">
          <SkeletonToggleRow />
          <SkeletonToggleRow />
        </div>
      </div>
    </div>
  </SectionSkeletonLoader>
);

/**
 * Skeleton pour la section Abonnement
 */
export const SubscriptionSectionSkeleton: React.FC = () => (
  <SectionSkeletonLoader>
    <div className="space-y-4">
      {/* Current plan — h3 text-lg mb-2 + badge mb-3 + description text-sm mb-4 */}
      <div>
        <Skeleton width="w-28" height="h-5" className="mb-2" />
        <Skeleton width="w-32" height="h-8" rounded="full" className="mb-3" />
        <SkeletonText lines={1} className="mb-4" />
      </div>
      {/* Payment title — h3 text-lg mb-4 */}
      <Skeleton width="w-44" height="h-5" className="mb-4" />
      {/* Info box — opacités identiques au vrai : bg 0.1, border 0.3 */}
      <div className="p-4 bg-[rgba(var(--primary),0.1)] border border-[rgba(var(--primary),0.3)] rounded-lg">
        <div className="flex items-center gap-3">
          <Skeleton
            width="w-5"
            height="h-5"
            rounded="md"
            className="flex-shrink-0"
          />
          <SkeletonText lines={2} className="flex-1" />
        </div>
      </div>
      {/* Manage button */}
      <div className="pt-2">
        <SkeletonButton width="w-64" />
      </div>
    </div>
  </SectionSkeletonLoader>
);

/**
 * Skeleton pour la section Données & confidentialité
 */
export const PrivacySectionSkeleton: React.FC = () => (
  <SectionSkeletonLoader>
    <div className="space-y-4">
      {/* Download section */}
      <div>
        <Skeleton width="w-44" height="h-5" className="mb-2" />
        <SkeletonText lines={1} className="mb-3" />
        <SkeletonButton width="w-48" />
      </div>
      {/* Favorites section */}
      <div className="pt-4 border-t border-[var(--border)]">
        <Skeleton width="w-20" height="h-5" className="mb-2" />
        <SkeletonText lines={1} className="mb-3" />
        <SkeletonButton width="w-52" />
      </div>
      {/* Danger zone */}
      <div className="pt-4 border-t border-[var(--border)]">
        <Skeleton width="w-32" height="h-5" className="mb-2" />
        <SkeletonText lines={2} className="mb-4" />
        <SkeletonButton width="w-44" />
      </div>
    </div>
  </SectionSkeletonLoader>
);

/**
 * Skeleton complet pour la page Mon Compte
 * Affiche toutes les sections en skeleton
 */
const AccountPageSkeleton: React.FC = () => (
  <div className="pt-2 w-full">
    <ProfileSectionSkeleton />
    <SecuritySectionSkeleton />
    <SettingsSectionSkeleton />
    <SubscriptionSectionSkeleton />
    <PrivacySectionSkeleton />
    <div className="h-[1px]" aria-hidden="true" />
  </div>
);

export default AccountPageSkeleton;
