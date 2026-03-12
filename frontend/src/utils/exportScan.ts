/**
 * Utilitaires d'export des résultats de scan (CSV, JSON, XLSX).
 */

import * as XLSX from "xlsx";
import type { ScanResult, ScanFinding } from "../services/scanService";
import {
  BOM,
  CSV_SEP,
  escapeCsvCell,
  buildScanBaseFilename,
  downloadBlob,
} from "./exportCore";

export { BOM, CSV_SEP, escapeCsvCell, buildScanBaseFilename, downloadBlob };

/**
 * Exporte les résultats en CSV (une ligne par finding).
 */
export function exportToCsv(result: ScanResult): void {
  const headers = [
    "ID",
    "Catégorie",
    "Sévérité",
    "Titre",
    "Preuve",
    "Recommandation",
    "Références",
  ];
  const rows: string[][] = [headers];

  for (const f of result.findings) {
    rows.push([
      f.id,
      f.category,
      f.severity,
      f.title,
      f.evidence,
      f.recommendation,
      (f.references ?? []).join(" | "),
    ]);
  }

  const csvContent =
    BOM + rows.map((row) => row.map(escapeCsvCell).join(CSV_SEP)).join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
  downloadBlob(blob, `${buildScanBaseFilename(result.url)}.csv`);
}

/**
 * Exporte les résultats en JSON (structure alignée sur la page de scan).
 */
export function exportToJson(result: ScanResult): void {
  const totalTestsCount =
    result.total_tests_count ??
    (result.category_summaries ?? []).reduce(
      (sum, s) => sum + (s.checks_count ?? 0),
      0,
    );

  const json = JSON.stringify(
    {
      synthese: {
        url: result.url,
        timestamp: result.timestamp,
        duration: result.duration,
        score: result.score,
        total_tests_count: totalTestsCount,
        findings_count: result.findings.length,
      },
      repartition: result.category_summaries ?? [],
      findings: result.findings,
    },
    null,
    2,
  );
  const blob = new Blob([json], { type: "application/json" });
  downloadBlob(blob, `${buildScanBaseFilename(result.url)}.json`);
}

/**
 * Exporte les résultats en XLSX (Excel) : une ligne par finding.
 */
export function exportToXlsx(result: ScanResult): void {
  const wb = XLSX.utils.book_new();
  const totalTestsCount =
    result.total_tests_count ??
    (result.category_summaries ?? []).reduce(
      (sum, s) => sum + (s.checks_count ?? 0),
      0,
    );

  // Feuille 1 : résumé
  const summaryData = [
    ["URL", result.url],
    ["Date", result.timestamp],
    ["Durée (s)", result.duration],
    ["Score", result.score],
    ["Nombre total de tests", totalTestsCount],
    ["Nombre de findings", result.findings.length],
  ];
  const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(wb, wsSummary, "Résumé");

  // Feuille 2 : répartition par catégorie
  if (result.category_summaries && result.category_summaries.length > 0) {
    const repartitionHeaders = [
      "Catégorie",
      "Label FR",
      "Label EN",
      "Nb tests",
      "Nb anomalies",
    ];
    const repartitionRows = result.category_summaries.map((s) => [
      s.category,
      s.label_fr,
      s.label_en,
      s.checks_count ?? 0,
      s.anomaly_count ?? 0,
    ]);
    const wsRepartition = XLSX.utils.aoa_to_sheet([
      repartitionHeaders,
      ...repartitionRows,
    ]);
    XLSX.utils.book_append_sheet(wb, wsRepartition, "Répartition");
  }

  // Feuille 3 : findings (une ligne par finding)
  const findingsHeaders = [
    "ID",
    "Catégorie",
    "Sévérité",
    "Titre",
    "Preuve",
    "Recommandation",
    "Références",
  ];
  const findingsRows: (string | number)[][] = result.findings.map(
    (f: ScanFinding) => [
      f.id,
      f.category,
      f.severity,
      f.title,
      f.evidence,
      f.recommendation,
      (f.references ?? []).join(" | "),
    ],
  );
  const wsFindings = XLSX.utils.aoa_to_sheet([
    findingsHeaders,
    ...findingsRows,
  ]);
  XLSX.utils.book_append_sheet(wb, wsFindings, "Findings");

  const xlsxBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
  const blob = new Blob([xlsxBuffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  downloadBlob(blob, `${buildScanBaseFilename(result.url)}.xlsx`);
}

export type ExportFormat = "csv" | "json" | "xlsx";

const EXPORT_FUNCTIONS: Record<ExportFormat, (r: ScanResult) => void> = {
  csv: exportToCsv,
  json: exportToJson,
  xlsx: exportToXlsx,
};

/**
 * Exporte les résultats dans le format demandé.
 */
export function exportScanResult(
  result: ScanResult,
  format: ExportFormat,
): void {
  EXPORT_FUNCTIONS[format](result);
}
