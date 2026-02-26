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
  emoji: string;
  labelKey: string;
} {
  if (score >= 80) return { emoji: "🟢", labelKey: "scanner.scoreGood" };
  if (score >= 50) return { emoji: "🟡", labelKey: "scanner.scoreMedium" };
  return { emoji: "🔴", labelKey: "scanner.scoreLow" };
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
