import type { Metadata } from "next";
import { getTranslation } from "../../../i18n/server";
import { SITE_URL, SLUG_MAP, type Locale } from "../../../i18n/config";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);

  return {
    title: t("metadata.registerTitle"),
    description: t("metadata.registerDescription"),
    robots: { index: true, follow: true },
    alternates: {
      canonical: `${SITE_URL}/${locale}/${SLUG_MAP[locale as Locale].inscription}`,
    },
  };
}

export default function InscriptionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
