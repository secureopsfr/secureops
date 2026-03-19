"use client";

import React from "react";
import { CreditCard } from "lucide-react";
import SectionSkeleton from "../SectionSkeleton";
import { useLanguage } from "../../LanguageProvider";

interface SubscriptionSectionProps {
  subscription: {
    plan?: string;
    status?: string;
    [key: string]: unknown;
  } | null;
  onManageSubscription?: () => void;
}

const SubscriptionSection: React.FC<SubscriptionSectionProps> = () => {
  const { t } = useLanguage();

  return (
    <SectionSkeleton
      id="subscription"
      icon={CreditCard}
      title={t("subscription.title")}
    >
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-[var(--text)] mb-2">
            {t("subscription.currentPlan")}
          </h3>
          <div className="mb-3">
            <span className="inline-block px-4 py-1.5 rounded-full text-base font-medium bg-[var(--color-surface-hover)] text-[var(--muted)]">
              {t("subscription.freePlan")}
            </span>
          </div>
          <p className="text-sm text-[var(--muted)]">
            {t("subscription.freeDesc")}
          </p>
        </div>
      </div>
    </SectionSkeleton>
  );
};

export default SubscriptionSection;
