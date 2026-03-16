/**
 * Hook centralisant le flow scan/crawl complet.
 * Gère l'URL, la state machine et tous les callbacks de lancement/résultat.
 */

import { useState, useCallback, useEffect } from "react";
import { useStepQueue } from "./useStepQueue";
import { useCrawlState } from "./useCrawlState";
import {
  runAsyncScan,
  runMultiScan,
  type AsyncScanMode,
  type AsyncScanType,
  type ScanResult,
  type MultiScanResult,
  type ScanError,
} from "../services/scanService";
import { runCrawl } from "../services/crawlService";
import { normalizeScanUrl } from "../utils/scanUrl";
import {
  savePendingScanResult,
  consumePendingScanResult,
} from "../utils/scanStorage";
import {
  saveMultiScan,
  saveScan,
  type ScanHistorySelection,
} from "../services/scanHistoryService";
import { showErrorToast } from "../utils/toastNotifications";

export type ScanState =
  | "idle"
  | "crawling"
  | "validation"
  | "loading"
  | "success"
  | "error";

interface UseScanFlowProps {
  isAuthenticated: boolean;
  authLoading: boolean;
  getToken: (() => Promise<string | null>) | undefined;
  t: (key: string) => string;
}

export function useScanFlow({
  isAuthenticated,
  authLoading,
  getToken,
  t,
}: UseScanFlowProps) {
  const [url, setUrl] = useState("");
  const [scanTarget, setScanTarget] = useState<AsyncScanType>("frontend");
  const [scanMode, setScanMode] = useState<AsyncScanMode>("passive");
  const [scanOnlyThisPage, setScanOnlyThisPage] = useState(true);
  const [state, setState] = useState<ScanState>("idle");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [multiResult, setMultiResult] = useState<MultiScanResult | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [error, setError] = useState<ScanError | null>(null);
  const [errorModalOpen, setErrorModalOpen] = useState(false);

  const { steps, enqueueStep, resetSteps } = useStepQueue();
  const {
    steps: crawlSteps,
    enqueueStep: enqueueCrawlStep,
    resetSteps: resetCrawlSteps,
  } = useStepQueue();
  const {
    crawl,
    setCrawlMode,
    setCrawlMaxUrls,
    setCrawlUrls,
    setCrawlResult,
    resetCrawlState,
  } = useCrawlState();

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const pending = consumePendingScanResult();
      if (pending) {
        setResult(pending);
        setState("success");
        saveScan(pending, (pending.scan_type as AsyncScanType) ?? scanTarget)
          .then((id) => {
            if (id) setScanId(id);
          })
          .catch(() => showErrorToast(t("scanner.saveFailed")));
      }
    }
  }, [authLoading, isAuthenticated, t, scanTarget]);

  const runScanOnUrl = useCallback(
    (
      urlToScan: string,
      target: AsyncScanType = scanTarget,
      mode: AsyncScanMode = scanMode,
    ) => {
      setState("loading");
      resetSteps();
      setResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      runAsyncScan(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueStep(ev.data);
          } else if (ev.type === "result") {
            if (isAuthenticated) {
              setResult(ev.data);
              const effectiveScanType = ev.data.scan_type ?? target;
              saveScan(ev.data, effectiveScanType)
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
        {
          scanType: target,
          scanMode: mode,
          input: {},
          logPrefix: `[scan-${target}-${mode}-polling]`,
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
    [
      t,
      isAuthenticated,
      getToken,
      resetSteps,
      enqueueStep,
      scanTarget,
      scanMode,
    ],
  );

  const runMultiScanOnUrls = useCallback(
    (
      urlsToScan: string[],
      target: AsyncScanType = scanTarget,
      mode: AsyncScanMode = scanMode,
    ) => {
      setState("loading");
      resetSteps();
      setResult(null);
      setMultiResult(null);
      setScanId(null);
      setError(null);
      setErrorModalOpen(false);

      runMultiScan(
        urlsToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueStep(ev.data);
          } else if (ev.type === "result") {
            setMultiResult(ev.data);
            if (isAuthenticated) {
              saveMultiScan(ev.data)
                .then((id) => {
                  if (id) setScanId(id);
                })
                .catch(() => showErrorToast(t("scanner.saveFailed")));
            }
            setState("success");
          } else if (ev.type === "error") {
            setError(ev.data);
            setState("error");
            setErrorModalOpen(true);
          }
        },
        getToken ?? (async () => null),
        {
          scanType: target,
          scanMode: mode,
        },
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
    [
      isAuthenticated,
      t,
      getToken,
      resetSteps,
      enqueueStep,
      scanTarget,
      scanMode,
    ],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;
      const urlToScan = normalizeScanUrl(trimmed);
      setError(null);
      setErrorModalOpen(false);

      if (scanOnlyThisPage) {
        runScanOnUrl(urlToScan, scanTarget, scanMode);
        return;
      }

      if (scanTarget === "backend") {
        return;
      }

      setState("crawling");
      resetCrawlSteps();
      runCrawl(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            enqueueCrawlStep(ev.data);
          } else if (ev.type === "result") {
            const urls =
              ev.data.urls.length > 0
                ? ev.data.urls
                : [{ url: urlToScan, depth: 0 }];
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
        crawl.maxUrls,
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
      scanOnlyThisPage,
      scanTarget,
      scanMode,
      runScanOnUrl,
      t,
      enqueueCrawlStep,
      resetCrawlSteps,
      setCrawlResult,
      crawl,
    ],
  );

  const handleLaunchScanFromValidation = useCallback(() => {
    const urlStrings = crawl.urls.map((u) => u.url).filter(Boolean);
    if (urlStrings.length > 1) {
      runMultiScanOnUrls(urlStrings, scanTarget, scanMode);
    } else {
      runScanOnUrl(normalizeScanUrl(url.trim()), scanTarget, scanMode);
    }
  }, [url, crawl.urls, runScanOnUrl, runMultiScanOnUrls, scanTarget, scanMode]);

  const handleBackFromValidation = useCallback(() => {
    setState("idle");
    resetCrawlState();
  }, [resetCrawlState]);

  const handleSelectScan = useCallback((selection: ScanHistorySelection) => {
    setScanId(selection.scan_id ?? null);
    if (selection.result_mode === "multi") {
      setMultiResult(selection.result);
      setResult(null);
    } else {
      setResult(selection.result);
      setMultiResult(null);
    }
    setState("success");
  }, []);

  const handleNewScan = useCallback(() => {
    setState("idle");
    resetSteps();
    resetCrawlSteps();
    setResult(null);
    setMultiResult(null);
    setScanId(null);
    setError(null);
    resetCrawlState();
  }, [resetCrawlState, resetSteps, resetCrawlSteps]);

  return {
    url,
    setUrl,
    scanOnlyThisPage,
    setScanOnlyThisPage,
    state,
    setState,
    steps,
    crawlSteps,
    result,
    multiResult,
    scanId,
    error,
    errorModalOpen,
    setErrorModalOpen,
    crawl,
    setCrawlMode,
    setCrawlMaxUrls,
    setCrawlUrls,
    resetCrawlState,
    scanTarget,
    scanMode,
    setScanTarget,
    setScanMode,
    runScanOnUrl,
    runMultiScanOnUrls,
    handleSubmit,
    handleLaunchScanFromValidation,
    handleBackFromValidation,
    handleSelectScan,
    handleNewScan,
  };
}
