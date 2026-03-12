"use client";

import { DropdownSelector } from "../buttons";
import { Checkbox } from "../inputs";
import type { CrawlState } from "../../hooks/useCrawlState";

interface ScanTypeSelectorProps {
  scanOnlyThisPage: boolean;
  onScanOnlyThisPageChange: (checked: boolean) => void;
  crawlMode: CrawlState["mode"];
  crawlMaxUrls: number;
  onCrawlModeChange: (mode: CrawlState["mode"]) => void;
  onCrawlMaxUrlsChange: (value: number) => void;
  t: (key: string) => string;
}

/**
 * Contrôles de mode scan : page unique ou crawl multi-pages.
 * Affiche les options crawl (mode + maxUrls) uniquement quand crawl activé.
 */
export default function ScanTypeSelector({
  scanOnlyThisPage,
  onScanOnlyThisPageChange,
  crawlMode,
  crawlMaxUrls,
  onCrawlModeChange,
  onCrawlMaxUrlsChange,
  t,
}: ScanTypeSelectorProps) {
  return (
    <>
      <Checkbox
        label={t("scanner.scanOnlyThisPage")}
        checked={scanOnlyThisPage}
        onChange={onScanOnlyThisPageChange}
      />
      {!scanOnlyThisPage && (
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
      )}
      {!scanOnlyThisPage && (
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
      )}
    </>
  );
}
