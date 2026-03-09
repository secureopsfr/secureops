import { GenericButton } from "./buttons";
import AnimateInView from "./AnimateInView";
import { getTranslation } from "../i18n/server";
import { localePath, type Locale } from "../i18n/config";

export default function HomeContent({ locale }: { locale: string }) {
  const t = getTranslation(locale as Locale);

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
    </>
  );
}
