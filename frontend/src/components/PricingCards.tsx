"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import { GenericButton } from "./buttons";
import { Card } from "./cards";

export interface PricingPlan {
  name: string;
  description: string;
  monthlyPrice: string;
  yearlyPrice: string;
  period: string;
  features: string[];
  cta: string;
  ctaHref: string;
  variant: "secondary" | "primary";
  popular?: boolean;
}

interface PricingCardsProps {
  plans: PricingPlan[];
  translations: {
    monthly: string;
    yearly: string;
    mostPopular: string;
    billedYearly: string;
  };
}

/**
 * Client component — billing toggle (monthly/yearly) + pricing cards.
 * All plan data & translations are pre-computed on the server and passed as props.
 */
export default function PricingCards({
  plans,
  translations: t,
}: PricingCardsProps) {
  const [billing, setBilling] = useState<"monthly" | "yearly">("monthly");

  return (
    <>
      {/* Monthly / Yearly toggle */}
      <div className="flex justify-center">
        <div className="flex gap-1 rounded-lg border border-[var(--border)] p-1 bg-[var(--color-surface-subtle)]">
          <button
            type="button"
            onClick={() => setBilling("monthly")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all cursor-pointer ${
              billing === "monthly"
                ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
            }`}
          >
            {t.monthly}
          </button>
          <button
            type="button"
            onClick={() => setBilling("yearly")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all cursor-pointer ${
              billing === "yearly"
                ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
            }`}
          >
            {t.yearly}
          </button>
        </div>
      </div>

      {/* Cards */}
      <div
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
        style={{ alignItems: "stretch" }}
      >
        {plans.map((plan) => {
          const price =
            billing === "monthly" ? plan.monthlyPrice : plan.yearlyPrice;

          return (
            <Card
              key={plan.name}
              className="flex flex-col relative"
              disableHover
              style={{
                border: plan.popular
                  ? "2px solid rgb(var(--primary))"
                  : undefined,
              }}
            >
              {plan.popular && (
                <div
                  className="absolute top-0 left-1/2 -translate-x-1/2 px-4 py-1 rounded-b-lg text-xs font-semibold"
                  style={{
                    background: "rgb(var(--primary))",
                    color: "var(--color-btn-primary-text)",
                  }}
                >
                  {t.mostPopular}
                </div>
              )}

              <div className="flex-1">
                <h3
                  className="text-xl font-bold mb-1"
                  style={{ color: "var(--text)" }}
                >
                  {plan.name}
                </h3>
                <p className="text-sm mb-6" style={{ color: "var(--muted)" }}>
                  {plan.description}
                </p>

                <div className="mb-6 relative" style={{ minHeight: "3.5rem" }}>
                  <div className="flex items-center gap-2">
                    <span
                      className="text-4xl font-extrabold"
                      style={{ color: "var(--text)" }}
                    >
                      {price}
                    </span>
                    {plan.period && (
                      <span
                        className="text-base font-normal"
                        style={{ color: "var(--muted)" }}
                      >
                        {plan.period}
                      </span>
                    )}
                    {billing === "yearly" && plan.period && (
                      <span
                        className="text-xs font-semibold px-2 py-0.5 rounded-full"
                        style={{
                          background: "rgba(var(--primary), 0.15)",
                          color: "rgb(var(--primary))",
                        }}
                      >
                        -20%
                      </span>
                    )}
                  </div>
                  <span
                    className="block text-xs mt-1"
                    style={{
                      color: "var(--muted)",
                      visibility:
                        billing === "yearly" && plan.period
                          ? "visible"
                          : "hidden",
                    }}
                  >
                    {t.billedYearly}
                  </span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3">
                      <Check
                        className="w-5 h-5 flex-shrink-0 mt-0.5"
                        style={{ color: "rgb(var(--primary))" }}
                      />
                      <span
                        className="text-sm"
                        style={{ color: "var(--text)" }}
                      >
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <GenericButton
                label={plan.cta}
                href={plan.ctaHref}
                variant={plan.variant}
                className="w-full"
              />
            </Card>
          );
        })}
      </div>
    </>
  );
}
