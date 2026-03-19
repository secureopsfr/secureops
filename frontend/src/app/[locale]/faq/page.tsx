import type { Metadata } from "next";
import Header from "../../../components/ui/Header";
import Footer from "../../../components/ui/Footer";
import FAQContent from "../../../components/FAQContent";
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
  const slug = SLUG_MAP[l].faq;

  return {
    title: t("metadata.faqTitle"),
    description: t("metadata.faqDescription"),
    openGraph: {
      title: `${t("metadata.faqTitle")} – SecureOps`,
      description: t("metadata.faqDescription"),
      url: `${SITE_URL}/${locale}/${slug}`,
    },
    alternates: {
      canonical: `${SITE_URL}/${locale}/${slug}`,
      languages: {
        ...Object.fromEntries(
          LOCALES.map((loc) => [
            loc,
            `${SITE_URL}/${loc}/${SLUG_MAP[loc].faq}`,
          ]),
        ),
        "x-default": `${SITE_URL}/${DEFAULT_LOCALE}/${SLUG_MAP[DEFAULT_LOCALE].faq}`,
      },
    },
  };
}

export default async function FAQPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);
  const l = locale as Locale;
  const pageUrl = `${SITE_URL}/${locale}/${SLUG_MAP[l].faq}`;

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
        name: t("metadata.faqTitle"),
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
        name: t("faqPage.q1Question"),
        acceptedAnswer: { "@type": "Answer", text: t("faqPage.q1Answer") },
      },
      {
        "@type": "Question",
        name: t("faqPage.q2Question"),
        acceptedAnswer: { "@type": "Answer", text: t("faqPage.q2Answer") },
      },
      {
        "@type": "Question",
        name: t("faqPage.q3Question"),
        acceptedAnswer: { "@type": "Answer", text: t("faqPage.q3Answer") },
      },
      {
        "@type": "Question",
        name: t("faqPage.q4Question"),
        acceptedAnswer: { "@type": "Answer", text: t("faqPage.q4Answer") },
      },
      {
        "@type": "Question",
        name: t("faqPage.q5Question"),
        acceptedAnswer: { "@type": "Answer", text: t("faqPage.q5Answer") },
      },
      {
        "@type": "Question",
        name: t("faqPage.q6Question"),
        acceptedAnswer: { "@type": "Answer", text: t("faqPage.q6Answer") },
      },
    ],
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
      <Header />
      <main id="main" className="min-h-screen">
        <FAQContent />
      </main>
      <Footer locale={locale} />
    </>
  );
}
