import { localePath, type Locale } from "../i18n/config";
import { getTranslation } from "../i18n/server";
import { Card } from "./cards";
import PricingCards from "./PricingCards";
import type { PricingPlan } from "./PricingCards";
import AnimateInView from "./AnimateInView";

export default function PricingContent({ locale }: { locale: string }) {
  const t = getTranslation(locale as Locale);
  const lp = (p: string) => localePath(locale as Locale, p);

  const PLANS: PricingPlan[] = [
    {
      name: t("pricing.starter.name"),
      description: t("pricing.starter.description"),
      monthlyPrice: "29€",
      yearlyPrice: "23€",
      period: t("pricing.perMonth"),
      features: [
        t("pricing.starter.features.0"),
        t("pricing.starter.features.1"),
        t("pricing.starter.features.2"),
        t("pricing.starter.features.3"),
        t("pricing.starter.features.4"),
      ],
      cta: t("pricing.starter.cta"),
      ctaHref: lp("/inscription"),
      variant: "primary",
    },
    {
      name: t("pricing.pro.name"),
      description: t("pricing.pro.description"),
      monthlyPrice: "79€",
      yearlyPrice: "63€",
      period: t("pricing.perMonth"),
      features: [
        t("pricing.pro.features.0"),
        t("pricing.pro.features.1"),
        t("pricing.pro.features.2"),
        t("pricing.pro.features.3"),
        t("pricing.pro.features.4"),
        t("pricing.pro.features.5"),
        t("pricing.pro.features.6"),
      ],
      cta: t("pricing.pro.cta"),
      ctaHref: lp("/inscription"),
      variant: "primary",
      popular: true,
    },
    {
      name: t("pricing.enterprise.name"),
      description: t("pricing.enterprise.description"),
      monthlyPrice: t("pricing.custom"),
      yearlyPrice: t("pricing.custom"),
      period: "",
      features: [
        t("pricing.enterprise.features.0"),
        t("pricing.enterprise.features.1"),
        t("pricing.enterprise.features.2"),
        t("pricing.enterprise.features.3"),
        t("pricing.enterprise.features.4"),
        t("pricing.enterprise.features.5"),
        t("pricing.enterprise.features.6"),
        t("pricing.enterprise.features.7"),
      ],
      cta: t("pricing.enterprise.cta"),
      ctaHref: lp("/contact"),
      variant: "secondary",
    },
  ];

  const FAQ = [
    { question: t("pricing.faq1Question"), answer: t("pricing.faq1Answer") },
    { question: t("pricing.faq2Question"), answer: t("pricing.faq2Answer") },
    { question: t("pricing.faq3Question"), answer: t("pricing.faq3Answer") },
  ];

  return (
    <>
      {/* Pricing */}
      <AnimateInView
        initialOnly
        delay={80}
        className="page-section landing-reveal-page"
        as="section"
      >
        <div className="page-container space-y-8">
          <div className="page-header">
            <h1 className="page-title">{t("pricing.title")}</h1>
            <p className="page-subtitle mt-4">{t("pricing.subtitle")}</p>
          </div>

          <h2 className="sr-only">{t("pricing.plansTitle")}</h2>
          {/* Client component: billing toggle + cards */}
          <PricingCards
            plans={PLANS}
            translations={{
              monthly: t("pricing.monthly"),
              yearly: t("pricing.yearly"),
              mostPopular: t("pricing.mostPopular"),
              billedYearly: t("pricing.billedYearly"),
            }}
          />
        </div>
      </AnimateInView>

      {/* FAQ — fully server-rendered */}
      <AnimateInView
        className="landing-section landing-reveal-stagger"
        as="section"
      >
        <div className="section-title">
          <h2>{t("pricing.faqTitle")}</h2>
        </div>
        <div
          className="grid"
          style={{
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {FAQ.map((item) => (
            <Card key={item.question} disableHover>
              <h3
                className="text-base font-semibold mb-2"
                style={{ color: "var(--text)" }}
              >
                {item.question}
              </h3>
              <p
                className="text-sm leading-relaxed"
                style={{ color: "var(--muted)" }}
              >
                {item.answer}
              </p>
            </Card>
          ))}
        </div>
      </AnimateInView>
    </>
  );
}
