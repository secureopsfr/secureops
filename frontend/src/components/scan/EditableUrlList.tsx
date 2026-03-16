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
    if (urls.some((u) => u.url === normalized)) {
      setInputHasError(true);
      showErrorToast(t("scanner.addUrlErrorDuplicate"));
      return;
    }
    onUrlsChange([...urls, { url: normalized, depth: 0 }]);
    setNewUrl("");
    setInputHasError(false);
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
