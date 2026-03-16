/**
 * Parse API documentation specs (OpenAPI, Postman) to extract endpoint URLs.
 * Returns CrawlUrlEntry[] suitable for backend multi-scan.
 */

import yaml from "js-yaml";
import type { CrawlUrlEntry } from "../services/crawlService";

const MAX_ENDPOINTS = 200;

export type ParseApiDocResult =
  | {
      ok: true;
      urls: CrawlUrlEntry[];
      format: "openapi" | "postman";
    }
  | {
      ok: false;
      error: string;
    };

function normalizeUrl(base: string, path: string): string {
  const baseClean = base.replace(/\/+$/, "");
  const pathClean = path.startsWith("/") ? path : `/${path}`;
  return `${baseClean}${pathClean}`;
}

function extractBaseUrlFromOpenApi(spec: Record<string, unknown>): string {
  // OpenAPI 3.x: servers
  const servers = spec.servers as Array<{ url: string }> | undefined;
  if (servers?.[0]?.url) {
    return servers[0].url.replace(/\/+$/, "");
  }

  // Swagger 2.0: host + basePath + schemes
  const host = spec.host as string | undefined;
  if (host && typeof host === "string") {
    const schemes = spec.schemes as string[] | undefined;
    const scheme = schemes?.[0] ?? "https";
    const basePath = (spec.basePath as string) || "";
    const base = `${scheme}://${host.replace(/\/+$/, "")}${basePath}`;
    return base.replace(/\/+$/, "");
  }

  return "";
}

function extractPathsFromOpenApi(spec: Record<string, unknown>): string[] {
  const paths = spec.paths as Record<string, unknown> | undefined;
  if (!paths || typeof paths !== "object") return [];
  return Object.keys(paths).filter((p) => p && typeof p === "string");
}

function parseOpenApi(
  spec: Record<string, unknown>,
  baseOverride?: string,
): CrawlUrlEntry[] {
  const base = baseOverride || extractBaseUrlFromOpenApi(spec);
  if (!base) return [];
  const pathList = extractPathsFromOpenApi(spec);
  const unique = new Set<string>();
  for (const p of pathList) {
    if (unique.size >= MAX_ENDPOINTS) break;
    const url = normalizeUrl(base, p);
    try {
      new URL(url);
      unique.add(url);
    } catch {
      // skip invalid
    }
  }
  return Array.from(unique).map((url) => ({ url, depth: 0 }));
}

function parsePostman(
  spec: Record<string, unknown>,
  baseOverride?: string,
): CrawlUrlEntry[] {
  const base = baseOverride || "";
  const item = spec.item as
    | Array<{
        request?: {
          url?: string | { raw?: string; host?: string[]; path?: string[] };
        };
        item?: Array<{ request?: { url?: string | { raw?: string } } }>;
      }>
    | undefined;
  if (!item || !Array.isArray(item)) return [];

  const unique = new Set<string>();

  function walk(items: typeof item): void {
    if (!items) return;
    for (const i of items) {
      if (unique.size >= MAX_ENDPOINTS) return;
      const req = i?.request;
      if (req) {
        let rawUrl: string | undefined;
        if (typeof req.url === "string") {
          rawUrl = req.url;
        } else if (req.url && typeof req.url === "object") {
          rawUrl = (req.url as { raw?: string }).raw;
          if (
            !rawUrl &&
            Array.isArray((req.url as { host?: string[] }).host) &&
            Array.isArray((req.url as { path?: string[] }).path)
          ) {
            const u = req.url as { host?: string[]; path?: string[] };
            const host = u.host?.join(".") || "";
            const path = (u.path || []).join("/");
            if (host) rawUrl = `https://${host}/${path}`;
          }
        }
        if (rawUrl) {
          try {
            const parsed = new URL(rawUrl);
            if (parsed.protocol === "http:" || parsed.protocol === "https:") {
              unique.add(parsed.href);
            }
          } catch {
            // skip
          }
        }
      }
      if (i.item && Array.isArray(i.item)) {
        walk(i.item);
      }
    }
  }

  walk(item);
  return Array.from(unique).map((url) => ({ url, depth: 0 }));
}

/**
 * Detect spec format and parse. If baseUrlOverride is provided (e.g. from user input),
 * it is used as base for OpenAPI paths and Postman when base is missing.
 */
export function parseApiDoc(
  content: string,
  baseUrlOverride?: string,
): ParseApiDocResult {
  let spec: Record<string, unknown>;
  try {
    if (content.trim().startsWith("{")) {
      spec = JSON.parse(content) as Record<string, unknown>;
    } else {
      spec = yaml.load(content) as Record<string, unknown>;
    }
  } catch {
    return { ok: false, error: "Invalid JSON or YAML" };
  }

  if (!spec || typeof spec !== "object") {
    return { ok: false, error: "Invalid spec structure" };
  }

  // OpenAPI 2 (Swagger) or 3
  if (spec.swagger || spec.openapi) {
    const urls = parseOpenApi(spec, baseUrlOverride);
    if (urls.length === 0) {
      return { ok: false, error: "No paths found in OpenAPI spec" };
    }
    return { ok: true, urls, format: "openapi" };
  }

  // Postman collection
  if (spec.info && Array.isArray(spec.item)) {
    const urls = parsePostman(spec, baseUrlOverride);
    if (urls.length === 0) {
      return { ok: false, error: "No requests found in Postman collection" };
    }
    return { ok: true, urls, format: "postman" };
  }

  return { ok: false, error: "Unsupported format (OpenAPI, Postman)" };
}
