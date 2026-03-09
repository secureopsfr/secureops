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
    title: t("scanner.backend.metaTitle"),
    description: t("scanner.backend.metaDesc"),
    openGraph: {
      title: `${t("scanner.backend.metaTitle")} – SecureOps`,
      url: `${SITE_URL}/${locale}/${SLUG_MAP[l].scanner}/backend`,
    },
  };
}

export default async function ScannerBackendPage({
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
            <h1 className="page-title mb-4">{t("scanner.backend.title")}</h1>
            <p className="text-[var(--color-text-muted)] max-w-xl mx-auto">
              {t("scanner.backend.placeholder")}
            </p>
            <Link
              href={localePath(locale as Locale, "/scanner/docs/scan-backend")}
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
