import type { Metadata } from "next";
import Header from "../../../components/ui/Header";
import Footer from "../../../components/ui/Footer";
import ScannerContent from "../../../components/scan/ScannerContent";
import { getTranslation } from "../../../i18n/server";
import {
  SITE_URL,
  LOCALES,
  DEFAULT_LOCALE,
  SLUG_MAP,
  type Locale,
} from "../../../i18n/config";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);
  const l = locale as Locale;
  const slug = SLUG_MAP[l].scanner;

  return {
    title: t("metadata.scannerTitle"),
    description: t("metadata.scannerDescription"),
    openGraph: {
      title: `${t("metadata.scannerTitle")} – SecureOps`,
      description: t("metadata.scannerDescription"),
      url: `${SITE_URL}/${locale}/${slug}`,
    },
    alternates: {
      canonical: `${SITE_URL}/${locale}/${slug}`,
      languages: {
        ...Object.fromEntries(
          LOCALES.map((loc) => [
            loc,
            `${SITE_URL}/${loc}/${SLUG_MAP[loc].scanner}`,
          ]),
        ),
        "x-default": `${SITE_URL}/${DEFAULT_LOCALE}/${SLUG_MAP[DEFAULT_LOCALE].scanner}`,
      },
    },
  };
}

export default async function ScannerPage({
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
          <ScannerContent />
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
