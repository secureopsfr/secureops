import { NextRequest, NextResponse } from "next/server";
import {
  LOCALES,
  DEFAULT_LOCALE,
  EN_SLUG_TO_INTERNAL,
  SCANNER_SUBPATH_EN_TO_INTERNAL,
  type Locale,
} from "./i18n/config";

/**
 * Paths that should never get a locale prefix.
 */
const PUBLIC_FILES = /\.(.*)$/; // files with extensions
const IGNORED_PREFIXES = [
  "/_next",
  "/api",
  "/favicon.ico",
  "/robots.txt",
  "/sitemap.xml",
  "/logo",
];

function shouldIgnore(pathname: string): boolean {
  if (PUBLIC_FILES.test(pathname)) return true;
  return IGNORED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

/**
 * Detect the best locale from the Accept-Language header.
 */
function detectLocale(request: NextRequest): Locale {
  // 1. Check cookie preference
  const cookieLocale = request.cookies.get("locale")?.value;
  if (cookieLocale && LOCALES.includes(cookieLocale as Locale)) {
    return cookieLocale as Locale;
  }

  // 2. Parse Accept-Language
  const acceptLang = request.headers.get("accept-language") ?? "";
  const preferred = acceptLang
    .split(",")
    .map((part) => {
      const [lang, q] = part.trim().split(";q=");
      return {
        lang: lang.trim().split("-")[0].toLowerCase(),
        q: q ? parseFloat(q) : 1,
      };
    })
    .sort((a, b) => b.q - a.q);

  for (const { lang } of preferred) {
    if (LOCALES.includes(lang as Locale)) {
      return lang as Locale;
    }
  }

  return DEFAULT_LOCALE;
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip static files and internal paths
  if (shouldIgnore(pathname)) {
    return NextResponse.next();
  }

  const segments = pathname.split("/").filter(Boolean);
  const firstSegment = segments[0];

  // Check if pathname already starts with a known locale
  const hasLocale = LOCALES.includes(firstSegment as Locale);

  if (!hasLocale) {
    // No locale prefix → redirect to /{detectedLocale}{pathname}
    const locale = detectLocale(request);
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}${pathname}`;
    const response = NextResponse.redirect(url);
    response.cookies.set("locale", locale, {
      path: "/",
      maxAge: 365 * 24 * 60 * 60,
    });
    return response;
  }

  // Locale is present. Now check if we need to rewrite EN slugs.
  const locale = firstSegment as Locale;

  if (locale === "en" && segments.length >= 2) {
    const slug = segments[1];
    const internalSlug = EN_SLUG_TO_INTERNAL[slug];

    if (internalSlug) {
      // Rewrite /en/pricing → /en/tarifs (internal route)
      const url = request.nextUrl.clone();
      const remainingSegments = segments.slice(2);
      url.pathname = `/${locale}/${internalSlug}${remainingSegments.length ? "/" + remainingSegments.join("/") : ""}`;
      return NextResponse.rewrite(url);
    }

    // Scanner sub-paths: /en/scanner/overview → /en/scanner/vue-d-ensemble
    if (
      slug === "scanner" &&
      segments.length >= 3 &&
      SCANNER_SUBPATH_EN_TO_INTERNAL[segments[2]]
    ) {
      const url = request.nextUrl.clone();
      const internalSubpath = SCANNER_SUBPATH_EN_TO_INTERNAL[segments[2]];
      const afterSubpath = segments.slice(3);
      url.pathname = `/${locale}/scanner/${internalSubpath}${afterSubpath.length ? "/" + afterSubpath.join("/") : ""}`;
      return NextResponse.rewrite(url);
    }
  }

  // Set locale cookie for persistence
  const response = NextResponse.next();
  response.cookies.set("locale", locale, {
    path: "/",
    maxAge: 365 * 24 * 60 * 60,
  });
  return response;
}

export const config = {
  matcher: [
    /*
     * Match all paths except:
     * - _next/static, _next/image
     * - favicon.ico, sitemap.xml, robots.txt
     */
    "/((?!_next/static|_next/image|favicon\\.ico|sitemap\\.xml|robots\\.txt).*)",
  ],
};
