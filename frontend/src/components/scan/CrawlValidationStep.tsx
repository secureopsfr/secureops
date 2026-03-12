"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Plus,
  ShieldAlert,
  Timer,
  Trash2,
  WandSparkles,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import Card from "../ui/cards/Card";
import FloatingActionDock from "./FloatingActionDock";
import type { CrawlUrlEntry } from "../../services/crawlService";
import { showErrorToast } from "../../utils/toastNotifications";

const MAX_VALIDATION_URLS = 200;

interface CrawlValidationStepProps {
  urls: CrawlUrlEntry[];
  /** Nombre d'URLs initialement identifiées par le crawl (avant édition manuelle). */
  identifiedCount?: number;
  startUrl: string;
  /** True si le crawl a été interrompu par le timeout (résultats partiels). */
  timeoutReached?: boolean;
  /** True si timeout sur le crawler HTML. */
  timeoutHtml?: boolean;
  /** True si timeout sur le crawler avancé. */
  timeoutPlaywright?: boolean;
  /** True si une signature anti-bot explicite a été détectée. */
  antiBotSignatureDetected?: boolean;
  /** True si peu d'URLs ont été découvertes (suspicion liée aux protections anti-bot). */
  antiBotLowUrlSuspected?: boolean;
  /** True si trop de requêtes 403 (protection anti-bot, WAF) ; crawl arrêté. */
  requestsBlocked?: boolean;
  /** True si blocage 403 sur le crawler HTML. */
  requestsBlockedHtml?: boolean;
  /** True si blocage 403 sur le crawler avancé. */
  requestsBlockedPlaywright?: boolean;
  /** Maximum de 403 consécutifs observés pendant l'exploration. */
  maxConsecutive403?: number;
  /** Chemins Disallow extraits de robots.txt. */
  disallowPaths?: string[];
  /** Autorise l'ajout manuel d'URL depuis cette étape. */
  allowManualAdd?: boolean;
  /** Autorise l'action de lancement du scan depuis cette étape. */
  allowLaunchScan?: boolean;
  /** Clé i18n du libellé du bouton d'action principal. */
  launchButtonLabelKey?: string;
  /** Autorise la suppression d'URLs depuis la liste. */
  allowUrlRemoval?: boolean;
  /** Affiche l'action flottante "Nouveau crawl". */
  showFloatingBackAction?: boolean;
  /** Active une version plus compacte (utile en popup). */
  compact?: boolean;
  onUrlsChange: (urls: CrawlUrlEntry[]) => void;
  onLaunchScan: () => void;
  onBack: () => void;
}

