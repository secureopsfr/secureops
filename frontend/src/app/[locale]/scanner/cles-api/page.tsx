import type { Metadata } from "next";
import Link from "next/link";
import { FileText } from "lucide-react";
import Header from "../../../../components/ui/Header";
import Footer from "../../../../components/ui/Footer";
import ApiKeysContent from "../../../../components/scan/ApiKeysContent";
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
    title: t("scanner.apiPublique.metaTitle"),
    description: t("scanner.apiPublique.metaDesc"),
    openGraph: {
      title: `${t("scanner.apiPublique.metaTitle")} – SecureOps`,
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

  return (
    <>
      <Header />
      <main
        id="main"
        className="min-h-screen py-6 w-full flex justify-center scanner-page"
      >
        <div className="w-full max-w-[1335px] px-8">
          <div className="text-center max-w-2xl mx-auto mb-8">
            <h1 className="page-title mb-2">
              {getTranslation(locale as Locale)("scanner.apiPublique.title")}
            </h1>
            <p className="text-[var(--color-text-muted)] mb-3">
              {getTranslation(locale as Locale)("scanner.apiPublique.intro")}
            </p>
            <Link
              href={localePath(locale as Locale, "/scanner/docs/api")}
              className="inline-flex items-center gap-2 text-sm text-[rgb(var(--primary))] border-b border-transparent hover:border-[rgb(var(--primary))] transition-colors pb-0.5"
            >
              <FileText className="w-4 h-4 shrink-0" />
              {getTranslation(locale as Locale)("scanner.docsLink")}
            </Link>
          </div>
          <ApiKeysContent />
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
