import type { Metadata } from "next";
import { getTranslation } from "../../../i18n/server";
import { SITE_URL, type Locale } from "../../../i18n/config";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);

  return {
    title: t("metadata.loginTitle"),
    description: t("metadata.loginDescription"),
    robots: { index: false, follow: true },
    alternates: { canonical: `${SITE_URL}/${locale}` },
  };
}

export default function ConnexionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
