"use client";

import { usePathname } from "next/navigation";
import Header from "./Header";
import Footer from "./Footer";
import { GenericButton } from "./buttons";
import AnimateInView from "./AnimateInView";
import { useLanguage } from "./LanguageProvider";
import { LOCALES, DEFAULT_LOCALE, type Locale } from "../i18n/config";
import { Home, Mail, CreditCard } from "lucide-react";

/**
 * Contenu de la page 404 : Header, message stylé, actions, Footer.
 * Utilise le pathname pour déduire la locale (premier segment).
 */
export default function NotFoundContent() {
  const pathname = usePathname();
  const segments = pathname?.split("/").filter(Boolean) ?? [];
  const firstSegment = segments[0];
  const locale: Locale =
    firstSegment && LOCALES.includes(firstSegment as Locale)
      ? (firstSegment as Locale)
      : DEFAULT_LOCALE;

  const { t, lp } = useLanguage();

  return (
    <>
      <Header />
      <main id="main">
        <AnimateInView
          initialOnly
          className="min-h-[calc(100vh-var(--header-height)-200px)] flex flex-col items-center justify-center px-4 py-16 landing-section"
          as="section"
        >
          <div className="max-w-[560px] mx-auto text-center">
            {/* Code 404 mis en avant */}
            <p
              className="text-6xl md:text-8xl font-bold tracking-tighter text-[rgb(var(--primary))] opacity-90 mb-4"
              aria-hidden
            >
              {t("notFound.code")}
            </p>
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text)] mb-3">
              {t("notFound.title")}
            </h1>
            <p className="text-[var(--color-text-muted)] text-base md:text-lg leading-relaxed mb-10">
              {t("notFound.description")}
            </p>

            {/* Actions */}
            <div className="flex flex-wrap justify-center gap-3">
              <GenericButton
                label={t("notFound.backHome")}
                href={lp("/")}
                variant="primary"
                icon={<Home className="w-4 h-4" />}
                iconPosition="left"
              />
              <GenericButton
                label={t("notFound.contact")}
                href={lp("/contact")}
                variant="outline"
                icon={<Mail className="w-4 h-4" />}
                iconPosition="left"
              />
              <GenericButton
                label={t("notFound.pricing")}
                href={lp("/tarifs")}
                variant="outline"
                icon={<CreditCard className="w-4 h-4" />}
                iconPosition="left"
              />
            </div>
          </div>
        </AnimateInView>
      </main>
      <Footer locale={locale} />
    </>
  );
}
