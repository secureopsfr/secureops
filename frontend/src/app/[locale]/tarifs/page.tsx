import type { Metadata } from "next";
import Header from "../../../components/ui/Header";
import Footer from "../../../components/ui/Footer";
import PricingContent from "../../../components/PricingContent";
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
    title: t("metadata.pricingTitle"),
    description: t("metadata.pricingDescription"),
    openGraph: {
      title: `${t("metadata.pricingTitle")} – SecureOps`,
      description: t("metadata.pricingDescription"),
      url: `${SITE_URL}/${locale}/${SLUG_MAP[l].tarifs}`,
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
      canonical: `${SITE_URL}/${locale}/${SLUG_MAP[l].tarifs}`,
      languages: {
        ...Object.fromEntries(
          LOCALES.map((loc) => [
            loc,
            `${SITE_URL}/${loc}/${SLUG_MAP[loc].tarifs}`,
          ]),
        ),
        "x-default": `${SITE_URL}/${DEFAULT_LOCALE}/${SLUG_MAP[DEFAULT_LOCALE].tarifs}`,
      },
    },
  };
}

export default async function TarifsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);
  const l = locale as Locale;
  const pageUrl = `${SITE_URL}/${locale}/${SLUG_MAP[l].tarifs}`;
  const signupUrl = `${SITE_URL}/${locale}/${SLUG_MAP[l].inscription}`;
  const contactUrl = `${SITE_URL}/${locale}/${SLUG_MAP[l].contact}`;

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
        name: t("metadata.pricingTitle"),
        item: pageUrl,
      },
    ],
  };

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: t("pricing.faq1Question"),
        acceptedAnswer: {
          "@type": "Answer",
          text: t("pricing.faq1Answer"),
        },
      },
      {
        "@type": "Question",
        name: t("pricing.faq2Question"),
        acceptedAnswer: {
          "@type": "Answer",
          text: t("pricing.faq2Answer"),
        },
      },
      {
        "@type": "Question",
        name: t("pricing.faq3Question"),
        acceptedAnswer: {
          "@type": "Answer",
          text: t("pricing.faq3Answer"),
        },
      },
    ],
  };

  const offersJsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: t("metadata.pricingTitle"),
    description: t("metadata.pricingDescription"),
    url: pageUrl,
    mainEntity: {
      "@type": "ItemList",
      numberOfItems: 3,
      itemListElement: [
        {
          "@type": "ListItem",
          position: 1,
          item: {
            "@type": "Product",
            name: t("pricing.starter.name"),
            description: t("pricing.starter.description"),
            url: signupUrl,
            offers: {
              "@type": "Offer",
              price: "29",
              priceCurrency: "EUR",
              priceSpecification: {
                "@type": "UnitPriceSpecification",
                price: "29",
                priceCurrency: "EUR",
                unitText: "MONTH",
              },
              availability: "https://schema.org/InStock",
              url: signupUrl,
            },
          },
        },
        {
          "@type": "ListItem",
          position: 2,
          item: {
            "@type": "Product",
            name: t("pricing.pro.name"),
            description: t("pricing.pro.description"),
            url: signupUrl,
            offers: {
              "@type": "Offer",
              price: "79",
              priceCurrency: "EUR",
              priceSpecification: {
                "@type": "UnitPriceSpecification",
                price: "79",
                priceCurrency: "EUR",
                unitText: "MONTH",
              },
              availability: "https://schema.org/InStock",
              url: signupUrl,
            },
          },
        },
        {
          "@type": "ListItem",
          position: 3,
          item: {
            "@type": "Product",
            name: t("pricing.enterprise.name"),
            description: t("pricing.enterprise.description"),
            url: contactUrl,
            offers: {
              "@type": "Offer",
              price: "0",
              priceCurrency: "EUR",
              availability: "https://schema.org/InStock",
              url: contactUrl,
              priceValidUntil: new Date(new Date().getFullYear() + 1, 0, 1)
                .toISOString()
                .split("T")[0],
              description:
                locale === "fr" ? "Sur devis personnalisé" : "Custom pricing",
            },
          },
        },
      ],
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
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(offersJsonLd) }}
      />
      <Header />
      <main id="main">
        <PricingContent locale={locale} />
      </main>
      <Footer locale={locale} />
    </>
  );
}
