/**
 * Logique de classification des steps et construction de la timeline.
 */

import type { ScanStepDisplay } from "../../services/scanService";

export const COLUMN_INDEX = { html: 0, common: 1, playwright: 2 } as const;

/** Mappe les noms de steps vers leurs clés i18n. */
export const STEP_I18N_KEYS: Record<string, string> = {
  // Synthetic frontend steps
  scan_init: "scanner.scanInit",
  scan_score_compute: "scanner.scanScoreCompute",
  crawl_init: "scanner.crawlInit",
  crawl_score_compute: "scanner.crawlScoreCompute",
  multi_scan_init: "scanner.multiScanInit",
  multi_scan_results_compute: "scanner.multiScanResultsCompute",
  // Crawl both-mode steps
  crawl_html_done: "scanner.crawlHtmlDone",
  crawl_playwright_done: "scanner.crawlPlaywrightDone",
  crawl_stopping_other: "scanner.crawlStoppingOther",
  crawl_stopping_other_done: "scanner.crawlStoppingOtherDone",
  crawl_merging: "scanner.crawlMerging",
  // Scan pipeline steps
  validation_url_check: "scanner.validationUrlCheck",
  validation_url_done: "scanner.validationUrlDone",
  ssrf_check: "scanner.ssrfCheck",
  ssrf_done: "scanner.ssrfDone",
  fetch_https_check: "scanner.fetchHttpsCheck",
  fetch_https_done: "scanner.fetchHttpsDone",
  tls_check: "scanner.tlsCheck",
  tls_done: "scanner.tlsDone",
  headers_check: "scanner.headersCheck",
  headers_done: "scanner.headersDone",
  cache_check: "scanner.cacheCheck",
  cache_done: "scanner.cacheDone",
  cookies_check: "scanner.cookiesCheck",
  cookies_done: "scanner.cookiesDone",
  exposed_files_check: "scanner.exposedFilesCheck",
  exposed_files_done: "scanner.exposedFilesDone",
  directory_listing_check: "scanner.directoryListingCheck",
  directory_listing_done: "scanner.directoryListingDone",
  robots_txt_check: "scanner.robotsTxtCheck",
  robots_txt_done: "scanner.robotsTxtDone",
  sitemap_check: "scanner.sitemapCheck",
  sitemap_done: "scanner.sitemapDone",
  tech_fingerprinting_check: "scanner.techFingerprintingCheck",
  tech_fingerprinting_done: "scanner.techFingerprintingDone",
  information_disclosure_check: "scanner.informationDisclosureCheck",
  information_disclosure_done: "scanner.informationDisclosureDone",
  integrity_check: "scanner.integrityCheck",
  integrity_done: "scanner.integrityDone",
  cors_cross_origin_check: "scanner.corsCheck",
  cors_cross_origin_done: "scanner.corsDone",
  // Crawl single-mode steps
  robots_check: "scanner.robotsCheck",
  robots_done: "scanner.robotsDone",
  crawl_progress: "scanner.crawlProgress",
  crawl_done: "scanner.crawlDone",
  // Crawl both-mode prefixed steps
  html_robots_check: "scanner.htmlRobotsCheck",
  html_robots_done: "scanner.htmlRobotsDone",
  html_sitemap_check: "scanner.htmlSitemapCheck",
  html_sitemap_done: "scanner.htmlSitemapDone",
  html_crawl_progress: "scanner.htmlCrawlProgress",
  playwright_robots_check: "scanner.playwrightRobotsCheck",
  playwright_robots_done: "scanner.playwrightRobotsDone",
  playwright_sitemap_check: "scanner.playwrightSitemapCheck",
  playwright_sitemap_done: "scanner.playwrightSitemapDone",
  playwright_crawl_progress: "scanner.playwrightCrawlProgress",
  // Multi-scan domain steps
  domain_tls_check: "scanner.domainTlsCheck",
  domain_robots_check: "scanner.domainRobotsCheck",
  domain_sitemap_check: "scanner.domainSitemapCheck",
  domain_exposed_files_check: "scanner.domainExposedFilesCheck",
  domain_directory_listing_check: "scanner.domainDirectoryListingCheck",
  domain_cors_check: "scanner.domainCorsCheck",
  domain_checks_done: "scanner.domainChecksDone",
  // Multi-scan page steps
  page_scan_started: "scanner.pageScanning",
  page_scan_done: "scanner.pageDone",
  page_scan_error: "scanner.pageError",
  multi_scan_done: "scanner.multiScanDone",
};

