import { GenericButton } from "./buttons";
import { TestimonialCard, FeatureCard } from "./ui/cards";
import AnimateInView from "./AnimateInView";
import { getTranslation } from "../i18n/server";
import { localePath, type Locale } from "../i18n/config";

const TRUSTED_LOGOS = [
  "ACME CORP",
  "FINTECHX",
  "GOVTECH",
  "CLOUDSAFE",
  "DATAFLOW",
];

export default function HomeContent({ locale }: { locale: string }) {
  const t = getTranslation(locale as Locale);

  const HIGHLIGHTS = [
    { title: t("home.highlight1Title"), body: t("home.highlight1Body") },
    { title: t("home.highlight2Title"), body: t("home.highlight2Body") },
    { title: t("home.highlight3Title"), body: t("home.highlight3Body") },
  ];

  const TESTIMONIALS = [
    {
      quote: t("home.testimonial1Quote"),
      author: t("home.testimonial1Author"),
    },
    {
      quote: t("home.testimonial2Quote"),
      author: t("home.testimonial2Author"),
    },
    {
      quote: t("home.testimonial3Quote"),
      author: t("home.testimonial3Author"),
    },
  ];

  return (
    <>
      <AnimateInView
        initialOnly
        delay={80}
        className="hero-wrapper landing-reveal-hero"
        as="section"
      >
        <div className="hero-content">
          <div className="badge">{t("home.badge")}</div>
          <h1>
            {t("home.titleLine1")}
            <br />
            <span>{t("home.titleHighlight")}</span> {t("home.titleLine2")}
          </h1>
          <p>{t("home.subtitle")}</p>
          <div className="actions">
            <GenericButton
              label={t("home.requestDemo")}
              href={localePath(locale as Locale, "/contact")}
              variant="primary"
            />
            <GenericButton
              label={t("home.viewDocs")}
              href={localePath(locale as Locale, "/tarifs")}
              variant="outline"
            />
          </div>
        </div>
      </AnimateInView>

      <AnimateInView
        className="landing-section landing-reveal-stagger"
        as="section"
      >
        <div className="logos">
          {TRUSTED_LOGOS.map((logo) => (
            <div key={logo}>{logo}</div>
          ))}
        </div>
      </AnimateInView>

      <h2 className="sr-only">{t("home.sectionsTitle")}</h2>
      <AnimateInView
        className="landing-section landing-reveal-stagger"
        as="section"
      >
        <div className="section-title">
          <h3>{t("home.featuresTitle")}</h3>
          <p>{t("home.featuresSub")}</p>
        </div>
        <div className="grid">
          {HIGHLIGHTS.map((highlight) => (
            <FeatureCard
              key={highlight.title}
              title={highlight.title}
              body={highlight.body}
            />
          ))}
        </div>
      </AnimateInView>

      <AnimateInView
        className="landing-section landing-reveal-stagger"
        as="section"
      >
        <div className="section-title">
          <h3>{t("home.trustTitle")}</h3>
        </div>
        <div className="grid">
          {TESTIMONIALS.map((testimonial, index) => (
            <TestimonialCard
              key={`${testimonial.author}-${index}`}
              quote={testimonial.quote}
              author={testimonial.author}
            />
          ))}
        </div>
      </AnimateInView>

      <AnimateInView
        className="landing-section landing-reveal-cta"
        as="section"
      >
        <div className="cta">
          <h3>{t("home.ctaTitle")}</h3>
          <p className="my-4 mx-auto max-w-[600px] text-muted-theme mb-8">
            {t("home.ctaSub")}
          </p>
          <GenericButton
            label={t("home.ctaBtn")}
            href={localePath(locale as Locale, "/contact")}
            variant="primary"
            className="!inline-flex !w-auto !py-2 !px-5 !text-sm"
          />
        </div>
      </AnimateInView>
    </>
  );
}
