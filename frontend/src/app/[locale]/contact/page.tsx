import type { Metadata } from "next";
import Header from "../../../components/ui/Header";
import Footer from "../../../components/ui/Footer";
import ContactForm from "../../../components/ContactForm";
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
  const slug = SLUG_MAP[l].contact;

  return {
    title: t("metadata.contactTitle"),
    description: t("metadata.contactDescription"),
    openGraph: {
      title: `${t("metadata.contactTitle")} – SecureOps`,
      description: t("metadata.contactDescription"),
      url: `${SITE_URL}/${locale}/${slug}`,
    },
    alternates: {
      canonical: `${SITE_URL}/${locale}/${slug}`,
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

export default async function ContactPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);
  const l = locale as Locale;
  const pageUrl = `${SITE_URL}/${locale}/${SLUG_MAP[l].contact}`;

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "SecureOps",
        item: `${SITE_URL}/${locale}`,
      },
      {
        "@type": "ListItem",
        position: 2,
        name: t("metadata.contactTitle"),
        item: pageUrl,
      },
    ],
  };

  const contactPageJsonLd = {
    "@context": "https://schema.org",
    "@type": "ContactPage",
    name: t("metadata.contactTitle"),
    description: t("metadata.contactDescription"),
    url: pageUrl,
    mainEntity: {
      "@type": "Organization",
      name: "SecureOps",
      url: SITE_URL,
      logo: `${SITE_URL}/logo.png`,
      email: "contact@secureops.io",
      contactPoint: {
        "@type": "ContactPoint",
        contactType: "customer support",
        email: "contact@secureops.io",
        url: pageUrl,
        availableLanguage: ["French", "English"],
      },
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(contactPageJsonLd) }}
      />
      <Header />
      <main id="main" className="min-h-screen">
        <ContactForm />
        <Footer locale={locale} />
      </main>
    </>
  );
}
