/**
 * Hook centralisant tous les états liés au crawl.
 * Remplace les 11+ useState individuels dans ScannerContent.
 */

import { useCallback, useState } from "react";
import type { CrawlUrlEntry } from "../services/crawlService";

export interface CrawlState {
  mode: "html" | "playwright" | "both";
  maxUrls: number;
  urls: CrawlUrlEntry[];
  identifiedCount: number;
  timeoutReached: boolean;
  timeoutHtml: boolean;
  timeoutPlaywright: boolean;
  antiBotSignatureDetected: boolean;
  antiBotLowUrlSuspected: boolean;
  requestsBlocked: boolean;
  requestsBlockedHtml: boolean;
  requestsBlockedPlaywright: boolean;
  maxConsecutive403: number;
  disallowPaths: string[];
}

const INITIAL_CRAWL_STATE: CrawlState = {
  mode: "html",
  maxUrls: 50,
  urls: [],
  identifiedCount: 0,
  timeoutReached: false,
  timeoutHtml: false,
  timeoutPlaywright: false,
  antiBotSignatureDetected: false,
  antiBotLowUrlSuspected: false,
  requestsBlocked: false,
  requestsBlockedHtml: false,
  requestsBlockedPlaywright: false,
  maxConsecutive403: 0,
  disallowPaths: [],
};

export function useCrawlState() {
  const [crawl, setCrawl] = useState<CrawlState>(INITIAL_CRAWL_STATE);

  const setCrawlMode = useCallback((mode: CrawlState["mode"]) => {
    setCrawl((prev) => ({ ...prev, mode }));
  }, []);

  const setCrawlMaxUrls = useCallback((maxUrls: number) => {
    setCrawl((prev) => ({ ...prev, maxUrls }));
  }, []);

  const setCrawlUrls = useCallback((urls: CrawlUrlEntry[]) => {
    setCrawl((prev) => ({ ...prev, urls, identifiedCount: urls.length }));
  }, []);

  const setCrawlResult = useCallback(
    (
      data: {
        urls: CrawlUrlEntry[];
        timeout_reached?: boolean;
        timeout_html?: boolean;
        timeout_playwright?: boolean;
        anti_bot_signature_detected?: boolean;
        anti_bot_low_url_suspected?: boolean;
        anti_bot_suspected?: boolean;
        requests_blocked?: boolean;
        requests_blocked_html?: boolean;
        requests_blocked_playwright?: boolean;
        max_consecutive_403?: number;
        disallow_paths?: string[];
      },
      mode: CrawlState["mode"],
    ) => {
      const signatureDetected = data.anti_bot_signature_detected ?? false;
      const lowUrlSuspected =
        data.anti_bot_low_url_suspected ??
        ((data.anti_bot_suspected ?? false) && !signatureDetected);
      setCrawl((prev) => ({
        ...prev,
        urls: data.urls,
        identifiedCount: data.urls.length,
        timeoutReached: data.timeout_reached ?? false,
        timeoutHtml:
          data.timeout_html ??
          ((data.timeout_reached ?? false) && mode === "html"),
        timeoutPlaywright:
          data.timeout_playwright ??
          ((data.timeout_reached ?? false) && mode === "playwright"),
        antiBotSignatureDetected: signatureDetected,
        antiBotLowUrlSuspected: lowUrlSuspected,
        requestsBlocked: data.requests_blocked ?? false,
        requestsBlockedHtml:
          data.requests_blocked_html ??
          ((data.requests_blocked ?? false) && mode === "html"),
        requestsBlockedPlaywright:
          data.requests_blocked_playwright ??
          ((data.requests_blocked ?? false) && mode === "playwright"),
        maxConsecutive403: data.max_consecutive_403 ?? 0,
        disallowPaths: data.disallow_paths ?? [],
      }));
    },
    [],
  );

  const resetCrawlState = useCallback(() => {
    setCrawl(INITIAL_CRAWL_STATE);
  }, []);

  return {
    crawl,
    setCrawlMode,
    setCrawlMaxUrls,
    setCrawlUrls,
    setCrawlResult,
    resetCrawlState,
  };
}
