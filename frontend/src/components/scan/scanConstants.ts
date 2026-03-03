/**
 * Constantes et helpers pour le scanner (catégories, sévérités, tri).
 */

import type { ScanFinding } from "../../services/scanService";

export const SEVERITY_ORDER = [
  "critical",
  "high",
  "medium",
  "low",
  "info",
] as const;

/** Nombre de checks par catégorie (fallback quand category_summaries absent, ex. historique). */
export const CHECKS_COUNT_FALLBACK: Record<string, number> = {
  tls: 4,
  headers: 6,
  cache: 5,
  cookies: 7,
  exposed_files: 13,
  directory_listing: 9,
  robots_txt: 5,
  tech_fingerprinting: 6,
  information_disclosure: 6,
  cors_cross_origin: 8,
};

/** Ordre des catégories de tests (aligné avec le PDF). */
export const CHECKED_CATEGORIES_ORDER: readonly string[] = [
  "tls",
  "headers",
  "cache",
  "cookies",
  "exposed_files",
  "directory_listing",
  "robots_txt",
  "tech_fingerprinting",
  "information_disclosure",
  "cors_cross_origin",
];

export const CATEGORY_I18N_MAP: Record<string, string> = {
  tls: "scanner.categoryTls",
  headers: "scanner.categoryHeaders",
  cache: "scanner.categoryCache",
  cookies: "scanner.categoryCookies",
  exposed_files: "scanner.categoryExposedFiles",
  directory_listing: "scanner.categoryDirectoryListing",
  robots_txt: "scanner.categoryRobotsTxt",
  tech_fingerprinting: "scanner.categoryTechFingerprinting",
  information_disclosure: "scanner.categoryInformationDisclosure",
  cors_cross_origin: "scanner.categoryCorsCrossOrigin",
};

export const SEVERITY_I18N_MAP: Record<string, string> = {
  critical: "scanner.severityCritical",
  high: "scanner.severityHigh",
  medium: "scanner.severityMedium",
  low: "scanner.severityLow",
  info: "scanner.severityInfo",
};

export function getCategoryKey(category: string): string {
  return CATEGORY_I18N_MAP[category] ?? category;
}

/** Clés i18n pour le résumé « ce qui a été vérifié » quand tout est OK. */
export const CATEGORY_SUMMARY_OK_I18N: Record<string, string> = {
  tls: "scanner.summaryTlsOk",
  headers: "scanner.summaryHeadersOk",
  cache: "scanner.summaryCacheOk",
  cookies: "scanner.summaryCookiesOk",
  exposed_files: "scanner.summaryExposedFilesOk",
  directory_listing: "scanner.summaryDirectoryListingOk",
  robots_txt: "scanner.summaryRobotsTxtOk",
  tech_fingerprinting: "scanner.summaryTechFingerprintingOk",
  information_disclosure: "scanner.summaryInformationDisclosureOk",
  cors_cross_origin: "scanner.summaryCorsCrossOriginOk",
};

export function getCategorySummaryOkKey(category: string): string {
  return CATEGORY_SUMMARY_OK_I18N[category] ?? "";
}

export function getSeverityKey(severity: string): string {
  return SEVERITY_I18N_MAP[severity] ?? severity;
}

export function getScoreBadge(score: number): {
  labelKey: string;
  ringColor: string;
} {
  if (score >= 80)
    return { labelKey: "scanner.scoreGood", ringColor: "rgb(var(--success))" };
  if (score >= 50)
    return {
      labelKey: "scanner.scoreMedium",
      ringColor: "rgb(var(--warning))",
    };
  return { labelKey: "scanner.scoreLow", ringColor: "rgb(var(--danger))" };
}

export function severitySort(a: ScanFinding, b: ScanFinding): number {
  const ia = SEVERITY_ORDER.indexOf(
    a.severity as (typeof SEVERITY_ORDER)[number],
  );
  const ib = SEVERITY_ORDER.indexOf(
    b.severity as (typeof SEVERITY_ORDER)[number],
  );
  const ai = ia === -1 ? 99 : ia;
  const bi = ib === -1 ? 99 : ib;
  return ai - bi;
}
