import type { Metadata } from "next";
import NotFoundContent from "../../components/NotFoundContent";

export const metadata: Metadata = {
  title: "Page non trouvée",
  description: "La page demandée n'existe pas ou a été déplacée.",
  robots: { index: false, follow: true },
};

/**
 * Page 404 pour les routes sous [locale] : même charte que le site (Header, Footer, i18n).
 * La locale effective est déduite côté client depuis le pathname.
 */
export default function NotFound() {
  return <NotFoundContent />;
}
