"use client";

import React, {
  createContext,
  useContext,
  useCallback,
  useState,
  useEffect,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import en from "../locales/en.json";
import fr from "../locales/fr.json";
import { localePath, switchLocalePath, type Locale } from "../i18n/config";
import { setToastTranslator } from "../utils/toastNotifications";

export type Language = Locale;

const translations: Record<Language, Record<string, unknown>> = { en, fr };

/**
 * Recursively access a nested key in a translation object.
 * e.g. getNestedValue(obj, "header.home") => obj.header.home
 */
function getNestedValue(obj: Record<string, unknown>, path: string): string {
  const keys = path.split(".");
  let current: unknown = obj;
  for (const key of keys) {
    if (
      current === null ||
      current === undefined ||
      typeof current !== "object"
    ) {
      return path; // fallback: return the key itself
    }
    current = (current as Record<string, unknown>)[key];
  }
  if (typeof current === "string") return current;
  return path; // fallback
}

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  /** Build a locale-prefixed path: lp("/tarifs") → "/fr/tarifs" */
  lp: (path: string) => string;
}

const LanguageContext = createContext<LanguageContextType>({
  language: "fr",
  setLanguage: () => {},
  t: (key: string) => key,
  lp: (path: string) => path,
});

export const useLanguage = () => useContext(LanguageContext);

export function LanguageProvider({
  children,
  initialLocale,
}: {
  children: React.ReactNode;
  initialLocale: Language;
}) {
  const [language, setLanguageState] = useState<Language>(initialLocale);
  const router = useRouter();
  const pathname = usePathname();

  // Keep <html lang> in sync
  useEffect(() => {
    document.documentElement.setAttribute("lang", language);
  }, [language]);

  // When locale in URL changes (e.g. navigation), sync state
  useEffect(() => {
    const segments = pathname.split("/").filter(Boolean);
    const urlLocale = segments[0] as Language | undefined;
    if (
      urlLocale &&
      (urlLocale === "fr" || urlLocale === "en") &&
      urlLocale !== language
    ) {
      setLanguageState(urlLocale);
    }
  }, [pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Switch language: navigates to the equivalent page in the target locale.
   */
  const setLanguage = useCallback(
    (lang: Language) => {
      if (lang === language) return;
      const targetPath = switchLocalePath(pathname, lang);
      setLanguageState(lang);
      router.push(targetPath);
    },
    [language, pathname, router],
  );

  /**
   * Translation function.
   * Supports simple interpolation: t("key", { name: "John" }) where the translation has {{name}}.
   */
  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      let result = getNestedValue(translations[language], key);
      if (params) {
        Object.entries(params).forEach(([paramKey, paramValue]) => {
          result = result.replace(
            new RegExp(`\\{\\{${paramKey}\\}\\}`, "g"),
            String(paramValue),
          );
        });
      }
      return result;
    },
    [language],
  );

  /** Build a locale-prefixed path. */
  const lp = useCallback(
    (path: string) => localePath(language, path),
    [language],
  );

  // Expose t to toast fallbacks (hors React) pour que les toasts suivent la langue
  useEffect(() => {
    setToastTranslator(t);
    return () => setToastTranslator((k: string) => k);
  }, [t]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, lp }}>
      {children}
    </LanguageContext.Provider>
  );
}
