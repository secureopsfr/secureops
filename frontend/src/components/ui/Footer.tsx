import Link from "next/link";
import { localePath, type Locale } from "../../i18n/config";
import { getTranslation } from "../../i18n/server";
import CopyEmailButton from "../CopyEmailButton";
import AnimateInView from "../AnimateInView";

const CONTACT_EMAIL = "contact@secureops.fr";

export default function Footer({ locale }: { locale: string }) {
  const t = getTranslation(locale as Locale);
  const lp = (internalPath: string) =>
    localePath(locale as Locale, internalPath);

  return (
    <AnimateInView
      as="footer"
      id="site-footer"
      role="contentinfo"
      className="border-t border-[var(--color-border)] pt-10 px-4 pb-4 text-[var(--color-text-muted)] text-sm text-center md:text-left mt-6 landing-reveal-footer"
    >
      <div className="max-w-[1200px] mx-auto px-4">
        <div className="flex flex-wrap justify-center md:justify-between gap-12 pl-0 md:pl-4 footer-columns">
          {/* Brand column */}
          <div className="flex-[1_1_280px] max-w-[400px] text-center md:text-left">
            <h2 className="text-lg font-semibold text-[var(--color-text)] mb-3">
              Secure
              <span className="text-[rgb(var(--primary))]">Ops</span>
            </h2>
            <p className="text-[var(--color-text-muted)] leading-relaxed">
              {t("footer.description")}
            </p>
          </div>

          {/* Contact column */}
          <div className="flex-[1_1_280px] max-w-[400px] text-center md:text-left">
            <h3 className="text-base font-semibold text-[var(--color-text)] mb-3">
              {t("footer.contact")}
            </h3>
            <p className="text-[var(--color-text-muted)] leading-relaxed">
              {t("footer.emailLabel")}{" "}
              <CopyEmailButton
                email={CONTACT_EMAIL}
                copyLabel={t("footer.copyEmail")}
                copiedLabel={t("footer.emailCopied")}
                ariaLabel={t("footer.copyEmailAria")}
              />
              <br />
              <span>{t("footer.orDirectly")} </span>
              <Link
                href={lp("/contact")}
                className="text-[rgb(var(--primary))] no-underline hover:underline"
              >
                {t("footer.contactForm")}
              </Link>
            </p>
          </div>
        </div>

        {/* Copyright line */}
        <div className="mt-8 text-center text-[var(--color-text-muted)] text-xs footer-copyright">
          <p>
            &copy; {new Date().getFullYear()} SecureOps.{" "}
            {t("footer.allRightsReserved")}{" "}
            <Link
              href={lp("/politique-confidentialite")}
              className="text-[rgb(var(--primary))] no-underline hover:underline"
            >
              {t("footer.privacyPolicy")}
            </Link>
          </p>
        </div>
      </div>
    </AnimateInView>
  );
}
