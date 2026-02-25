"use client";

import React from "react";
import { CreditCard, ExternalLink, Info } from "lucide-react";
import SectionSkeleton from "../SectionSkeleton";
import { GenericButton } from "../../buttons";
import { useLanguage } from "../../LanguageProvider";

interface SubscriptionSectionProps {
  subscription: {
    plan?: string;
    status?: string;
    [key: string]: unknown;
  } | null;
  onManageSubscription?: () => void;
}

const SubscriptionSection: React.FC<SubscriptionSectionProps> = ({
  subscription,
  onManageSubscription,
}) => {
  const { t } = useLanguage();

  const handleManageSubscription = () => {
    if (onManageSubscription) {
      onManageSubscription();
    } else {
      const stripePortalUrl =
        process.env.NEXT_PUBLIC_STRIPE_CUSTOMER_PORTAL_URL ||
        "https://billing.stripe.com";
      window.open(stripePortalUrl, "_blank");
    }
  };

  const plan = subscription?.plan || "free";
  const isPremium = plan === "premium";
  const planLabel = isPremium
    ? t("subscription.premiumPlan")
    : t("subscription.freePlan");
  const planDescription = isPremium
    ? t("subscription.premiumDesc")
    : t("subscription.freeDesc");

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
            <span
              className={`inline-block px-4 py-1.5 rounded-full text-base font-medium ${
                isPremium
                  ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                  : "bg-[var(--color-surface-hover)] text-[var(--muted)]"
              }`}
            >
              {planLabel}
            </span>
          </div>
          <p className="text-sm text-[var(--muted)] mb-4">{planDescription}</p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-[var(--text)] mb-4">
            {t("subscription.paymentTitle")}
          </h3>
        </div>

        <div className="p-4 bg-[rgba(var(--primary),0.1)] border border-[rgba(var(--primary),0.3)] rounded-lg">
          <div className="flex items-center gap-3">
            <Info className="w-5 h-5 text-[rgb(var(--primary))] flex-shrink-0" />
            <p className="text-sm text-[var(--text)] leading-relaxed">
              {t("subscription.stripeInfo")}
            </p>
          </div>
        </div>

        <div className="pt-2">
          <GenericButton
            label={t("subscription.manageBtn")}
            onClick={handleManageSubscription}
            variant="primary"
            icon={<ExternalLink className="w-4 h-4" />}
            iconPosition="right"
          />
        </div>
      </div>
    </SectionSkeleton>
  );
};

export default SubscriptionSection;
