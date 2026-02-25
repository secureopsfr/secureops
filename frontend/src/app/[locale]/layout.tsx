import "../globals.css";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  SITE_URL,
  LOCALES,
  DEFAULT_LOCALE,
  type Locale,
} from "../../i18n/config";
import { getTranslation } from "../../i18n/server";
import { Providers } from "../../components/Providers";
const SITE_NAME = "SecureOps";

/**
 * Tell Next.js which locale values are valid so it can statically generate
 * both /fr and /en versions.
 */
export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);

  const baseUrl = SITE_URL.startsWith("http")
    ? SITE_URL
    : `https://${SITE_URL}`;
  return {
    metadataBase: new URL(baseUrl),
    title: {
      default: t("metadata.siteTitle"),
      template: `%s | ${SITE_NAME}`,
    },
    description: t("metadata.siteDescription"),
    keywords: [
      "cybersécurité",
      "cybersecurity",
      "SaaS",
      "vulnérabilités",
      "vulnerabilities",
      "SecureOps",
    ],
    authors: [{ name: SITE_NAME }],
    creator: SITE_NAME,
    publisher: SITE_NAME,
    applicationName: SITE_NAME,

    /** ── Manifest PWA ── */
    manifest: `/api/manifest/${locale}`,

    /** ── Icons / Favicons ── */
    icons: {
      icon: [
        { url: "/favicon.ico", sizes: "any" },
        { url: "/favicon-96x96.png", sizes: "96x96", type: "image/png" },
        { url: "/logo.svg", type: "image/svg+xml" },
      ],
      apple: { url: "/apple-touch-icon.png", sizes: "180x180" },
    },

    /** ── Open Graph (Facebook, LinkedIn, Discord…) ── */
    openGraph: {
      type: "website",
      locale: locale === "fr" ? "fr_FR" : "en_US",
      alternateLocale: locale === "fr" ? "en_US" : "fr_FR",
      url: `${SITE_URL}/${locale}`,
      siteName: SITE_NAME,
      title: t("metadata.siteTitle"),
      description: t("metadata.siteDescription"),
      images: [
        {
          url: `${SITE_URL}/og-image.png`,
          width: 1200,
          height: 630,
          alt: SITE_NAME,
          type: "image/png",
        },
        {
          url: `${SITE_URL}/logo.png`,
          width: 512,
          height: 512,
          alt: SITE_NAME,
          type: "image/png",
        },
      ],
    },

    /** ── Twitter / X Card ── */
    twitter: {
      card: "summary_large_image",
      title: t("metadata.siteTitle"),
      description: t("metadata.siteDescription"),
      ...(process.env.NEXT_PUBLIC_TWITTER_SITE && {
        site: process.env.NEXT_PUBLIC_TWITTER_SITE,
      }),
      ...(process.env.NEXT_PUBLIC_TWITTER_CREATOR && {
        creator: process.env.NEXT_PUBLIC_TWITTER_CREATOR,
      }),
      images: [
        {
          url: `${SITE_URL}/og-image.png`,
          width: 1200,
          height: 630,
          alt: SITE_NAME,
        },
        { url: `${SITE_URL}/logo.png`, alt: SITE_NAME },
      ],
    },

    /** ── Robots ── */
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        "max-video-preview": -1,
        "max-image-preview": "large",
        "max-snippet": -1,
      },
    },

    /** ── Canonical + hreflang ── */
    alternates: {
      canonical: `${SITE_URL}/${locale}`,
      languages: {
        fr: `${SITE_URL}/fr`,
        en: `${SITE_URL}/en`,
        "x-default": `${SITE_URL}/${DEFAULT_LOCALE}`,
      },
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // Validate the locale
  if (!LOCALES.includes(locale as Locale)) {
    notFound();
  }

  const t = getTranslation(locale as Locale);

  /* ── Global JSON-LD: Organization (appears on every page) ── */
  const organizationJsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: SITE_NAME,
    url: SITE_URL,
    logo: `${SITE_URL}/logo.png`,
    description: t("metadata.siteDescription"),
    email: "contact@secureops.io",
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "customer support",
      email: "contact@secureops.io",
      availableLanguage: ["French", "English"],
    },
  };

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        {/* Anti-flash script: applies theme BEFORE first render */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t)}}catch(e){}})()`,
          }}
        />
        {/* Global structured data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(organizationJsonLd),
          }}
        />
      </head>
      <body suppressHydrationWarning>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-[var(--color-surface)] focus:text-[var(--color-text)] focus:rounded focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))]"
        >
          {locale === "fr" ? "Aller au contenu" : "Skip to content"}
        </a>
        <Providers locale={locale as Locale}>{children}</Providers>
      </body>
    </html>
  );
}
