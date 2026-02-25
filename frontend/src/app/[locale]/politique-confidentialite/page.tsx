import type { Metadata } from "next";
import Header from "../../../components/Header";
import Footer from "../../../components/Footer";
import Link from "next/link";
import AnimateInView from "../../../components/AnimateInView";
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
  const slug = SLUG_MAP[l]["politique-confidentialite"];

  return {
    title: t("metadata.privacyTitle"),
    description: t("metadata.privacyDescription"),
    openGraph: {
      title: `${t("metadata.privacyTitle")} – SecureOps`,
      description: t("metadata.privacyDescription"),
      url: `${SITE_URL}/${locale}/${slug}`,
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
      canonical: `${SITE_URL}/${locale}/${slug}`,
      languages: {
        ...Object.fromEntries(
          LOCALES.map((loc) => [
            loc,
            `${SITE_URL}/${loc}/${SLUG_MAP[loc]["politique-confidentialite"]}`,
          ]),
        ),
        "x-default": `${SITE_URL}/${DEFAULT_LOCALE}/${SLUG_MAP[DEFAULT_LOCALE]["politique-confidentialite"]}`,
      },
    },
  };
}

export default async function PolitiqueConfidentialitePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslation(locale as Locale);
  const l = locale as Locale;
  const contactHref = `/${l}/${SLUG_MAP[l].contact}`;
  const pageUrl = `${SITE_URL}/${locale}/${SLUG_MAP[l]["politique-confidentialite"]}`;

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
        name: t("metadata.privacyTitle"),
        item: pageUrl,
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <Header />

      <main id="main" className="min-h-screen">
        <AnimateInView
          initialOnly
          delay={80}
          className="page-section landing-reveal-page"
          as="section"
        >
          <div className="page-container space-y-8">
            {/* Header */}
            <div className="page-header">
              <h1 className="page-title">{t("privacyPage.title")}</h1>
              <p className="page-subtitle mt-4">{t("privacyPage.subtitle")}</p>
            </div>

            {/* Content */}
            <div className="space-y-8 max-w-4xl mx-auto">
              <AnimateInView className="landing-reveal-privacy-block">
                <Section>
                  <SectionTitle>{t("privacyPage.policyTitle")}</SectionTitle>
                  <Paragraph>{t("privacyPage.intro")}</Paragraph>
                  <DynamicBulletList t={t} listKey="privacyPage.introItems" />
                </Section>
              </AnimateInView>

              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection1
                  t={t}
                  contactHref={contactHref}
                  siteHomeUrl={`${SITE_URL}/${locale}`}
                />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection2 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection3 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection4 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection5 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection6 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection7 t={t} contactHref={contactHref} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection8 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection9 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection10 t={t} />
              </AnimateInView>
              <AnimateInView className="landing-reveal-privacy-block">
                <PrivacySection11 t={t} contactHref={contactHref} />
              </AnimateInView>
            </div>
          </div>
        </AnimateInView>
      </main>

      <Footer locale={locale} />
    </>
  );
}

/* ---------- Privacy sub-sections ---------- */

type TFn = (key: string) => string;

function PrivacySection1({
  t,
  contactHref,
  siteHomeUrl,
}: {
  t: TFn;
  contactHref: string;
  siteHomeUrl: string;
}) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section1Title")}</SectionTitle>
      <Paragraph>
        {t("privacyPage.section1Text1")}{" "}
        <InlineLink href={siteHomeUrl} external>
          {siteHomeUrl}
        </InlineLink>
      </Paragraph>
      <Paragraph>{t("privacyPage.section1Text2")}</Paragraph>
      <Paragraph>
        {t("privacyPage.section1Text3")}{" "}
        <InlineLink href={contactHref}>
          {t("privacyPage.section1Text3Link")}
        </InlineLink>{" "}
        {t("privacyPage.section1Text3End")}
      </Paragraph>
    </Section>
  );
}

function PrivacySection2({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section2Title")}</SectionTitle>
      <Paragraph>{t("privacyPage.section2Intro")}</Paragraph>

      <SubTitle>{t("privacyPage.section2_1Title")}</SubTitle>
      <Paragraph>
        <Strong>{t("privacyPage.section2_1aTitle")}</Strong>
      </Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section2_1aItems" />
      <Paragraph>{t("privacyPage.section2_1aText")}</Paragraph>

      <Paragraph>
        <Strong>{t("privacyPage.section2_1bTitle")}</Strong>
      </Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section2_1bItems" />
      <Paragraph>{t("privacyPage.section2_1bText")}</Paragraph>

      <Paragraph>
        <Strong>{t("privacyPage.section2_1cTitle")}</Strong>
      </Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section2_1cItems" />

      <SubTitle>{t("privacyPage.section2_2Title")}</SubTitle>
      <Paragraph>{t("privacyPage.section2_2Intro")}</Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section2_2Items" />
      <Paragraph>
        <Strong>{t("privacyPage.section2_2Text")}</Strong>
        {t("privacyPage.section2_2TextEnd")}
      </Paragraph>
    </Section>
  );
}

