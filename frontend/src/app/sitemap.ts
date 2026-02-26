import type { MetadataRoute } from "next";
import { SITE_URL, LOCALES, SLUG_MAP } from "../i18n/config";

/**
 * Public pages to include in the sitemap.
 * key = internal slug (matches the file-system route), value = config.
 */
const PUBLIC_PAGES: {
  internalSlug: string;
  changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"];
  priority: number;
}[] = [
  { internalSlug: "", changeFrequency: "weekly", priority: 1 },
  { internalSlug: "tarifs", changeFrequency: "monthly", priority: 0.8 },
  { internalSlug: "contact", changeFrequency: "monthly", priority: 0.7 },
  { internalSlug: "scanner", changeFrequency: "weekly", priority: 0.8 },
  {
    internalSlug: "politique-confidentialite",
    changeFrequency: "yearly",
    priority: 0.3,
  },
];

/** Date stable pour lastModified (build ou déploiement). */
const SITEMAP_LAST_MOD =
  (typeof process.env.VERCEL_BUILD_TIME !== "undefined" &&
    new Date(process.env.VERCEL_BUILD_TIME)) ||
  new Date();

export default function sitemap(): MetadataRoute.Sitemap {
  const entries: MetadataRoute.Sitemap = [];

  for (const page of PUBLIC_PAGES) {
    for (const locale of LOCALES) {
      const slug = page.internalSlug
        ? (SLUG_MAP[locale][page.internalSlug] ?? page.internalSlug)
        : "";

      const url = slug
        ? `${SITE_URL}/${locale}/${slug}`
        : `${SITE_URL}/${locale}`;

      // Build alternates for hreflang
      const languages: Record<string, string> = {};
      for (const altLocale of LOCALES) {
        const altSlug = page.internalSlug
          ? (SLUG_MAP[altLocale][page.internalSlug] ?? page.internalSlug)
          : "";
        languages[altLocale] = altSlug
          ? `${SITE_URL}/${altLocale}/${altSlug}`
          : `${SITE_URL}/${altLocale}`;
      }

      entries.push({
        url,
        lastModified: SITEMAP_LAST_MOD,
        changeFrequency: page.changeFrequency,
        priority: page.priority,
        alternates: {
          languages,
        },
      });
    }
  }

  return entries;
}