function normalizeManualDomainInput(
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

function buildDomainBasedPlaceholder(
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

export default function CrawlValidationStep({
  urls,
  identifiedCount,
  startUrl,
  timeoutReached,
  timeoutHtml,
  timeoutPlaywright,
  antiBotSignatureDetected,
  antiBotLowUrlSuspected,
  requestsBlocked,
  requestsBlockedHtml,
  requestsBlockedPlaywright,
  maxConsecutive403 = 0,
  disallowPaths = [],
  allowManualAdd = true,
  allowLaunchScan = true,
  launchButtonLabelKey = "scanner.launchScanFromList",
  allowUrlRemoval = true,
  showFloatingBackAction = true,
  compact = false,
  onUrlsChange,
  onLaunchScan,
  onBack,
}: CrawlValidationStepProps) {
  const { t } = useLanguage();
  const [newUrl, setNewUrl] = useState("");
  const [inputHasError, setInputHasError] = useState(false);
  const urlsListRef = useRef<HTMLUListElement | null>(null);
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(false);
  const hasWarnings =
    timeoutReached ||
    antiBotSignatureDetected ||
    antiBotLowUrlSuspected ||
    requestsBlocked;
  const timeoutCrawlers = [
    timeoutHtml ? t("scanner.crawlEngineHtmlLabel") : null,
    timeoutPlaywright ? t("scanner.crawlEngineAdvancedLabel") : null,
  ]
    .filter(Boolean)
    .join(", ");
  const blockedCrawlers = [
    requestsBlockedHtml ? t("scanner.crawlEngineHtmlLabel") : null,
    requestsBlockedPlaywright ? t("scanner.crawlEngineAdvancedLabel") : null,
  ]
    .filter(Boolean)
    .join(", ");
  const domainBasedPlaceholder =
    buildDomainBasedPlaceholder(
      startUrl,
      t("scanner.addUrlPlaceholderExamplePath"),
    ) || t("scanner.addUrlPlaceholder");
  const isOverUrlLimit = urls.length > MAX_VALIDATION_URLS;
  const displayIdentifiedCount = identifiedCount ?? urls.length;
  const bodyScrollClass = compact ? "min-h-0 flex-1 overflow-y-auto pr-1" : "";

  const handleRemove = (index: number) => {
    onUrlsChange(urls.filter((_, i) => i !== index));
  };

  const handleAdd = () => {
    if (urls.length >= MAX_VALIDATION_URLS) {
      setInputHasError(true);
      showErrorToast(
        t("scanner.crawlValidationMaxUrlsExceeded", {
          count: MAX_VALIDATION_URLS,
        }),
      );
      return;
    }
    const { normalized, errorKey } = normalizeManualDomainInput(
      newUrl,
      startUrl,
    );
    if (!normalized) {
      setInputHasError(true);
      showErrorToast(t(errorKey || "scanner.addUrlErrorInvalidDomain"));
      return;
    }
    if (urls.some((u) => u.url === normalized)) {
      setInputHasError(true);
      showErrorToast(t("scanner.addUrlErrorDuplicate"));
      return;
    }
    setShouldScrollToBottom(true);
    onUrlsChange([...urls, { url: normalized, depth: 0 }]);
    setNewUrl("");
    setInputHasError(false);
  };

  useEffect(() => {
    if (!shouldScrollToBottom) return;
    const el = urlsListRef.current;
    if (el) el.scrollTop = el.scrollHeight;
    setShouldScrollToBottom(false);
  }, [urls.length, shouldScrollToBottom]);

  return (
    <Card
      disableHover
      className={`mx-auto max-w-5xl ${compact ? "flex h-[78vh] flex-col p-4 md:p-5" : "p-6 md:p-7"}`}
    >
      <div className="mb-5 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)]/40 p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="section-title !mb-0 !text-left text-[1.35rem]">
              {t("scanner.crawlValidationTitle")}
            </h3>
            <p className="text-sm text-[var(--muted)]">
              {t("scanner.crawlValidationDesc")}
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--color-surface)] px-3 py-1.5">
            <WandSparkles className="h-4 w-4 text-[rgb(var(--primary))]" />
            <span className="text-sm font-medium text-[var(--text)]">
              {t("scanner.crawlValidationCount", {
                count: displayIdentifiedCount,
              })}
            </span>
          </div>
        </div>
      </div>

      <div className={bodyScrollClass}>
        {hasWarnings && (
          <div className="mb-5 space-y-2">
            {timeoutReached && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <Timer className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationTimeoutDesc", {
                    crawlers:
                      timeoutCrawlers || t("scanner.crawlEngineUnknownLabel"),
                  })}
                </p>
              </div>
            )}
            {antiBotSignatureDetected && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationAntiBotDesc")}
                </p>
              </div>
            )}
            {antiBotLowUrlSuspected && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationAntiBotLowUrlsDesc", {
                    count: displayIdentifiedCount,
                  })}
                </p>
              </div>
            )}
            {requestsBlocked && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationRequestsBlockedDesc", {
                    count: maxConsecutive403 || 5,
                    crawlers:
                      blockedCrawlers || t("scanner.crawlEngineUnknownLabel"),
                  })}
                </p>
              </div>
            )}
          </div>
        )}

        {isOverUrlLimit && (
          <div className="mb-5 rounded-lg border border-[rgb(var(--danger))]/40 bg-[rgb(var(--danger))]/10 px-3 py-2.5">
            <p className="text-sm text-[rgb(var(--danger))]">
              {t("scanner.crawlValidationMaxUrlsExceeded", {
                count: MAX_VALIDATION_URLS,
              })}
            </p>
          </div>
        )}

        {disallowPaths.length > 0 && (
          <section className="mb-5 rounded-xl border border-[var(--border)] p-4">
            <p className="mb-2 text-sm font-medium text-[var(--text)]">
              {t("scanner.crawlValidationDisallowTitle")}
            </p>
            <div
              className={`flex flex-wrap gap-2 overflow-y-auto pr-1 ${compact ? "max-h-24" : "max-h-32"}`}
            >
              {disallowPaths.map((path, i) => (
                <code
                  key={`${path}-${i}`}
                  className="rounded-full border border-[var(--border)] bg-[var(--surface-secondary)]/40 px-2.5 py-1 text-xs text-[var(--muted)]"
                >
                  {path || "/"}
                </code>
              ))}
            </div>
          </section>
        )}

        <section
          className={`mb-5 rounded-xl border ${
            isOverUrlLimit
              ? "border-[rgb(var(--danger))] ring-1 ring-[rgba(var(--danger),0.35)]"
              : "border-[var(--border)]"
          }`}
        >
          <div className="border-b border-[var(--border)] px-4 py-2.5">
            <p className="text-sm font-medium text-[var(--text)]">
              {`URLs (${urls.length})`}
            </p>
          </div>
          <ul
            ref={urlsListRef}
            className={`${compact ? "max-h-56" : "max-h-72"} overflow-y-auto`}
          >
            {urls.map((entry, i) => (
              <li
                key={`${entry.url}-${i}`}
                className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-2.5 last:border-b-0"
              >
                <span
                  className="min-w-0 flex-1 truncate text-sm"
                  title={entry.url}
                >
                  {entry.url}
                </span>
                {allowUrlRemoval && (
                  <button
                    type="button"
                    onClick={() => handleRemove(i)}
                    className="shrink-0 rounded-md p-1.5 text-[var(--muted)] hover:bg-[var(--color-surface-hover)] hover:text-red-500 transition-colors"
                    aria-label={t("scanner.removeUrl")}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>

        {allowManualAdd && (
          <div className="mb-5 rounded-xl border border-[var(--border)] p-4">
            <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <label className="block text-sm font-medium text-[var(--text)]">
                {t("scanner.addSpecificUrl")}
              </label>
              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)]/40 px-3 py-2">
                <p className="mb-1 text-xs font-medium text-[var(--text)]">
                  {t("scanner.addUrlRulesTitle")}
                </p>
                <p className="text-xs text-[var(--muted)]">
                  {t("scanner.addUrlRuleDomainOnly")}
                </p>
                <p className="text-xs text-[var(--muted)]">
                  {t("scanner.addUrlRuleHttpsOnly")}
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                type="text"
                inputMode="url"
                value={newUrl}
                onChange={(e) => {
                  setNewUrl(e.target.value);
                  if (inputHasError) setInputHasError(false);
                }}
                placeholder={domainBasedPlaceholder}
                className={`auth-input flex-1 ${
                  inputHasError || isOverUrlLimit
                    ? "border-[rgb(var(--danger))] ring-2 ring-[rgba(var(--danger),0.35)]"
                    : ""
                }`}
                onKeyDown={(e) =>
                  e.key === "Enter" && (e.preventDefault(), handleAdd())
                }
              />
              <GenericButton
                type="button"
                label={t("scanner.addUrl")}
                icon={<Plus className="h-4 w-4" />}
                variant="secondary"
                onClick={handleAdd}
              />
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap justify-end gap-2">
        {allowLaunchScan && (
          <GenericButton
            type="button"
            label={t(launchButtonLabelKey)}
            variant="primary"
            onClick={onLaunchScan}
            disabled={isOverUrlLimit}
          />
        )}
      </div>

      {showFloatingBackAction && (
        <FloatingActionDock
          ariaLabel={t("scanner.newCrawl")}
          actions={[
            {
              key: "new-crawl",
              label: t("scanner.newCrawl"),
              variant: "outline",
              onClick: onBack,
            },
          ]}
        />
      )}
    </Card>
  );
}
