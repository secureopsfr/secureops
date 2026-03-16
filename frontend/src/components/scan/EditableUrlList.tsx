"use client";

import { useRef, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { GenericButton } from "../buttons";
import {
  normalizeManualDomainInput,
  normalizeManualApiEndpointInput,
  buildDomainBasedPlaceholder,
  buildDomainBasedPlaceholderOrNull,
} from "../../utils/urlValidation";
import {
  processUrlWithParams,
  resolveUrlWithParams,
} from "../../utils/urlPathParams";
import { showErrorToast } from "../../utils/toastNotifications";
import type { CrawlUrlEntry } from "../../services/crawlService";

const MAX_URLS = 200;

export interface EditableUrlListProps {
  urls: CrawlUrlEntry[];
  onUrlsChange: (urls: CrawlUrlEntry[]) => void;
  startUrl: string;
  /** Si true, autorise les URLs complètes avec path (endpoints API). Sinon domaine uniquement (crawler frontend). */
  allowFullUrlAdd?: boolean;
  /** Autorise la suppression d'URLs. */
  allowUrlRemoval?: boolean;
  /** Affiche le formulaire d'ajout manuel. */
  allowManualAdd?: boolean;
  /** Version compacte (hauteur réduite de la liste). */
  compact?: boolean;
  /** Affiche l'alerte limite dépassée au-dessus de la liste. */
  showOverLimitAlert?: boolean;
  t: (key: string, params?: Record<string, string | number>) => string;
}

export default function EditableUrlList({
  urls,
  onUrlsChange,
  startUrl,
  allowFullUrlAdd = false,
  allowUrlRemoval = true,
  allowManualAdd = true,
  compact = false,
  showOverLimitAlert = true,
  t,
}: EditableUrlListProps) {
  const [newUrl, setNewUrl] = useState("");
  const [inputHasError, setInputHasError] = useState(false);
  const urlsListRef = useRef<HTMLUListElement>(null);

  const isOverUrlLimit = urls.length > MAX_URLS;
  const urlsWithoutParams = urls.filter(
    (u) => !u.params || Object.keys(u.params).length === 0,
  );
  const urlsWithParams = urls.filter(
    (u) => u.params && Object.keys(u.params).length > 0,
  );
  const startWithScheme = startUrl.includes("://")
    ? startUrl
    : `https://${startUrl}`;
  const domainBasedPlaceholder = allowFullUrlAdd
    ? buildDomainBasedPlaceholder(
        startUrl,
        t("scanner.addUrlPlaceholderExamplePath"),
        t("scanner.addUrlPlaceholderEndpoint"),
      )
    : buildDomainBasedPlaceholderOrNull(
        startUrl,
        t("scanner.addUrlPlaceholderExamplePath"),
      ) || t("scanner.addUrlPlaceholder");

  const resolveCrawlEntryUrl = (e: CrawlUrlEntry) =>
    e.params && Object.keys(e.params).length > 0
      ? resolveUrlWithParams(e.url, e.params)
      : e.url;

  const handleRemove = (index: number) => {
    onUrlsChange(urls.filter((_, i) => i !== index));
  };

  const handleAdd = () => {
    if (urls.length >= MAX_URLS) {
      setInputHasError(true);
      showErrorToast(
        t("scanner.crawlValidationMaxUrlsExceeded", { count: MAX_URLS }),
      );
      return;
    }
    const normalizeFn = allowFullUrlAdd
      ? normalizeManualApiEndpointInput
      : normalizeManualDomainInput;
    const { normalized, errorKey } = normalizeFn(newUrl, startWithScheme);
    if (!normalized) {
      setInputHasError(true);
      showErrorToast(t(errorKey || "scanner.addUrlErrorInvalidDomain"));
      return;
    }
    const { url: finalUrl, params } = processUrlWithParams(normalized);
    const duplicateUrl = params
      ? resolveUrlWithParams(finalUrl, params)
      : finalUrl;
    if (urls.some((u) => resolveCrawlEntryUrl(u) === duplicateUrl)) {
      setInputHasError(true);
      showErrorToast(t("scanner.addUrlErrorDuplicate"));
      return;
    }
    onUrlsChange([
      ...urls,
      params
        ? { url: finalUrl, depth: 0, params }
        : { url: finalUrl, depth: 0 },
    ]);
    setNewUrl("");
    setInputHasError(false);
  };

  const handleUpdateParam = (
    index: number,
    paramName: string,
    value: string,
  ) => {
    const entry = urls[index];
    if (!entry?.params) return;
    const updated = [...urls];
    updated[index] = {
      ...entry,
      params: { ...entry.params, [paramName]: value },
    };
    onUrlsChange(updated);
  };

  const getGlobalIndex = (entry: CrawlUrlEntry) => {
    const idx = urls.findIndex(
      (u) =>
        u.url === entry.url &&
        JSON.stringify(u.params || {}) === JSON.stringify(entry.params || {}),
    );
    return idx >= 0 ? idx : 0;
  };

  return (
    <>
      {showOverLimitAlert && isOverUrlLimit && (
        <div className="mb-5 rounded-lg border border-[rgb(var(--danger))]/40 bg-[rgb(var(--danger))]/10 px-3 py-2.5">
          <p className="text-sm text-[rgb(var(--danger))]">
            {t("scanner.crawlValidationMaxUrlsExceeded", { count: MAX_URLS })}
          </p>
        </div>
      )}

      {urlsWithoutParams.length > 0 && (
        <section
          className={`mb-5 rounded-xl border ${
            isOverUrlLimit
              ? "border-[rgb(var(--danger))] ring-1 ring-[rgba(var(--danger),0.35)]"
              : "border-[var(--border)]"
          }`}
        >
          <div className="border-b border-[var(--border)] px-4 py-2.5">
            <p className="text-sm font-medium text-[var(--text)]">
              {t("scanner.urlsReady", { count: urlsWithoutParams.length })}
            </p>
          </div>
          <ul
            ref={urlsListRef}
            className={`${compact ? "max-h-40" : "max-h-52"} overflow-y-auto`}
          >
            {urlsWithoutParams.map((entry) => {
              const globalIdx = getGlobalIndex(entry);
              return (
                <li
                  key={`simple-${entry.url}-${globalIdx}`}
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
                      onClick={() => handleRemove(globalIdx)}
                      className="shrink-0 rounded-md p-1.5 text-[var(--muted)] hover:bg-[var(--color-surface-hover)] hover:text-red-500 transition-colors"
                      aria-label={t("scanner.removeUrl")}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {urlsWithParams.length > 0 && (
        <section
          className={`mb-5 rounded-xl border ${
            isOverUrlLimit
              ? "border-[rgb(var(--danger))] ring-1 ring-[rgba(var(--danger),0.35)]"
              : "border-[var(--border)]"
          }`}
        >
          <div className="border-b border-[var(--border)] px-4 py-2.5">
            <p className="text-sm font-medium text-[var(--text)]">
              {t("scanner.urlsWithParams", { count: urlsWithParams.length })}
            </p>
          </div>
          <ul
            className={`${compact ? "max-h-40" : "max-h-52"} overflow-y-auto`}
          >
            {urlsWithParams.map((entry) => {
              const globalIdx = getGlobalIndex(entry);
              const paramEntries = entry.params
                ? Object.entries(entry.params)
                : [];
              return (
                <li
                  key={`param-${entry.url}-${globalIdx}`}
                  className="border-b border-[var(--border)] px-4 py-2.5 last:border-b-0"
                >
                  <div className="flex items-start gap-2">
                    <span
                      className="min-w-0 flex-1 truncate text-sm"
                      title={entry.url}
                    >
                      {entry.url}
                    </span>
                    {allowUrlRemoval && (
                      <button
                        type="button"
                        onClick={() => handleRemove(globalIdx)}
                        className="shrink-0 rounded-md p-1.5 text-[var(--muted)] hover:bg-[var(--color-surface-hover)] hover:text-red-500 transition-colors"
                        aria-label={t("scanner.removeUrl")}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {paramEntries.map(([name, value]) => (
                      <div
                        key={name}
                        className="flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-secondary)]/40 px-2 py-1"
                      >
                        <label className="text-xs text-[var(--muted)]">
                          {name}:
                        </label>
                        <input
                          type="text"
                          value={value}
                          onChange={(e) =>
                            handleUpdateParam(globalIdx, name, e.target.value)
                          }
                          className="auth-input w-20 py-0.5 text-xs"
                          size={1}
                        />
                      </div>
                    ))}
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {allowManualAdd && urls.length < MAX_URLS && (
        <div className="mb-5 rounded-xl border border-[var(--border)] p-4">
          <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <label className="block text-sm font-medium text-[var(--text)]">
              {t("scanner.addSpecificUrl")}
            </label>
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)]/40 px-3 py-2">
              <p className="mb-1 text-xs font-medium text-[var(--text)]">
                {t("scanner.addUrlRulesTitle")}
              </p>
              {!allowFullUrlAdd && (
                <p className="text-xs text-[var(--muted)]">
                  {t("scanner.addUrlRuleDomainOnly")}
                </p>
              )}
              {allowFullUrlAdd && (
                <p className="text-xs text-[var(--muted)]">
                  {t("scanner.addUrlRuleFullUrlAllowed")}
                </p>
              )}
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
    </>
  );
}

export { MAX_URLS as EDITABLE_URL_LIST_MAX };
