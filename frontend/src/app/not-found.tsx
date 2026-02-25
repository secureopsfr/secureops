import type { Metadata } from "next";
import Link from "next/link";
import { DEFAULT_LOCALE } from "../i18n/config";

export const metadata: Metadata = {
  title: "Page non trouvée",
  description: "La page demandée n'existe pas ou a été déplacée.",
  robots: { index: false, follow: true },
};

/**
 * Fallback 404 (hors [locale]) : style aligné sur le design system.
 * En pratique le middleware redirige vers /[locale]/…, donc c'est [locale]/not-found qui s'affiche.
 */
export default function RootNotFound() {
  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center gap-6 p-6 bg-[var(--color-bg)] text-[var(--color-text)]"
      id="main"
    >
      <p
        className="text-6xl md:text-8xl font-bold tracking-tighter text-[rgb(var(--primary))] opacity-90"
        aria-hidden
      >
        404
      </p>
      <h1 className="text-2xl md:text-3xl font-semibold text-center">
        Page non trouvée
      </h1>
      <p className="text-[var(--color-text-muted)] text-center max-w-md">
        La page demandée n&apos;existe pas ou a été déplacée.
      </p>
      <Link
        href={`/${DEFAULT_LOCALE}`}
        className="rounded-lg px-5 py-2.5 text-sm font-medium bg-[rgb(var(--primary))] text-[var(--color-btn-primary-text)] no-underline hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)]"
      >
        Retour à l&#39;accueil
      </Link>
    </main>
  );
}
