/**
 * i18n configuration – locales, default locale, slug mappings.
 */

/** URL publique du site (canonicals, sitemap, OG). En prod : HTTPS, domaine final. Jamais vide pour éviter Invalid URL au build. */
export const SITE_URL =
  process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

export const LOCALES = ["fr", "en"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "fr";

/** Slugs used in the file-system (always French). */
const INTERNAL_SLUGS = [
  "tarifs",
  "contact",
  "scanner",
  "connexion",
  "inscription",
  "confirmation",
  "mot-de-passe-oublie",
  "politique-confidentialite",
  "mon-compte",
  "admin",
] as const;

/**
 * Map internal (FR) slug → user-facing slug per locale.
 * French keeps the same slugs; English gets translated ones.
 */
export const SLUG_MAP: Record<Locale, Record<string, string>> = {
  fr: Object.fromEntries(INTERNAL_SLUGS.map((s) => [s, s])),
  en: {
    tarifs: "pricing",
    contact: "contact",
    scanner: "scanner",
    connexion: "login",
    inscription: "register",
    confirmation: "confirmation",
    "mot-de-passe-oublie": "forgot-password",
    "politique-confidentialite": "privacy-policy",
    "mon-compte": "my-account",
    admin: "admin",
  },
};

/**
 * Reverse map: user-facing EN slug → internal slug.
 * Used by middleware to rewrite incoming English URLs to internal routes.
 */
export const EN_SLUG_TO_INTERNAL: Record<string, string> = Object.fromEntries(
  Object.entries(SLUG_MAP.en)
    .filter(([internal, external]) => internal !== external)
    .map(([internal, external]) => [external, internal]),
);

/**
 * Build a locale-aware href.
 * @param locale  Current locale
 * @param internalPath  Internal path (e.g. "/tarifs", "/contact")
 * @returns Localised path (e.g. "/en/pricing", "/fr/tarifs")
 */
export function localePath(locale: Locale, internalPath: string): string {
  // Remove leading slash for processing
  const clean = internalPath.replace(/^\//, "");

  if (!clean) return `/${locale}`;

  // Split path: first segment is the page slug, rest is sub-path
  const [firstSegment, ...rest] = clean.split("/");

  const mappedSlug = SLUG_MAP[locale]?.[firstSegment] ?? firstSegment;
  const suffix = rest.length > 0 ? `/${rest.join("/")}` : "";

  return `/${locale}/${mappedSlug}${suffix}`;
}

/**
 * Given a full pathname (e.g. "/en/pricing") return the equivalent path in
 * another locale (e.g. "/fr/tarifs").
 */
export function switchLocalePath(
  currentPathname: string,
  targetLocale: Locale,
): string {
  const segments = currentPathname.split("/").filter(Boolean);

  // First segment is the current locale
  const currentLocale = segments[0] as Locale;
  const restSegments = segments.slice(1);

  if (restSegments.length === 0) return `/${targetLocale}`;

  const [firstSlug, ...remainingSegments] = restSegments;

  // Convert user-facing slug back to internal slug
  let internalSlug = firstSlug;
  if (currentLocale === "en") {
    internalSlug = EN_SLUG_TO_INTERNAL[firstSlug] ?? firstSlug;
  }

  // Map internal slug to target locale's slug
  const targetSlug = SLUG_MAP[targetLocale]?.[internalSlug] ?? internalSlug;

  const suffix =
    remainingSegments.length > 0 ? `/${remainingSegments.join("/")}` : "";

  return `/${targetLocale}/${targetSlug}${suffix}`;
}
