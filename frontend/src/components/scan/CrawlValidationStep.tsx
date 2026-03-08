"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import Card from "../ui/cards/Card";
import type { CrawlUrlEntry } from "../../services/crawlService";

interface CrawlValidationStepProps {
  urls: CrawlUrlEntry[];
  startUrl: string;
  /** True si le crawl a été interrompu par le timeout (résultats partiels). */
  timeoutReached?: boolean;
  /** True si une protection anti-bot a été détectée (mode Playwright). */
  antiBotSuspected?: boolean;
  /** True si trop de requêtes 403 (protection anti-bot, WAF) ; crawl arrêté. */
  requestsBlocked?: boolean;
  /** Chemins Disallow extraits de robots.txt. */
  disallowPaths?: string[];
  onUrlsChange: (urls: CrawlUrlEntry[]) => void;
  onLaunchScan: () => void;
  onBack: () => void;
}

function isValidUrl(s: string): boolean {
  try {
    const u = new URL(s);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export default function CrawlValidationStep({
  urls,
  startUrl,
  timeoutReached,
  antiBotSuspected,
  requestsBlocked,
  disallowPaths = [],
  onUrlsChange,
  onLaunchScan,
  onBack,
}: CrawlValidationStepProps) {
  const { t } = useLanguage();
  const [newUrl, setNewUrl] = useState("");

  const handleRemove = (index: number) => {
    onUrlsChange(urls.filter((_, i) => i !== index));
  };

  const handleAdd = () => {
    const trimmed = newUrl.trim();
    if (!trimmed || !isValidUrl(trimmed)) return;
    if (urls.some((u) => u.url === trimmed)) return;
    onUrlsChange([...urls, { url: trimmed, type: "page", depth: 0 }]);
    setNewUrl("");
  };

  return (
    <Card disableHover className="mx-auto max-w-4xl p-6">
      <h3 className="section-title -mt-2 mb-2 text-left">
        {t("scanner.crawlValidationTitle")}
      </h3>
      <p className="mb-1 text-sm font-medium text-[var(--text)]">
        {t("scanner.crawlValidationCount", { count: urls.length })}
      </p>
      {timeoutReached && (
        <p className="mb-2 text-sm text-[rgb(var(--warning))]">
          {t("scanner.crawlValidationTimeoutDesc")}
        </p>
      )}
      {antiBotSuspected && (
        <p className="mb-2 text-sm text-[rgb(var(--warning))]">
          {t("scanner.crawlValidationAntiBotDesc")}
        </p>
      )}
      {requestsBlocked && (
        <p className="mb-2 text-sm text-[rgb(var(--warning))]">
          {t("scanner.crawlValidationRequestsBlockedDesc")}
        </p>
      )}
      <p className="mb-4 text-sm text-[var(--muted)]">
        {t("scanner.crawlValidationDesc")}
      </p>

      {disallowPaths.length > 0 && (
        <div className="mb-4">
          <p className="mb-1 text-sm font-medium text-[var(--text)]">
            {t("scanner.crawlValidationDisallowTitle")}
          </p>
          <ul className="mb-4 max-h-32 overflow-y-auto rounded border border-[var(--border)]">
            {disallowPaths.map((path, i) => (
              <li
                key={`${path}-${i}`}
                className="border-b border-[var(--border)] px-3 py-2 last:border-b-0"
              >
                <code className="text-sm text-[var(--muted)]">
                  {path || "/"}
                </code>
              </li>
            ))}
          </ul>
        </div>
      )}

      <ul className="mb-4 max-h-64 overflow-y-auto rounded border border-[var(--border)]">
        {urls.map((entry, i) => (
          <li
            key={`${entry.url}-${i}`}
            className="flex items-center justify-between gap-2 border-b border-[var(--border)] px-3 py-2 last:border-b-0"
          >
            <span className="min-w-0 truncate text-sm" title={entry.url}>
              {entry.url}
            </span>
            <span
              className="shrink-0 text-xs text-[var(--muted)]"
              title={entry.type}
            >
              <span className="opacity-60">·</span> {entry.type}
            </span>
            <button
              type="button"
              onClick={() => handleRemove(i)}
              className="shrink-0 rounded p-1 text-[var(--muted)] hover:bg-[var(--muted)]/10 hover:text-[var(--danger)]"
              aria-label={t("scanner.removeUrl")}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </li>
        ))}
      </ul>

      <div className="mb-4 flex gap-2">
        <input
          type="url"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          placeholder={t("scanner.addUrlPlaceholder")}
          className="auth-input flex-1"
          onKeyDown={(e) =>
            e.key === "Enter" && (e.preventDefault(), handleAdd())
          }
        />
        <GenericButton
          type="button"
          label={t("scanner.addUrl")}
          variant="secondary"
          onClick={handleAdd}
          disabled={!newUrl.trim() || !isValidUrl(newUrl.trim())}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <GenericButton
          type="button"
          label={t("scanner.launchScanFromList")}
          variant="primary"
          onClick={onLaunchScan}
        />
        <GenericButton
          type="button"
          label={t("common.cancel")}
          variant="secondary"
          onClick={onBack}
        />
      </div>
    </Card>
  );
}
