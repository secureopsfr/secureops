import AnimateInView from "./AnimateInView";
import LandingScanBlock from "./landing/LandingScanBlock";
import { FeatureCard } from "./ui/cards";
import { getTranslation } from "../i18n/server";
import type { Locale } from "../i18n/config";

export default function HomeContent({ locale }: { locale: string }) {
  const t = getTranslation(locale as Locale);

  const FEATURES = [
    {
      title: t("home.feature1Title"),
      body: t("home.feature1Body"),
    },
    {
      title: t("home.feature2Title"),
      body: t("home.feature2Body"),
    },
    {
      title: t("home.feature3Title"),
      body: t("home.feature3Body"),
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
          <h1>
            {t("home.titleLine1")}
            <br />
            <span>{t("home.titleHighlight")}</span> {t("home.titleLine2")}
          </h1>
          <LandingScanBlock />
          <AnimateInView
            className="landing-section landing-reveal-stagger mt-16"
            as="div"
          >
            <div className="section-title">
              <h3>{t("home.featuresTitle")}</h3>
            </div>
            <div className="grid features-grid">
              {FEATURES.map((feature) => (
                <FeatureCard
                  key={feature.title}
                  title={feature.title}
                  body={feature.body}
                />
              ))}
            </div>
          </AnimateInView>
        </div>
      </AnimateInView>
    </>
  );
}
