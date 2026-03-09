import type { Metadata } from "next";
import Header from "../../../../components/ui/Header";
import ScannerBackButton from "../../../../components/scan/ScannerBackButton";
import Footer from "../../../../components/ui/Footer";
import ScannerGestion from "../../../../components/scan/ScannerGestion";
import { getTranslation } from "../../../../i18n/server";
import {
  SITE_URL,
  SLUG_MAP,
  SCANNER_SUBPATH_MAP,
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
          </div>
          <ScannerGestion />
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
