"use client";

import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { AlertTriangle, Bot, FileText } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";
import { useCrawlState } from "../../hooks/useCrawlState";
import { useStepQueue } from "../../hooks/useStepQueue";
import { useAuthToken } from "../../hooks/useAuthToken";
import AnimateInView from "../AnimateInView";
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
} from "../../services/scanService";
import { runCrawl } from "../../services/crawlService";
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
  const getToken = useAuthToken(isAuthenticated);
  const {
    crawl,
    setCrawlMode,
    setCrawlMaxUrls,
    setCrawlUrls,
    setCrawlResult,
    resetCrawlState,
  } = useCrawlState();
  const { steps, enqueueStep, resetSteps } = useStepQueue();
  const {
    steps: crawlSteps,
    enqueueStep: enqueueCrawlStep,
    resetSteps: resetCrawlSteps,
  } = useStepQueue();

  const [url, setUrl] = useState("");
  const [maxUrlsInput, setMaxUrlsInput] = useState("50");
  const [state, setState] = useState<CrawlersState>("idle");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [error, setError] = useState<ScanError | null>(null);
  const [errorModalOpen, setErrorModalOpen] = useState(false);

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
      resetSteps();
      setResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      runScan(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueStep(ev.data);
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
    [t, isAuthenticated, getToken, resetSteps, enqueueStep],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;

      const parsedMaxUrls = parseInt(maxUrlsInput, 10);
      const effectiveMaxUrls = Number.isNaN(parsedMaxUrls)
        ? 5
        : Math.min(200, Math.max(5, parsedMaxUrls));
      setMaxUrlsInput(String(effectiveMaxUrls));
      setCrawlMaxUrls(effectiveMaxUrls);

      const urlToCrawl = normalizeScanUrl(trimmed);
      setError(null);
      setErrorModalOpen(false);
      setState("crawling");
      resetCrawlSteps();

      runCrawl(
        urlToCrawl,
        (ev) => {
          if (ev.type === "step") {
            enqueueCrawlStep(ev.data);
          } else if (ev.type === "result") {
            const urls =
              ev.data.urls.length > 0
                ? ev.data.urls
                : [{ url: urlToCrawl, depth: 0 }];
            setCrawlResult({ ...ev.data, urls }, crawl.mode);
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
        effectiveMaxUrls,
        crawl.mode,
      ).catch((err) => {
        setError({
          message: err instanceof Error ? err.message : t("scanner.crawlError"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [
      url,
      maxUrlsInput,
      crawl.mode,
      t,
      enqueueCrawlStep,
      resetCrawlSteps,
      setCrawlMaxUrls,
      setCrawlResult,
    ],
  );

  const handleLaunchScanFromValidation = useCallback(() => {
    runScanOnUrl(normalizeScanUrl(url.trim()));
  }, [url, runScanOnUrl]);

  const handleReset = useCallback(() => {
    setState("idle");
    resetSteps();
    resetCrawlSteps();
    setResult(null);
    setScanId(null);
    setError(null);
    resetCrawlState();
  }, [resetCrawlState, resetSteps, resetCrawlSteps]);

  const showHeader = state === "idle" || state === "error";

  return (
    <div className="space-y-4 w-full">
      {showHeader && (
        <AnimateInView
          initialOnly
          delay={80}
          className="page-section landing-reveal-page"
          as="section"
          aria-label={t("scanner.ariaHeader")}
        >
          <div className="page-container">
            <div className="page-header text-center mb-4">
              <h1 className="page-title mb-2">{t("scanner.crawlers.title")}</h1>
              <p className="page-subtitle mt-0">
                {t("scanner.crawlers.subtitle")}
              </p>
              <Link
                href={lp("/scanner/docs/crawler")}
                target="_blank"
                rel="noopener noreferrer"
                className="group mt-2 inline-flex text-sm text-[rgb(var(--primary))] no-underline"
              >
                <span className="inline-flex items-center gap-1.5 border-b-2 border-transparent group-hover:border-[rgb(var(--primary))]">
                  <FileText className="w-4 h-4" />
                  {t("scanner.docsLink")}
                </span>
              </Link>
            </div>
          </div>
        </AnimateInView>
      )}

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="section"
        aria-label="Scanner content"
      >
        <div className="scanner-content">
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
                    selectedValue={crawl.mode}
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
                    value={maxUrlsInput}
                    onChange={(e) => {
                      const next = e.target.value;
                      setMaxUrlsInput(next);
                      if (next.trim() === "") return;
                      const v = parseInt(next, 10);
                      if (Number.isNaN(v)) return;
                      setCrawlMaxUrls(Math.min(200, Math.max(5, v)));
                    }}
                    onBlur={() => {
                      const v = parseInt(maxUrlsInput, 10);
                      const normalized = Number.isNaN(v)
                        ? 5
                        : Math.min(200, Math.max(5, v));
                      setMaxUrlsInput(String(normalized));
                      setCrawlMaxUrls(normalized);
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
                      crawlMode={crawl.mode}
                      onAnimationComplete={
                        crawl.urls.length > 0
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
              urls={crawl.urls}
              identifiedCount={crawl.identifiedCount}
              startUrl={url.trim()}
              timeoutReached={crawl.timeoutReached}
              timeoutHtml={crawl.timeoutHtml}
              timeoutPlaywright={crawl.timeoutPlaywright}
              antiBotSignatureDetected={crawl.antiBotSignatureDetected}
              antiBotLowUrlSuspected={crawl.antiBotLowUrlSuspected}
              requestsBlocked={crawl.requestsBlocked}
              requestsBlockedHtml={crawl.requestsBlockedHtml}
              requestsBlockedPlaywright={crawl.requestsBlockedPlaywright}
              maxConsecutive403={crawl.maxConsecutive403}
              disallowPaths={crawl.disallowPaths}
              allowManualAdd={false}
              allowLaunchScan={false}
              allowUrlRemoval={false}
              onUrlsChange={setCrawlUrls}
              onLaunchScan={handleLaunchScanFromValidation}
              onBack={handleReset}
            />
          )}

          {state === "loading" &&
            (typeof document !== "undefined"
              ? createPortal(
                  <div className="scan-loading-overlay fixed inset-0 z-[60]">
                    <ScanLoader
                      steps={steps}
                      crawlMode={crawl.mode}
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
                onNewScan={handleReset}
              />
            ) : (
              <>
                <FakeScanResultsBlurred result={result} />
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
      </AnimateInView>
    </div>
  );
}
