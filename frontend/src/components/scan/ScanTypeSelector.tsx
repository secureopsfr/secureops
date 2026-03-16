"use client";

import { DropdownSelector } from "../buttons";
import { Checkbox } from "../inputs";
import ApiDocImportZone from "./ApiDocImportZone";
import type { CrawlState } from "../../hooks/useCrawlState";
import type { CrawlUrlEntry } from "../../services/crawlService";

interface ScanTypeSelectorProps {
  scanOnlyThisPage: boolean;
  onScanOnlyThisPageChange: (checked: boolean) => void;
  scanTarget: "frontend" | "backend";
  crawlMode: CrawlState["mode"];
  crawlMaxUrls: number;
  onCrawlModeChange: (mode: CrawlState["mode"]) => void;
  onCrawlMaxUrlsChange: (value: number) => void;
  baseUrl: string;
  apiDocUrls: CrawlUrlEntry[];
  onApiDocUrlsChange: (urls: CrawlUrlEntry[]) => void;
  t: (key: string) => string;
}

/**
 * Contrôles de mode scan : page unique, crawl multi-pages (frontend) ou import doc API (backend).
 */
export default function ScanTypeSelector({
  scanOnlyThisPage,
  onScanOnlyThisPageChange,
  scanTarget,
  crawlMode,
  crawlMaxUrls,
  onCrawlModeChange,
  onCrawlMaxUrlsChange,
  baseUrl,
  apiDocUrls,
  onApiDocUrlsChange,
  t,
}: ScanTypeSelectorProps) {
  const isBackend = scanTarget === "backend";
  const showCrawlOptions = !isBackend && !scanOnlyThisPage;
  const showApiDocZone = isBackend && !scanOnlyThisPage;

  const checkboxLabel = isBackend
    ? t("scanner.scanOnlyThisEndpoint")
    : t("scanner.scanOnlyThisPage");

  return (
    <>
      <Checkbox
        label={checkboxLabel}
        checked={scanOnlyThisPage}
        onChange={onScanOnlyThisPageChange}
      />
      {showApiDocZone && (
        <ApiDocImportZone
          baseUrl={baseUrl}
          urls={apiDocUrls}
          onUrlsChange={onApiDocUrlsChange}
          t={t}
        />
      )}
      {showCrawlOptions && (
        <>
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              {t("scanner.crawlModeLabel")}
            </label>
            <DropdownSelector
              selectedValue={crawlMode}
              onChange={(v) => onCrawlModeChange(v as CrawlState["mode"])}
              options={[
                { value: "html", label: t("scanner.crawlModeHtml") },
                {
                  value: "playwright",
                  label: t("scanner.crawlModePlaywright"),
                },
                { value: "both", label: t("scanner.crawlModeBoth") },
              ]}
              width="100%"
            />
          </div>
          <div>
            <label
              htmlFor="crawl-max-urls"
              className="block text-sm font-medium text-[var(--text)] mb-1"
            >
              {t("scanner.crawlMaxUrlsLabel")}
            </label>
            <input
              id="crawl-max-urls"
              type="number"
              min={5}
              max={200}
              value={crawlMaxUrls}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10);
                onCrawlMaxUrlsChange(
                  Number.isNaN(v) ? 50 : Math.min(200, Math.max(5, v)),
                );
              }}
              className="auth-input w-24"
              aria-describedby="crawl-max-urls-desc"
            />
            <span
              id="crawl-max-urls-desc"
              className="ml-2 text-sm text-[var(--muted)]"
            >
              {t("scanner.crawlMaxUrlsDesc")}
            </span>
          </div>
        </>
      )}
    </>
  );
}
