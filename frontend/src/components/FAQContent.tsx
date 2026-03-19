"use client";

import Link from "next/link";
import AnimateInView from "./AnimateInView";
import { useLanguage } from "./LanguageProvider";

const FAQ_KEYS = [
  "q1Question",
  "q2Question",
  "q3Question",
  "q4Question",
  "q5Question",
  "q6Question",
] as const;

export default function FAQContent() {
  const { t, lp } = useLanguage();

  const items = FAQ_KEYS.map((qKey) => {
    const aKey = qKey.replace("Question", "Answer");
    return { question: t(`faqPage.${qKey}`), answer: t(`faqPage.${aKey}`) };
  });

  return (
    <AnimateInView
      initialOnly
      delay={80}
      className="page-section landing-reveal-page"
      as="section"
      aria-label={t("faqPage.title")}
    >
      <div className="page-container space-y-8">
        <div className="page-header text-center mb-4">
          <h1 className="page-title mb-2">{t("faqPage.title")}</h1>
          <p className="page-subtitle mt-0 max-w-2xl mx-auto">
            {t("faqPage.subtitle")}
          </p>
        </div>

        <div className="faq-list max-w-[720px] mx-auto space-y-3">
          {items.map((item, idx) => (
            <details
              key={idx}
              className="faq-item group border border-[var(--color-border)] rounded-lg overflow-hidden bg-[var(--color-surface-input)] hover:bg-[var(--color-surface-hover)] transition-colors"
            >
              <summary className="flex items-center justify-between gap-4 px-5 py-4 cursor-pointer list-none text-[var(--color-text)] font-medium">
                <span className="pr-4">{item.question}</span>
                <span
                  className="faq-chevron shrink-0 w-5 h-5 flex items-center justify-center text-[var(--muted)] transition-transform group-open:rotate-180"
                  aria-hidden
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="m6 9 6 6 6-6" />
                  </svg>
                </span>
              </summary>
              <div className="px-5 pt-4 pb-4 text-[var(--color-text-muted)] text-sm leading-relaxed border-t border-[var(--color-border)]">
                {item.answer}
              </div>
            </details>
          ))}
        </div>

        <p className="text-center text-[var(--color-text-muted)] text-sm">
          {t("faqPage.contactCta")}{" "}
          <Link
            href={lp("/contact")}
            className="text-[rgb(var(--primary))] no-underline hover:underline"
          >
            {t("faqPage.contactLink")}
          </Link>
        </p>
      </div>
    </AnimateInView>
  );
}