type TFn = (key: string, params?: Record<string, string | number>) => string;

/**
 * Résout le message d'affichage d'un step.
 * Priorité : clé i18n → message brut (fallback si clé absente).
 */
export function getDisplayMessage(step: ScanStepDisplay, t: TFn): string {
  const stepName = step.step;
  const isDone = step.done ?? false;

  const i18nKey =
    stepName === "crawl_stopping_other" && isDone
      ? STEP_I18N_KEYS["crawl_stopping_other_done"]
      : STEP_I18N_KEYS[stepName];

  if (!i18nKey) return step.message;

  const params: Record<string, string | number> = {};
  if (step.url_count !== undefined) params.count = step.url_count;
  if (step.url !== undefined) params.url = step.url;
  if (step.page_index !== undefined) params.index = step.page_index;
  if (step.total_pages !== undefined) params.total = step.total_pages;
  if (step.score !== undefined) params.score = step.score;

  return t(i18nKey, Object.keys(params).length > 0 ? params : undefined);
}

/**
 * Colonne du step pour le layout en Y (mode crawl both).
 * crawl_stopping_other → colonne du crawler arrêté (l'autre que celui qui a fini).
 */
export function getStepColumn(
  step: string,
  steps: ScanStepDisplay[],
  index: number,
): "html" | "common" | "playwright" {
  if (step.startsWith("html_")) return "html";
  if (step.startsWith("playwright_")) return "playwright";
  if (step === "crawl_html_done") return "html";
  if (step === "crawl_playwright_done") return "playwright";
  if (step === "crawl_stopping_other") {
    const prev = index > 0 ? steps[index - 1]?.step : "";
    return prev === "crawl_html_done" ? "playwright" : "html";
  }
  return "common";
}

export function isMultiScanStep(step: string): boolean {
  return (
    step.startsWith("domain_") ||
    step.startsWith("page_scan_") ||
    step === "multi_scan_done"
  );
}

export interface TimelineStep extends ScanStepDisplay {
  details?: string[];
  groupKey?: "domain" | "pages";
}

/**
 * Construit la timeline d'affichage à partir des steps bruts.
 * Injecte des steps synthétiques (init, score compute) et regroupe les steps
 * multi-scan en entrées collapsibles.
 */
