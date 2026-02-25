import type { Metadata } from "next";
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

  return {
    title: t("metadata.contactTitle"),
    description: t("metadata.contactDescription"),
    openGraph: {
      title: `${t("metadata.contactTitle")} – SecureOps`,
      description: t("metadata.contactDescription"),
      url: `${SITE_URL}/${locale}/${SLUG_MAP[l].contact}`,
      images: [
        {
          url: `${SITE_URL}/logo.png`,
          width: 512,
          height: 512,
          alt: "SecureOps",
          type: "image/png",
        },
      ],
    },
    alternates: {
      canonical: `${SITE_URL}/${locale}/${SLUG_MAP[l].contact}`,
      languages: {
        ...Object.fromEntries(
          LOCALES.map((loc) => [
            loc,
            `${SITE_URL}/${loc}/${SLUG_MAP[loc].contact}`,
          ]),
        ),
        "x-default": `${SITE_URL}/${DEFAULT_LOCALE}/${SLUG_MAP[DEFAULT_LOCALE].contact}`,
      },
    },
  };
}

export default function ContactLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
