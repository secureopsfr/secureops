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
  methodes_http_et_redirections_check: "scanner.methodesHttpCheck",
  methodes_http_et_redirections_done: "scanner.methodesHttpDone",
  api_checks_check: "scanner.apiChecksCheck",
  api_checks_done: "scanner.apiChecksDone",
  formats_check: "scanner.formatsCheck",
  formats_done: "scanner.formatsDone",
  api_page_check: "scanner.apiPageCheck",
  api_page_done: "scanner.apiPageDone",
  // Intrusive fake probe steps (legacy)
  intrusive_reflected_xss_check: "scanner.intrusiveReflectedXssCheck",
  intrusive_reflected_xss_done: "scanner.intrusiveReflectedXssDone",
  intrusive_sql_injection_check: "scanner.intrusiveSqlInjectionCheck",
  intrusive_sql_injection_done: "scanner.intrusiveSqlInjectionDone",
  intrusive_authz_bypass_check: "scanner.intrusiveAuthzBypassCheck",
  intrusive_authz_bypass_done: "scanner.intrusiveAuthzBypassDone",
  // Intrusive Phase A — P0
  open_redirect_check: "scanner.openRedirectCheck",
  open_redirect_done: "scanner.openRedirectDone",
  methodes_http_check: "scanner.intrusiveMethodesHttpCheck",
  methodes_http_done: "scanner.intrusiveMethodesHttpDone",
  cors_actif_check: "scanner.corsActifCheck",
  cors_actif_done: "scanner.corsActifDone",
  parametres_reflechis_check: "scanner.parametresReflechisCheck",
  parametres_reflechis_done: "scanner.parametresReflechisDone",
  sqli_check: "scanner.sqliCheck",
  sqli_done: "scanner.sqliDone",
  path_traversal_check: "scanner.pathTraversalCheck",
  path_traversal_done: "scanner.pathTraversalDone",
  csrf_check: "scanner.csrfCheck",
  csrf_done: "scanner.csrfDone",
  idor_check: "scanner.idorCheck",
  idor_done: "scanner.idorDone",
  command_injection_check: "scanner.commandInjectionCheck",
  command_injection_done: "scanner.commandInjectionDone",
  nosqli_check: "scanner.nosqliCheck",
  nosqli_done: "scanner.nosqliDone",
  dos_p0_check: "scanner.dosP0Check",
  dos_p0_done: "scanner.dosP0Done",
  // Intrusive Phase B — P0 suite + P1
  auth_bruteforce_check: "scanner.authBruteforceCheck",
  auth_bruteforce_done: "scanner.authBruteforceDone",
  session_fixation_check: "scanner.sessionFixationCheck",
  session_fixation_done: "scanner.sessionFixationDone",
  upload_abuse_check: "scanner.uploadAbuseCheck",
  upload_abuse_done: "scanner.uploadAbuseDone",
  idor_complet_check: "scanner.idorCompletCheck",
  idor_complet_done: "scanner.idorCompletDone",
  mass_assignment_check: "scanner.massAssignmentCheck",
  mass_assignment_done: "scanner.massAssignmentDone",
  graphql_abuse_check: "scanner.graphqlAbuseCheck",
  graphql_abuse_done: "scanner.graphqlAbuseDone",
  api_schema_abuse_check: "scanner.apiSchemaAbuseCheck",
  api_schema_abuse_done: "scanner.apiSchemaAbuseDone",
  ssrf_intrusive_check: "scanner.ssrfIntrusiveCheck",
  ssrf_intrusive_done: "scanner.ssrfIntrusiveDone",
  xxe_check: "scanner.xxeCheck",
  xxe_done: "scanner.xxeDone",
  ssti_check: "scanner.sstiCheck",
  ssti_done: "scanner.sstiDone",
  insecure_deserialization_check: "scanner.insecureDeserializationCheck",
  insecure_deserialization_done: "scanner.insecureDeserializationDone",
  lfi_rfi_check: "scanner.lfiRfiCheck",
  lfi_rfi_done: "scanner.lfiRfiDone",
  // Intrusive Phase C — P2 + P3
  host_header_check: "scanner.hostHeaderCheck",
  host_header_done: "scanner.hostHeaderDone",
  cache_poisoning_check: "scanner.cachePoisoningCheck",
  cache_poisoning_done: "scanner.cachePoisoningDone",
  request_smuggling_check: "scanner.requestSmugglingCheck",
  request_smuggling_done: "scanner.requestSmugglingDone",
  race_conditions_check: "scanner.raceConditionsCheck",
  race_conditions_done: "scanner.raceConditionsDone",
  business_logic_check: "scanner.businessLogicCheck",
  business_logic_done: "scanner.businessLogicDone",
  websocket_authz_check: "scanner.websocketAuthzCheck",
  websocket_authz_done: "scanner.websocketAuthzDone",
  oauth_oidc_check: "scanner.oauthOidcCheck",
  oauth_oidc_done: "scanner.oauthOidcDone",
  object_storage_check: "scanner.objectStorageCheck",
  object_storage_done: "scanner.objectStorageDone",
  service_mesh_check: "scanner.serviceMeshCheck",
  service_mesh_done: "scanner.serviceMeshDone",
  graphql_subscriptions_check: "scanner.graphqlSubscriptionsCheck",
  graphql_subscriptions_done: "scanner.graphqlSubscriptionsDone",
  grpc_abuse_check: "scanner.grpcAbuseCheck",
  grpc_abuse_done: "scanner.grpcAbuseDone",
  // Custom fake probe steps
  custom_strategy_check: "scanner.customStrategyCheck",
  custom_strategy_done: "scanner.customStrategyDone",
  custom_guardrails_check: "scanner.customGuardrailsCheck",
  custom_guardrails_done: "scanner.customGuardrailsDone",
  // Destructive fake probe steps
  destructive_prechecks_check: "scanner.destructivePrechecksCheck",
  destructive_prechecks_done: "scanner.destructivePrechecksDone",
  destructive_safety_check: "scanner.destructiveSafetyCheck",
  destructive_safety_done: "scanner.destructiveSafetyDone",
  // Legacy custom/destructive fake plan steps
  custom_plan_check: "scanner.customPlanCheck",
  custom_plan_done: "scanner.customPlanDone",
  custom_multi_plan_check: "scanner.customMultiPlanCheck",
  custom_multi_plan_done: "scanner.customMultiPlanDone",
  destructive_plan_check: "scanner.destructivePlanCheck",
  destructive_plan_done: "scanner.destructivePlanDone",
  destructive_multi_plan_check: "scanner.destructiveMultiPlanCheck",
  destructive_multi_plan_done: "scanner.destructiveMultiPlanDone",
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
          s.step === "cors_cross_origin_done" ||
          s.step === "methodes_http_et_redirections_done" ||
          s.step === "api_page_done" ||
          s.step === "formats_done" ||
          s.step === "api_checks_done" ||
          s.step === "intrusive_authz_bypass_done" ||
          s.step === "custom_guardrails_done" ||
          s.step === "destructive_safety_done" ||
          s.step === "custom_plan_done" ||
          s.step === "destructive_plan_done" ||
          s.step === "fake_scan_done" ||
          // Intrusive Phase C terminal steps
          s.step === "grpc_abuse_done" ||
          s.step === "graphql_subscriptions_done" ||
          s.step === "service_mesh_done" ||
          s.step === "object_storage_done" ||
          s.step === "oauth_oidc_done" ||
          s.step === "websocket_authz_done" ||
          s.step === "business_logic_done" ||
          s.step === "race_conditions_done" ||
          s.step === "request_smuggling_done" ||
          s.step === "cache_poisoning_done" ||
          s.step === "host_header_done",
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
