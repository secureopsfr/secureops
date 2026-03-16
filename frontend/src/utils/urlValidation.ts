/**
 * Validation et normalisation des URLs pour l'ajout manuel (crawler, import API).
 */

export function normalizeManualDomainInput(
  value: string,
  startUrl: string,
): { normalized: string | null; errorKey?: string } {
  const trimmed = value.trim();
  if (!trimmed) {
    return { normalized: null, errorKey: "scanner.addUrlErrorRequired" };
  }

  if (trimmed.includes("://") && !/^https?:\/\//i.test(trimmed)) {
    return {
      normalized: null,
      errorKey: "scanner.addUrlErrorSchemeNotAllowed",
    };
  }

  const withScheme = /^https?:\/\//i.test(trimmed)
    ? trimmed
    : `https://${trimmed}`;

  try {
    const u = new URL(withScheme);
    if (u.protocol !== "https:" && u.protocol !== "http:") {
      return {
        normalized: null,
        errorKey: "scanner.addUrlErrorSchemeNotAllowed",
      };
    }
    if (u.username || u.password) {
      return { normalized: null, errorKey: "scanner.addUrlErrorInvalidDomain" };
    }
    if (u.search || u.hash) {
      return { normalized: null, errorKey: "scanner.addUrlErrorNoPathAllowed" };
    }
    if (u.port) {
      return { normalized: null, errorKey: "scanner.addUrlErrorNoPortAllowed" };
    }

    const normalizedPath = (u.pathname || "/").replace(/\/+$/, "");
    if (normalizedPath !== "") {
      return { normalized: null, errorKey: "scanner.addUrlErrorNoPathAllowed" };
    }

    const host = u.hostname.toLowerCase();
    const isValidDomain =
      /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i.test(
        host,
      );
    if (!isValidDomain) {
      return { normalized: null, errorKey: "scanner.addUrlErrorInvalidDomain" };
    }

    const startWithScheme = startUrl.includes("://")
      ? startUrl
      : `https://${startUrl}`;
    let startHost = "";
    try {
      startHost = new URL(startWithScheme).hostname.toLowerCase();
    } catch {
      startHost = "";
    }

    const normalizeScopeHost = (h: string) =>
      h.startsWith("www.") ? h.slice(4) : h;
    const scopeHost = normalizeScopeHost(startHost);
    const candidateHost = normalizeScopeHost(host);

    if (
      scopeHost &&
      candidateHost !== scopeHost &&
      !candidateHost.endsWith(`.${scopeHost}`)
    ) {
      return { normalized: null, errorKey: "scanner.addUrlErrorOutOfScope" };
    }

    return { normalized: `https://${host}` };
  } catch {
    return { normalized: null, errorKey: "scanner.addUrlErrorInvalidDomain" };
  }
}

export function normalizeManualApiEndpointInput(
  value: string,
  startUrl: string,
): { normalized: string | null; errorKey?: string } {
  const trimmed = value.trim();
  if (!trimmed) {
    return { normalized: null, errorKey: "scanner.addUrlErrorRequired" };
  }

  const withScheme = /^https?:\/\//i.test(trimmed)
    ? trimmed
    : `https://${trimmed}`;

  try {
    const u = new URL(withScheme);
    if (u.protocol !== "https:" && u.protocol !== "http:") {
      return {
        normalized: null,
        errorKey: "scanner.addUrlErrorSchemeNotAllowed",
      };
    }
    if (u.username || u.password) {
      return { normalized: null, errorKey: "scanner.addUrlErrorInvalidDomain" };
    }

    const startWithScheme = startUrl.includes("://")
      ? startUrl
      : `https://${startUrl}`;
    let startHost = "";
    try {
      startHost = new URL(startWithScheme).hostname.toLowerCase();
    } catch {
      startHost = "";
    }

    const normalizeScopeHost = (h: string) =>
      h.startsWith("www.") ? h.slice(4) : h;
    const scopeHost = normalizeScopeHost(startHost);
    const candidateHost = normalizeScopeHost(u.hostname.toLowerCase());

    if (
      scopeHost &&
      candidateHost !== scopeHost &&
      !candidateHost.endsWith(`.${scopeHost}`)
    ) {
      return { normalized: null, errorKey: "scanner.addUrlErrorOutOfScope" };
    }

    return { normalized: u.href };
  } catch {
    return { normalized: null, errorKey: "scanner.addUrlErrorInvalidDomain" };
  }
}

export function buildDomainBasedPlaceholder(
  startUrl: string,
  examplePath: string,
  fallback: string,
): string {
  const result = buildDomainBasedPlaceholderOrNull(startUrl, examplePath);
  return result ?? fallback;
}

/** Retourne null si startUrl invalide (utilisé avec || fallback). */
export function buildDomainBasedPlaceholderOrNull(
  startUrl: string,
  examplePath: string,
): string | null {
  const trimmed = startUrl.trim();
  if (!trimmed) return null;
  const withScheme = trimmed.includes("://") ? trimmed : `https://${trimmed}`;

  try {
    const u = new URL(withScheme);
    const host = u.hostname.toLowerCase();
    if (!host) return null;
    return `${host}/${examplePath}`;
  } catch {
    return null;
  }
}
