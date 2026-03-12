/**
 * Primitives partagées d'export (CSV, XLSX, téléchargement).
 * Importé par exportScan.ts et exportMultiScan.ts.
 */

export const CSV_SEP = ";";
export const BOM = "\uFEFF";

export function escapeCsvCell(value: string): string {
  if (value.includes(CSV_SEP) || value.includes('"') || value.includes("\n")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

/**
 * Génère un nom de fichier de base à partir de l'URL scannée.
 */
export function buildScanBaseFilename(url: string, prefix = "scan"): string {
  try {
    const host = new URL(url).hostname.replace(/\./g, "-");
    const date = new Date().toISOString().slice(0, 10);
    return `${prefix}-${host}-${date}`;
  } catch {
    return `${prefix}-${Date.now()}`;
  }
}

/**
 * Déclenche le téléchargement d'un fichier dans le navigateur.
 */
export function downloadBlob(blob: Blob, filename: string): void {
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