function PrivacySection3({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section3Title")}</SectionTitle>
      <Paragraph>
        <Strong>{t("privacyPage.section3PurposeTitle")}</Strong>
      </Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section3PurposeItems" />
      <Paragraph>
        <Strong>{t("privacyPage.section3LegalTitle")}</Strong>
      </Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section3LegalItems" />
    </Section>
  );
}

function PrivacySection4({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section4Title")}</SectionTitle>
      <SubTitle>{t("privacyPage.section4_1Title")}</SubTitle>
      <Paragraph>{t("privacyPage.section4_1Text")}</Paragraph>
      <SubTitle>{t("privacyPage.section4_2Title")}</SubTitle>
      <Paragraph>{t("privacyPage.section4_2Intro")}</Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section4_2Items" />
      <Paragraph>{t("privacyPage.section4_2Text")}</Paragraph>
    </Section>
  );
}

function PrivacySection5({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section5Title")}</SectionTitle>
      <DynamicBulletList t={t} listKey="privacyPage.section5Items" />
    </Section>
  );
}

function PrivacySection6({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section6Title")}</SectionTitle>
      <Paragraph>{t("privacyPage.section6Intro")}</Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section6Items" />
    </Section>
  );
}

function PrivacySection7({ t, contactHref }: { t: TFn; contactHref: string }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section7Title")}</SectionTitle>
      <Paragraph>{t("privacyPage.section7Intro")}</Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section7Items" />
      <Paragraph>
        {t("privacyPage.section7Text")}{" "}
        <InlineLink href={contactHref}>
          {t("privacyPage.section7TextLink")}
        </InlineLink>{" "}
        {t("privacyPage.section7TextEnd")}
      </Paragraph>
    </Section>
  );
}

function PrivacySection8({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section8Title")}</SectionTitle>
      <Paragraph>
        <Strong>{t("privacyPage.section8Current")}</Strong>
        {t("privacyPage.section8CurrentText")}
      </Paragraph>
      <Paragraph>
        <Strong>{t("privacyPage.section8Future")}</Strong>
        {t("privacyPage.section8FutureText")}
      </Paragraph>
    </Section>
  );
}

function PrivacySection9({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section9Title")}</SectionTitle>
      <Paragraph>{t("privacyPage.section9Text1")}</Paragraph>
      <Paragraph>{t("privacyPage.section9Text2")}</Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section9Items" />
    </Section>
  );
}

function PrivacySection10({ t }: { t: TFn }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section10Title")}</SectionTitle>
      <Paragraph>{t("privacyPage.section10Intro")}</Paragraph>
      <DynamicBulletList t={t} listKey="privacyPage.section10Items" />
      <Paragraph>{t("privacyPage.section10Text")}</Paragraph>
    </Section>
  );
}

function PrivacySection11({ t, contactHref }: { t: TFn; contactHref: string }) {
  return (
    <Section>
      <SectionTitle>{t("privacyPage.section11Title")}</SectionTitle>
      <Paragraph>
        {t("privacyPage.section11Text")}{" "}
        <InlineLink href={contactHref}>
          {t("privacyPage.section11TextLink")}
        </InlineLink>{" "}
        {t("privacyPage.section11TextEnd")}
      </Paragraph>
    </Section>
  );
}

/* ---------- Reusable UI components ---------- */

function Section({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-input)] p-6 sm:p-8 space-y-4">
      {children}
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xl font-bold text-[var(--color-text)] mb-2">
      {children}
    </h2>
  );
}

function SubTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-base font-semibold text-[var(--color-text)] mt-4 mb-1">
      {children}
    </h3>
  );
}

function Paragraph({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[var(--color-text-muted)] leading-relaxed">{children}</p>
  );
}

function Strong({ children }: { children: React.ReactNode }) {
  return (
    <strong className="text-[var(--color-text)] font-semibold">
      {children}
    </strong>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="list-disc list-inside space-y-1 text-[var(--color-text-muted)] pl-2">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

/**
 * Reads array translation keys (e.g. "privacyPage.section5Items")
 * by trying indices 0..19.
 */
function DynamicBulletList({ t, listKey }: { t: TFn; listKey: string }) {
  const items: string[] = [];
  for (let i = 0; i < 20; i++) {
    const val = t(`${listKey}.${i}`);
    if (val === `${listKey}.${i}`) break; // key not found
    items.push(val);
  }
  return <BulletList items={items} />;
}

function InlineLink({
  href,
  children,
  external,
}: {
  href: string;
  children: React.ReactNode;
  external?: boolean;
}) {
  return (
    <Link
      href={href}
      className="text-[rgb(var(--primary))] no-underline hover:underline"
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
    >
      {children}
    </Link>
  );
}
