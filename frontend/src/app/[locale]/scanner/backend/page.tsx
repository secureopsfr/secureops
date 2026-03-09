import type { Metadata } from "next";
import Header from "../../../../components/ui/Header";
import Footer from "../../../../components/ui/Footer";
import ScanTypePageContent from "../../../../components/scan/ScanTypePageContent";
import { getTranslation } from "../../../../i18n/server";
import { SITE_URL, SLUG_MAP, type Locale } from "../../../../i18n/config";

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

  return (
    <>
      <Header />
      <main
        id="main"
        className="min-h-screen py-6 w-full flex justify-center scanner-page"
      >
        <div className="w-full max-w-[1400px] px-8">
          <ScanTypePageContent
            titleKey="scanner.backend.title"
            placeholderKey="scanner.backend.placeholder"
            docSlug="scan-backend"
            filterScanType="backend"
          />
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