export function buildTimelineSteps(
  rawSteps: ScanStepDisplay[],
  t: TFn,
): TimelineStep[] {
  const isMulti = rawSteps.some((s) => isMultiScanStep(s.step));
  if (!isMulti) {
    if (rawSteps.length === 0) return rawSteps;

    const hasCrawlSteps = rawSteps.some(
      (s) =>
        s.step === "crawl_done" ||
        s.step.startsWith("crawl_") ||
        s.step.startsWith("html_") ||
        s.step.startsWith("playwright_"),
    );

    if (hasCrawlSteps) {
      const timeline: TimelineStep[] = [
        { step: "crawl_init", message: "", done: true },
        ...rawSteps,
      ];
      if (rawSteps.some((s) => s.step === "crawl_done")) {
        timeline.push({ step: "crawl_score_compute", message: "", done: true });
      }
      return timeline;
    }

    const timeline: TimelineStep[] = [
      { step: "scan_init", message: "", done: true },
      ...rawSteps,
    ];
    if (
      rawSteps.some(
        (s) =>
          s.step === "cors_cross_origin_done" || s.step === "fake_scan_done",
      )
    ) {
      timeline.push({ step: "scan_score_compute", message: "", done: true });
    }
    return timeline;
  }

  const timeline: TimelineStep[] = [
    { step: "multi_scan_init", message: "", done: true },
  ];
  let domainIdx = -1;
  let pagesIdx = -1;
  let hasMultiScanDone = false;
  let donePages = 0;
  let errorPages = 0;
  const pageStates = new Map<string, "done" | "error">();
  let totalPagesCount: number | null = null;
  const seenDomainChecks: string[] = [];

  const ensureDomainStep = (): number => {
    if (domainIdx >= 0) return domainIdx;
    timeline.push({
      step: "domain_parallel_group",
      message: t("scanner.domainParallelGroup"),
      done: false,
      details: [],
      groupKey: "domain",
    });
    domainIdx = timeline.length - 1;
    return domainIdx;
  };

  const ensurePagesStep = (): number => {
    if (pagesIdx >= 0) return pagesIdx;
    timeline.push({
      step: "pages_parallel_group",
      message: t("scanner.pagesParallelGroup"),
      done: false,
      details: [],
      groupKey: "pages",
    });
    pagesIdx = timeline.length - 1;
    return pagesIdx;
  };

  for (const step of rawSteps) {
    if (step.step.startsWith("domain_")) {
      const idx = ensureDomainStep();
      if (step.step === "domain_checks_done") {
        const doneDetails = seenDomainChecks.map((k) => {
          const key = STEP_I18N_KEYS[k];
          return `✓ ${key ? t(key) : k}`;
        });
        timeline[idx] = {
          ...timeline[idx],
          done: true,
          message: t("scanner.domainChecksDone"),
          details: [...(timeline[idx].details ?? []), ...doneDetails],
        };
      } else if (
        step.step.endsWith("_check") &&
        !seenDomainChecks.includes(step.step)
      ) {
        seenDomainChecks.push(step.step);
        const key = STEP_I18N_KEYS[step.step];
        const detail = key ? t(key) : step.step;
        timeline[idx].details = [...(timeline[idx].details ?? []), detail];
      }
      continue;
    }

    if (step.step.startsWith("page_scan_")) {
      const idx = ensurePagesStep();

      if (step.step === "page_scan_started" && step.url) {
        const total = step.total_pages;
        if (total !== undefined && total > 0) {
          totalPagesCount =
            totalPagesCount == null ? total : Math.max(totalPagesCount, total);
        }
        const detail = t("scanner.pageScanning", {
          url: step.url,
          index: step.page_index ?? 0,
          total: totalPagesCount ?? 0,
        });
        timeline[idx].details = [...(timeline[idx].details ?? []), detail];
      } else if (step.step === "page_scan_done" && step.url) {
        const url = step.url;
        if (!pageStates.has(url)) {
          pageStates.set(url, "done");
          donePages += 1;
        }
        const detail = t("scanner.pageDone", { url });
        timeline[idx].details = [...(timeline[idx].details ?? []), detail];
      } else if (step.step === "page_scan_error" && step.url) {
        const url = step.url;
        if (!pageStates.has(url)) {
          pageStates.set(url, "error");
          errorPages += 1;
        }
        const detail = t("scanner.pageError", { url });
        timeline[idx].details = [...(timeline[idx].details ?? []), detail];
      }

      const total = totalPagesCount ?? donePages + errorPages;
      const done = donePages + errorPages;
      timeline[idx] = {
        ...timeline[idx],
        message:
          total > 0
            ? `${t("scanner.pagesParallelGroup")} (${done}/${total})`
            : t("scanner.pagesParallelGroup"),
      };
      continue;
    }

    if (step.step === "multi_scan_done") {
      hasMultiScanDone = true;
      if (pagesIdx >= 0) {
        const total = totalPagesCount ?? donePages + errorPages;
        const done = donePages + errorPages;
        timeline[pagesIdx] = {
          ...timeline[pagesIdx],
          done: true,
          message:
            total > 0
              ? `${t("scanner.pagesParallelGroup")} (${done}/${total})`
              : t("scanner.pagesParallelGroup"),
        };
      }
      timeline.push({ ...step, done: true });
      continue;
    }

    timeline.push(step);
  }

  if (hasMultiScanDone) {
    timeline.push({
      step: "multi_scan_results_compute",
      message: "",
      done: true,
    });
  }

  return timeline;
}
