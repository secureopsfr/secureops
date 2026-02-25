/**
 * Server-side translation utilities.
 *
 * Usage in Server Components / generateMetadata:
 *   import { getTranslation } from "@/src/i18n/server";
 *   const t = getTranslation(locale);
 *   const title = t("metadata.homeTitle");
 */

import type { Locale } from "./config";
import en from "../locales/en.json";
import fr from "../locales/fr.json";

const dictionaries: Record<Locale, Record<string, unknown>> = { en, fr };

function getNestedValue(obj: Record<string, unknown>, path: string): string {
  const keys = path.split(".");
  let current: unknown = obj;
  for (const key of keys) {
    if (
      current === null ||
      current === undefined ||
      typeof current !== "object"
    ) {
      return path;
    }
    current = (current as Record<string, unknown>)[key];
  }
  if (typeof current === "string") return current;
  return path;
}

/**
 * Returns a translation function bound to the given locale.
 * Can be used in Server Components, `generateMetadata`, and `generateStaticParams`.
 */
export function getTranslation(locale: Locale) {
  const dict = dictionaries[locale] ?? dictionaries.fr;

  return function t(
    key: string,
    params?: Record<string, string | number>,
  ): string {
    let result = getNestedValue(dict, key);
    if (params) {
      Object.entries(params).forEach(([paramKey, paramValue]) => {
        result = result.replace(
          new RegExp(`\\{\\{${paramKey}\\}\\}`, "g"),
          String(paramValue),
        );
      });
    }
    return result;
  };
}
