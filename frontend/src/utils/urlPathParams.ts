/**
 * Détection et résolution des paramètres de chemin dans les URLs API.
 * Supporte {id}, {userId} (OpenAPI) et :id, :userId (Postman/Express).
 */

/** Patterns: {param} ou :param (pas de : en debut de segment pour éviter ports) */
const BRACE_PARAM = /\{([^}]+)\}/g;
const COLON_PARAM = /:([a-zA-Z_][a-zA-Z0-9_]*)(?=[/?#]|$)/g;

export function extractPathParams(url: string): string[] {
  const names = new Set<string>();
  let m: RegExpExecArray | null;
  const braceRe = new RegExp(BRACE_PARAM.source, "g");
  while ((m = braceRe.exec(url)) !== null) {
    names.add(m[1]);
  }
  const colonRe = new RegExp(COLON_PARAM.source, "g");
  while ((m = colonRe.exec(url)) !== null) {
    names.add(m[1]);
  }
  return Array.from(names);
}

/**
 * Valeur par défaut selon le type/nom du paramètre.
 */
export function getDefaultForParam(name: string): string {
  const lower = name.toLowerCase();
  if (lower === "id" || lower.endsWith("id")) return "1";
  if (lower === "uuid" || lower.endsWith("uuid"))
    return "550e8400-e29b-41d4-a716-446655440000";
  if (
    lower === "slug" ||
    lower === "name" ||
    lower.endsWith("slug") ||
    lower.endsWith("name")
  )
    return "test";
  if (lower === "email" || lower.endsWith("email")) return "test@example.com";
  if (lower === "key" || lower.endsWith("key")) return "default";
  return "1";
}

/**
 * Remplace les paramètres dans l'URL par les valeurs fournies.
 */
export function resolveUrlWithParams(
  url: string,
  params: Record<string, string>,
): string {
  let resolved = url;
  for (const [key, value] of Object.entries(params)) {
    resolved = resolved.replace(
      new RegExp(`\\{${escapeRe(key)}\\}`, "g"),
      value,
    );
    resolved = resolved.replace(
      new RegExp(`:${escapeRe(key)}(?=[/?#]|$)`, "g"),
      value,
    );
  }
  return resolved;
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export interface UrlWithParamsResult {
  url: string;
  params?: Record<string, string>;
}

/**
 * Si l'URL contient des paramètres, les extrait et assigne des valeurs par défaut.
 */
export function processUrlWithParams(url: string): UrlWithParamsResult {
  const paramNames = extractPathParams(url);
  if (paramNames.length === 0) {
    return { url };
  }
  const params: Record<string, string> = {};
  for (const name of paramNames) {
    params[name] = getDefaultForParam(name);
  }
  return { url, params };
}

export interface CrawlUrlEntryWithParams {
  url: string;
  params?: Record<string, string>;
}

/**
 * Convertit une liste CrawlUrlEntry en URLs résolues pour le scan.
 */
export function resolveCrawlUrlsToScanUrls(
  entries: CrawlUrlEntryWithParams[],
): string[] {
  return entries.map((e) =>
    e.params && Object.keys(e.params).length > 0
      ? resolveUrlWithParams(e.url, e.params)
      : e.url,
  );
}
