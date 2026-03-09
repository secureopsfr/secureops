import type { Metadata } from "next";
import Link from "next/link";
import { FileText } from "lucide-react";
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
    title: t("scanner.scansPersonnalises.metaTitle"),
    description: t("scanner.scansPersonnalises.metaDesc"),
    openGraph: {
      title: `${t("scanner.scansPersonnalises.metaTitle")} – SecureOps`,
      url: `${SITE_URL}/${locale}/${SLUG_MAP[l].scanner}/scans-personnalises`,
    },
  };
}

export default async function ScannerScansPersonnalisesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);

  return (
    <>
      <Header />
      <main
        id="main"
        className="min-h-screen py-6 w-full flex justify-center scanner-page"
      >
        <div className="w-full max-w-[1400px] px-8">
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
            <h1 className="page-title mb-4">
              {t("scanner.scansPersonnalises.title")}
            </h1>
            <p className="text-[var(--color-text-muted)] max-w-xl mx-auto">
              {t("scanner.scansPersonnalises.placeholder")}
            </p>
            <Link
              href={localePath(
                locale as Locale,
                "/scanner/docs/scans-personnalises",
              )}
              className="group mt-4 inline-flex text-sm text-[rgb(var(--primary))] no-underline"
            >
              <span className="inline-flex items-center gap-1.5 border-b-2 border-transparent group-hover:border-[rgb(var(--primary))]">
                <FileText className="w-4 h-4" />
                {t("scanner.docsLink")}
              </span>
            </Link>
          </div>
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
