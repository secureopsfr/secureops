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
          <div className="page-header text-center mb-6 pt-6">
            <h1 className="page-title mb-2">
              {getTranslation(locale as Locale)("scanner.apiPublique.title")}
            </h1>
            <p className="page-subtitle mt-0 max-w-2xl mx-auto">
              {getTranslation(locale as Locale)("scanner.apiPublique.intro")}
            </p>
            <Link
              href={localePath(locale as Locale, "/scanner/docs/api")}
              className="group mt-2 inline-flex text-sm text-[rgb(var(--primary))] no-underline"
            >
              <span className="inline-flex items-center gap-1.5 border-b-2 border-transparent group-hover:border-[rgb(var(--primary))]">
                <FileText className="w-4 h-4 shrink-0" />
                {getTranslation(locale as Locale)("scanner.docsLink")}
              </span>
            </Link>
          </div>
          <ApiKeysContent />
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
