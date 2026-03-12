/**
 * Utilitaires d'export des résultats de scan multi-pages (CSV, JSON, XLSX).
 */

import * as XLSX from "xlsx";
import type {
  MultiScanResult,
  PageScanResult,
  ScanFinding,
} from "../services/scanService";
import {
  BOM,
  CSV_SEP,
  buildScanBaseFilename,
  downloadBlob,
  escapeCsvCell,
} from "./exportScan";

type EnrichedFinding = ScanFinding & {
  page_url: string;
  page_score: number | null;
  page_error?: string;
};

function flattenFindings(result: MultiScanResult): EnrichedFinding[] {
  const rows: EnrichedFinding[] = [];
  for (const page of result.page_results ?? []) {
    const findings = page.findings ?? [];
    if (findings.length === 0 && page.error) {
      rows.push({
        id: "",
        category: "",
        severity: "",
        title: "",
        evidence: "",
        recommendation: "",
        references: [],
        page_url: page.url,
        page_score: typeof page.score === "number" ? page.score : null,
        page_error: page.error,
      });
      continue;
    }
    for (const finding of findings) {
      rows.push({
        ...finding,
        page_url: page.url,
        page_score: typeof page.score === "number" ? page.score : null,
      });
    }
  }
  return rows;
}

function getPageSummaryRows(
  pageResults: PageScanResult[],
): (string | number)[][] {
  return pageResults.map((page) => [
    page.url,
    page.score,
    page.findings?.length ?? 0,
    page.total_tests_count ?? 0,
    page.error ?? "",
  ]);
}

export function exportMultiToCsv(result: MultiScanResult): void {
  const headers = [
    "URL de page",
    "Score page",
    "Erreur page",
    "ID finding",
    "Catégorie",
    "Sévérité",
    "Titre",
    "Preuve",
    "Recommandation",
    "Références",
  ];

  const rows: string[][] = [headers];
  for (const row of flattenFindings(result)) {
    rows.push([
      row.page_url,
      row.page_score == null ? "" : String(row.page_score),
      row.page_error ?? "",
      row.id,
      row.category,
      row.severity,
      row.title,
      row.evidence,
      row.recommendation,
      (row.references ?? []).join(" | "),
    ]);
  }

  const csvContent =
    BOM + rows.map((row) => row.map(escapeCsvCell).join(CSV_SEP)).join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
  downloadBlob(
    blob,
    `${buildScanBaseFilename(result.base_url, "scan-multi")}.csv`,
  );
}

export function exportMultiToJson(result: MultiScanResult): void {
  const json = JSON.stringify(
    {
      synthese: {
        base_url: result.base_url,
        timestamp: result.timestamp,
        duration: result.duration,
        score_global: result.score_global,
        pages_count: result.urls.length,
      },
      urls: result.urls,
      page_results: result.page_results,
    },
    null,
    2,
  );
  const blob = new Blob([json], { type: "application/json" });
  downloadBlob(
    blob,
    `${buildScanBaseFilename(result.base_url, "scan-multi")}.json`,
  );
}

export function exportMultiToXlsx(result: MultiScanResult): void {
  const wb = XLSX.utils.book_new();

  const summaryData = [
    ["URL de base", result.base_url],
    ["Date", result.timestamp],
    ["Durée (s)", result.duration],
    ["Score global", result.score_global],
    ["Nombre de pages", result.urls.length],
  ];
  const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(wb, wsSummary, "Résumé");

  const pagesHeaders = [
    "URL de page",
    "Score page",
    "Nb findings",
    "Nb tests",
    "Erreur",
  ];
  const wsPages = XLSX.utils.aoa_to_sheet([
    pagesHeaders,
    ...getPageSummaryRows(result.page_results),
  ]);
  XLSX.utils.book_append_sheet(wb, wsPages, "Pages");

  const findingsHeaders = [
    "URL de page",
    "Score page",
    "Erreur page",
    "ID finding",
    "Catégorie",
    "Sévérité",
    "Titre",
    "Preuve",
    "Recommandation",
    "Références",
  ];
  const findingsRows = flattenFindings(result).map((row) => [
    row.page_url,
    row.page_score ?? "",
    row.page_error ?? "",
    row.id,
    row.category,
    row.severity,
    row.title,
    row.evidence,
    row.recommendation,
    (row.references ?? []).join(" | "),
  ]);
  const wsFindings = XLSX.utils.aoa_to_sheet([
    findingsHeaders,
    ...findingsRows,
  ]);
  XLSX.utils.book_append_sheet(wb, wsFindings, "Findings");

  const xlsxBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
  const blob = new Blob([xlsxBuffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  downloadBlob(
    blob,
    `${buildScanBaseFilename(result.base_url, "scan-multi")}.xlsx`,
  );
}

export type MultiExportFormat = "csv" | "json" | "xlsx";

const MULTI_EXPORT_FUNCTIONS: Record<
  MultiExportFormat,
  (result: MultiScanResult) => void
> = {
  csv: exportMultiToCsv,
  json: exportMultiToJson,
  xlsx: exportMultiToXlsx,
};

export function exportMultiScanResult(
  result: MultiScanResult,
  format: MultiExportFormat,
): void {
  MULTI_EXPORT_FUNCTIONS[format](result);
}
