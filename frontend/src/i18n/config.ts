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
 * Scanner sub-paths: internal (file-system) → locale-specific display.
 * FR keeps "vue-d-ensemble", EN uses "overview".
 */
export const SCANNER_SUBPATH_MAP: Record<Locale, Record<string, string>> = {
  fr: { "vue-d-ensemble": "vue-d-ensemble" },
  en: { "vue-d-ensemble": "overview" },
};

/** EN scanner sub-path → internal (for middleware rewrite). */
export const SCANNER_SUBPATH_EN_TO_INTERNAL: Record<string, string> = {
  overview: "vue-d-ensemble",
};

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

  // Scanner sub-paths: map vue-d-ensemble → overview for EN
  let suffix = "";
  if (rest.length > 0) {
    if (
      firstSegment === "scanner" &&
      rest[0] &&
      SCANNER_SUBPATH_MAP[locale]?.[rest[0]]
    ) {
      suffix = `/${SCANNER_SUBPATH_MAP[locale][rest[0]]}${rest.slice(1).length ? "/" + rest.slice(1).join("/") : ""}`;
    } else {
      suffix = `/${rest.join("/")}`;
    }
  }

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

  // Scanner sub-paths: EN "overview" → internal "vue-d-ensemble" → FR "vue-d-ensemble"
  let suffix = "";
  if (remainingSegments.length > 0) {
    let internalSubpath = remainingSegments[0];
    if (
      internalSlug === "scanner" &&
      currentLocale === "en" &&
      remainingSegments[0] &&
      SCANNER_SUBPATH_EN_TO_INTERNAL[remainingSegments[0]]
    ) {
      internalSubpath = SCANNER_SUBPATH_EN_TO_INTERNAL[remainingSegments[0]];
    }
    const targetSubpath =
      internalSlug === "scanner" && internalSubpath
        ? (SCANNER_SUBPATH_MAP[targetLocale]?.[internalSubpath] ??
          internalSubpath)
        : remainingSegments[0];
    suffix = `/${targetSubpath}${remainingSegments.length > 1 ? "/" + remainingSegments.slice(1).join("/") : ""}`;
  }

  return `/${targetLocale}/${targetSlug}${suffix}`;
}
