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

/** Ordre des catégories de tests (aligné avec le PDF). */
export const CHECKED_CATEGORIES_ORDER: readonly string[] = [
  "tls",
  "headers",
  "cookies",
  "exposed_files",
  "directory_listing",
  "robots_txt",
  "tech_fingerprinting",
];

export const CATEGORY_I18N_MAP: Record<string, string> = {
  tls: "scanner.categoryTls",
  headers: "scanner.categoryHeaders",
  cookies: "scanner.categoryCookies",
  exposed_files: "scanner.categoryExposedFiles",
  directory_listing: "scanner.categoryDirectoryListing",
  robots_txt: "scanner.categoryRobotsTxt",
  tech_fingerprinting: "scanner.categoryTechFingerprinting",
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
