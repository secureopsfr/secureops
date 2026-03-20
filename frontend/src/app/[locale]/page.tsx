import type { Metadata } from "next";
import Header from "../../components/ui/Header";
import Footer from "../../components/ui/Footer";
import HomeContent from "../../components/HomeContent";
import { getTranslation } from "../../i18n/server";
import {
  SITE_URL,
  LOCALES,
  DEFAULT_LOCALE,
  SLUG_MAP,
  type Locale,
} from "../../i18n/config";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);

  return {
    title: t("metadata.homeTitle"),
    description: t("metadata.homeDescription"),
    openGraph: {
      title: t("metadata.homeTitle"),
      description: t("metadata.homeDescription"),
      url: `${SITE_URL}/${locale}`,
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
      canonical: `${SITE_URL}/${locale}`,
      languages: {
        ...Object.fromEntries(LOCALES.map((l) => [l, `${SITE_URL}/${l}`])),
        "x-default": `${SITE_URL}/${DEFAULT_LOCALE}`,
      },
    },
  };
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);

  const organizationJsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "SecureOps",
    url: SITE_URL,
    logo: `${SITE_URL}/logo.png`,
    description: t("metadata.siteDescription"),
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "customer support",
      email: "contact@secureops.fr",
      url: `${SITE_URL}/${locale}/${SLUG_MAP[locale as Locale].contact}`,
      availableLanguage: ["French", "English"],
    },
    sameAs: [],
  };

  const webSiteJsonLd = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "SecureOps",
    url: SITE_URL,
    description: t("metadata.siteDescription"),
    inLanguage: locale === "fr" ? "fr-FR" : "en-US",
    publisher: {
      "@type": "Organization",
      name: "SecureOps",
      logo: {
        "@type": "ImageObject",
        url: `${SITE_URL}/logo.png`,
      },
    },
  };

  const softwareJsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "SecureOps",
    applicationCategory: "SecurityApplication",
    operatingSystem: "Web",
    description: t("metadata.homeDescription"),
    url: `${SITE_URL}/${locale}`,
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(organizationJsonLd),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(webSiteJsonLd),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(softwareJsonLd),
        }}
      />
      <Header />
      <main id="main">
        <HomeContent locale={locale} />
      </main>
      <Footer locale={locale} />
    </>
  );
}
