import type { Metadata } from "next";
import Link from "next/link";
import { FileText } from "lucide-react";
import Header from "../../../../components/ui/Header";
import Footer from "../../../../components/ui/Footer";
import ScannerGestion from "../../../../components/scan/ScannerGestion";
import { getTranslation } from "../../../../i18n/server";
import {
  SITE_URL,
  SLUG_MAP,
  SCANNER_SUBPATH_MAP,
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
    title: t("scanner.gestion.metaTitle"),
    description: t("scanner.gestion.metaDesc"),
    openGraph: {
      title: `${t("scanner.gestion.metaTitle")} – SecureOps`,
      url: `${SITE_URL}/${locale}/${SLUG_MAP[l].scanner}/${SCANNER_SUBPATH_MAP[l]["vue-d-ensemble"]}`,
    },
  };
}

export default async function ScannerVueEnsemblePage({
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
          <div className="text-center mb-6">
            <h1 className="page-title mb-2">
              {t("scanner.gestion.pageTitle")}
            </h1>
            <p className="page-subtitle mt-0 max-w-2xl mx-auto">
              {t("scanner.gestion.pageSubtitle")}
            </p>
            <Link
              href={localePath(locale as Locale, "/scanner/docs")}
              className="group mt-2 inline-flex text-sm text-[rgb(var(--primary))] no-underline"
            >
              <span className="inline-flex items-center gap-1.5 border-b-2 border-transparent group-hover:border-[rgb(var(--primary))]">
                <FileText className="w-4 h-4" />
                {t("scanner.docsLink")}
              </span>
            </Link>
          </div>
          <ScannerGestion />
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
