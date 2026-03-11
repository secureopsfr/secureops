"use client";

import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { fetchAuthSession } from "aws-amplify/auth";
import { AlertTriangle, Bot, FileText } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";
import { DropdownSelector, GenericButton } from "../buttons";
import Card from "../ui/cards/Card";
import Modal from "../ui/Modal";
import CrawlValidationStep from "./CrawlValidationStep";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import ScanResultsGate from "./ScanResultsGate";
import FakeScanResultsBlurred from "./FakeScanResultsBlurred";
import {
  runScan,
  type ScanResult,
  type ScanError,
  type ScanStepDisplay,
} from "../../services/scanService";
import { runCrawl, type CrawlUrlEntry } from "../../services/crawlService";
import { normalizeScanUrl } from "../../utils/scanUrl";
import {
  savePendingScanResult,
  consumePendingScanResult,
} from "../../utils/scanStorage";
import { saveScan } from "../../services/scanHistoryService";
import { showErrorToast } from "../../utils/toastNotifications";

type CrawlersState =
  | "idle"
  | "crawling"
  | "validation"
  | "loading"
  | "success"
  | "error";

export default function CrawlersContent() {
  const { t, lp } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuthUser({
    listenToAuthEvents: true,
  });
  const [url, setUrl] = useState("");
  const [state, setState] = useState<CrawlersState>("idle");
  const [steps, setSteps] = useState<ScanStepDisplay[]>([]);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [error, setError] = useState<ScanError | null>(null);
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [crawlMode, setCrawlMode] = useState<"html" | "playwright" | "both">(
    "html",
  );
  const [crawlMaxUrls, setCrawlMaxUrls] = useState(50);
  const [crawledUrls, setCrawledUrls] = useState<CrawlUrlEntry[]>([]);
  const [crawlTimeoutReached, setCrawlTimeoutReached] = useState(false);
  const [crawlAntiBotSuspected, setCrawlAntiBotSuspected] = useState(false);
  const [crawlRequestsBlocked, setCrawlRequestsBlocked] = useState(false);
  const [crawlDisallowPaths, setCrawlDisallowPaths] = useState<string[]>([]);
  const [crawlSteps, setCrawlSteps] = useState<ScanStepDisplay[]>([]);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const pending = consumePendingScanResult();
      if (pending) {
        setResult(pending);
        setState("success");
        saveScan(pending)
          .then((id) => {
            if (id) setScanId(id);
          })
          .catch(() => showErrorToast(t("scanner.saveFailed")));
      }
    }
  }, [authLoading, isAuthenticated, t]);

  const runScanOnUrl = useCallback(
    (urlToScan: string) => {
      setState("loading");
      setSteps([]);
      setResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      const getToken = isAuthenticated
        ? async () => {
            try {
              const session = await fetchAuthSession();
              return session.tokens?.accessToken?.toString() ?? null;
            } catch {
              return null;
            }
          }
        : undefined;

      runScan(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            const done = ev.data.step.endsWith("_done");
            setSteps((prev) => {
              if (done && prev.length > 0) {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: true,
                };
                return updated;
              }
              return [
                ...prev,
                {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: false,
                },
              ];
            });
          } else if (ev.type === "result") {
            if (isAuthenticated) {
              setResult(ev.data);
              saveScan(ev.data)
                .then((id) => {
                  if (id) setScanId(id);
                })
                .catch(() => showErrorToast(t("scanner.saveFailed")));
            } else {
              savePendingScanResult(ev.data);
              setResult(ev.data);
              setState("success");
            }
          } else if (ev.type === "save_done") {
            setScanId(ev.data.scan_id);
          } else if (ev.type === "error") {
            setError(ev.data);
            setState("error");
            setErrorModalOpen(true);
          } else if (ev.type === "save_failed") {
            showErrorToast(ev.data || t("scanner.saveFailed"));
          }
        },
        getToken,
      ).catch((err) => {
        setError({
          message:
            err instanceof Error ? err.message : t("scanner.errorGeneric"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [t, isAuthenticated],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;
      const urlToCrawl = normalizeScanUrl(trimmed);
      setError(null);
      setErrorModalOpen(false);

      setState("crawling");
      setCrawlSteps([]);
      runCrawl(
        urlToCrawl,
        (ev) => {
          if (ev.type === "step") {
            const step = ev.data.step;
            const done = step.endsWith("_done");
            const isCrawlMerging = step === "crawl_merging";
            const isCrawlStoppingOther = step === "crawl_stopping_other";
            const isCrawlProgress =
              step === "crawl_progress" ||
              step === "html_crawl_progress" ||
              step === "playwright_crawl_progress";
            setCrawlSteps((prev) => {
              if (isCrawlStoppingOther && prev.length > 0) {
                const lastDone = prev.findLastIndex((s) =>
                  ["crawl_html_done", "crawl_playwright_done"].includes(s.step),
                );
                const branchToReplace =
                  lastDone >= 0 && prev[lastDone]?.step === "crawl_html_done"
                    ? "playwright"
                    : "html";
                const targetStep =
                  branchToReplace === "playwright"
                    ? "playwright_crawl_progress"
                    : "html_crawl_progress";
                const idx = prev.findLastIndex((s) => s.step === targetStep);
                if (idx >= 0) {
                  const updated = [...prev];
                  updated[idx] = {
                    step: "crawl_stopping_other",
                    message: ev.data.message,
                    done: false,
                  };
                  return updated;
                }
              }
              if (isCrawlMerging && prev.length > 0) {
                const updated = [...prev];
                const stopIdx = updated.findLastIndex(
                  (s) => s.step === "crawl_stopping_other",
                );
                if (stopIdx >= 0) {
                  updated[stopIdx] = {
                    step: updated[stopIdx].step,
                    message: updated[stopIdx].message,
                    done: true,
                  };
                }
                return [
                  ...updated,
                  {
                    step: ev.data.step,
                    message: ev.data.message,
                    done: false,
                  },
                ];
              }
              if (done && prev.length > 0) {
                const updated = [...prev];
                const checkStep = step.replace("_done", "_check");
                const idx = updated.findLastIndex((s) => s.step === checkStep);
                if (idx >= 0) {
                  updated[idx] = {
                    step: updated[idx].step,
                    message: ev.data.message,
                    done: true,
                  };
                } else {
                  updated[updated.length - 1] = {
                    step: prev[prev.length - 1].step,
                    message: ev.data.message,
                    done: true,
                  };
                }
                return updated;
              }
              if (isCrawlProgress && prev.length > 0) {
                const lastIdx = prev.findLastIndex((s) => s.step === step);
                if (lastIdx >= 0) {
                  const updated = [...prev];
                  updated[lastIdx] = {
                    step: ev.data.step,
                    message: ev.data.message,
                    done: false,
                  };
                  return updated;
                }
              }
              return [
                ...prev,
                {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: false,
                },
              ];
            });
          } else if (ev.type === "result") {
            const urls =
              ev.data.urls.length > 0
                ? ev.data.urls
                : [{ url: urlToCrawl, type: "page", depth: 0 }];
            setCrawledUrls(urls);
            setCrawlTimeoutReached(ev.data.timeout_reached ?? false);
            setCrawlAntiBotSuspected(ev.data.anti_bot_suspected ?? false);
            setCrawlRequestsBlocked(ev.data.requests_blocked ?? false);
            setCrawlDisallowPaths(ev.data.disallow_paths ?? []);
          } else if (ev.type === "error") {
            setError({
              message: ev.data.message,
              status_code: ev.data.status_code,
              i18nKey: ev.data.i18nKey,
            });
            setState("error");
            setErrorModalOpen(true);
          }
        },
        crawlMaxUrls,
        crawlMode,
      ).catch((err) => {
        setError({
          message: err instanceof Error ? err.message : t("scanner.crawlError"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [url, crawlMaxUrls, crawlMode, t],
  );

  const handleLaunchScanFromValidation = useCallback(() => {
    runScanOnUrl(normalizeScanUrl(url.trim()));
  }, [url, runScanOnUrl]);

  const handleBackFromValidation = useCallback(() => {
    setState("idle");
    setCrawledUrls([]);
    setCrawlTimeoutReached(false);
    setCrawlAntiBotSuspected(false);
    setCrawlRequestsBlocked(false);
    setCrawlDisallowPaths([]);
    setCrawlSteps([]);
  }, []);

  const handleNewScan = useCallback(() => {
    setState("idle");
    setSteps([]);
    setResult(null);
    setScanId(null);
    setError(null);
    setCrawledUrls([]);
    setCrawlTimeoutReached(false);
    setCrawlAntiBotSuspected(false);
    setCrawlRequestsBlocked(false);
    setCrawlDisallowPaths([]);
  }, []);

  return (
    <div className="space-y-4 w-full">
      <div className="page-header text-center mb-6">
        <h1 className="page-title mb-2">{t("scanner.crawlers.title")}</h1>
        <p className="page-subtitle mt-0">{t("scanner.crawlers.subtitle")}</p>
        <Link
          href={lp("/scanner/docs/crawler")}
          className="group mt-2 inline-flex text-sm text-[rgb(var(--primary))] no-underline"
        >
          <span className="inline-flex items-center gap-1.5 border-b-2 border-transparent group-hover:border-[rgb(var(--primary))]">
            <FileText className="w-4 h-4" />
            {t("scanner.docsLink")}
          </span>
        </Link>
      </div>

      {(state === "idle" || state === "error") && (
        <Card disableHover>
          <div className="flex items-center gap-3 mb-4 -mt-2">
            <Bot className="w-6 h-6 text-[rgb(var(--primary))]" />
            <h2 className="section-title !text-left !mb-0">
              {t("scanner.crawlers.formTitle")}
            </h2>
          </div>
          <form
            onSubmit={handleSubmit}
            aria-label={t("scanner.ariaForm")}
            className="space-y-4"
          >
            <label
              htmlFor="crawl-url"
              className="block text-sm font-medium text-[var(--text)]"
            >
              {t("scheduledScans.urlLabel")}
            </label>
            <input
              id="crawl-url"
              type="text"
              inputMode="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={t("scheduledScans.urlPlaceholder")}
              required
              className="auth-input w-full"
            />
            <div>
              <label className="block text-sm font-medium text-[var(--text)] mb-2">
                {t("scanner.crawlModeLabel")}
              </label>
              <DropdownSelector
                selectedValue={crawlMode}
                onChange={(v) =>
                  setCrawlMode(v as "html" | "playwright" | "both")
                }
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
                  setCrawlMaxUrls(
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
            <GenericButton
              type="submit"
              label={t("scanner.crawlers.launchCrawl")}
              variant="primary"
              disabled={!url.trim()}
            />
          </form>
        </Card>
      )}

      {state === "crawling" &&
        (typeof document !== "undefined"
          ? createPortal(
              <div className="scan-loading-overlay fixed inset-0 z-[60]">
                <ScanLoader
                  steps={crawlSteps}
                  titleKey="scanner.crawlLoading"
                  crawlMode={crawlMode}
                  onAnimationComplete={
                    crawledUrls.length > 0
                      ? () => setState("validation")
                      : undefined
                  }
                />
              </div>,
              document.body,
            )
          : null)}

      {state === "validation" && (
        <CrawlValidationStep
          urls={crawledUrls}
          startUrl={url.trim()}
          timeoutReached={crawlTimeoutReached}
          antiBotSuspected={crawlAntiBotSuspected}
          requestsBlocked={crawlRequestsBlocked}
          disallowPaths={crawlDisallowPaths}
          onUrlsChange={setCrawledUrls}
          onLaunchScan={handleLaunchScanFromValidation}
          onBack={handleBackFromValidation}
        />
      )}

      {state === "loading" &&
        (typeof document !== "undefined"
          ? createPortal(
              <div className="scan-loading-overlay fixed inset-0 z-[60]">
                <ScanLoader
                  steps={steps}
                  crawlMode={crawlMode}
                  onAnimationComplete={
                    result ? () => setState("success") : undefined
                  }
                />
              </div>,
              document.body,
            )
          : null)}

      {state === "success" &&
        result &&
        !authLoading &&
        (isAuthenticated ? (
          <ScanResults
            result={result}
            scanId={scanId}
            onNewScan={handleNewScan}
          />
        ) : (
          <>
            <FakeScanResultsBlurred />
            <Modal
              isOpen
              onClose={() => {}}
              title={t("scanner.gateTitle")}
              maxWidth="420px"
              showCloseButton={false}
              closeOnBackdropClick={false}
            >
              <ScanResultsGate
                signInHref={`${lp("/connexion")}?returnTo=${encodeURIComponent(lp("/scanner/crawlers"))}`}
              />
            </Modal>
          </>
        ))}

      {state === "error" && error && (
        <Modal
          isOpen={errorModalOpen}
          onClose={() => setErrorModalOpen(false)}
          onExited={() => {
            setState("idle");
            setError(null);
          }}
          title={
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-6 h-6 text-[rgb(var(--danger))]" />
              <span>{t("scanner.errorTitle")}</span>
            </div>
          }
          maxWidth="500px"
        >
          <p className="text-[var(--text)] leading-relaxed">
            {error.i18nKey ? t(error.i18nKey) : error.message}
          </p>
        </Modal>
      )}
    </div>
  );
}
