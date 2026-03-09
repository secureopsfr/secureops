import type { Metadata } from "next";
import Link from "next/link";
import Header from "../../../../components/ui/Header";
import Footer from "../../../../components/ui/Footer";
import { getTranslation } from "../../../../i18n/server";
import {
  SITE_URL,
  SLUG_MAP,
  localePath,
  type Locale,
} from "../../../../i18n/config";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);
  const l = locale as Locale;

  return {
    title: t("scanner.clesApi.metaTitle"),
    description: t("scanner.clesApi.metaDesc"),
    openGraph: {
      title: `${t("scanner.clesApi.metaTitle")} – SecureOps`,
      url: `${SITE_URL}/${locale}/${SLUG_MAP[l].scanner}/cles-api`,
    },
  };
}

export default async function ScannerClesApiPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);
  const lp = (path: string) => localePath(locale as Locale, path);

  return (
    <>
      <Header />
      <main
        id="main"
        className="min-h-screen py-6 w-full flex justify-center scanner-page"
      >
        <div className="w-full max-w-[1400px] px-8">
          <Link
            href={lp("/scanner")}
            className="inline-flex items-center gap-1 text-[rgb(var(--primary))] no-underline hover:underline mb-4"
          >
            ← {t("scanner.hub.backToHub")}
          </Link>
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
            <h1 className="page-title mb-4">{t("scanner.clesApi.title")}</h1>
            <p className="text-[var(--color-text-muted)] max-w-xl mx-auto">
              {t("scanner.clesApi.placeholder")}
            </p>
          </div>
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
