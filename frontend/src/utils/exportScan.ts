/**
 * Utilitaires d'export des résultats de scan (CSV, JSON, XLSX).
 */

import * as XLSX from "xlsx";
import type { ScanResult, ScanFinding } from "../services/scanService";

const CSV_SEP = ";";
const BOM = "\uFEFF";

function escapeCsvCell(value: string): string {
  if (value.includes(CSV_SEP) || value.includes('"') || value.includes("\n")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

/**
 * Génère un nom de fichier à partir de l'URL scannée.
 */
function getBaseFilename(url: string): string {
  try {
    const host = new URL(url).hostname.replace(/\./g, "-");
    const date = new Date().toISOString().slice(0, 10);
    return `scan-${host}-${date}`;
  } catch {
    return `scan-${Date.now()}`;
  }
}

/**
 * Déclenche le téléchargement d'un fichier.
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Exporte les résultats en CSV.
 */
export function exportToCsv(result: ScanResult): void {
  const headers = [
    "Sévérité",
    "Catégorie",
    "Titre",
    "Preuve",
    "Recommandation",
    "Références",
  ];
  const rows: string[][] = [headers];

  for (const f of result.findings) {
    rows.push([
      f.severity,
      f.category,
      f.title,
      f.evidence,
      f.recommendation,
      f.references.join(" | "),
    ]);
  }

  const csvContent =
    BOM + rows.map((row) => row.map(escapeCsvCell).join(CSV_SEP)).join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
  downloadBlob(blob, `${getBaseFilename(result.url)}.csv`);
}

/**
 * Exporte les résultats en JSON.
 */
export function exportToJson(result: ScanResult): void {
  const json = JSON.stringify(
    {
      url: result.url,
      timestamp: result.timestamp,
      duration: result.duration,
      score: result.score,
      findings: result.findings,
    },
    null,
    2,
  );
  const blob = new Blob([json], { type: "application/json" });
  downloadBlob(blob, `${getBaseFilename(result.url)}.json`);
}

/**
 * Exporte les résultats en XLSX (Excel).
 */
export function exportToXlsx(result: ScanResult): void {
  const wb = XLSX.utils.book_new();

  // Feuille 1 : résumé
  const summaryData = [
    ["URL", result.url],
    ["Date", result.timestamp],
    ["Durée (s)", result.duration],
    ["Score", result.score],
    ["Nombre de findings", result.findings.length],
  ];
  const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(wb, wsSummary, "Résumé");

  // Feuille 2 : findings
  const findingsHeaders = [
    "Sévérité",
    "Catégorie",
    "Titre",
    "Preuve",
    "Recommandation",
    "Références",
  ];
  const findingsRows: (string | number)[][] = result.findings.map(
    (f: ScanFinding) => [
      f.severity,
      f.category,
      f.title,
      f.evidence,
      f.recommendation,
      f.references.join(" | "),
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
  downloadBlob(blob, `${getBaseFilename(result.url)}.xlsx`);
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
