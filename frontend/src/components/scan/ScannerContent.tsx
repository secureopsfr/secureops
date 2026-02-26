"use client";

import { useState, useCallback } from "react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import {
  runScan,
  type ScanResult,
  type ScanError,
} from "../../services/scanService";

type ScanState = "idle" | "loading" | "success" | "error";

export default function ScannerContent() {
  const { t } = useLanguage();
  const [url, setUrl] = useState("");
  const [state, setState] = useState<ScanState>("idle");
  const [steps, setSteps] = useState<
    { step: string; message: string; done?: boolean }[]
  >([]);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<ScanError | null>(null);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;
      setState("loading");
      setSteps([]);
      setResult(null);
      setError(null);

      runScan(trimmed, (ev) => {
        if (ev.type === "step") {
          setSteps((prev) => [
            ...prev,
            {
              step: ev.data.step,
              message: ev.data.message,
              done: ev.data.step.endsWith("_done"),
            },
          ]);
        } else if (ev.type === "result") {
          setResult(ev.data);
          setState("success");
        } else if (ev.type === "error") {
          setError(ev.data);
          setState("error");
        }
      });
    },
    [url],
  );

  const handleNewScan = useCallback(() => {
    setState("idle");
    setSteps([]);
    setResult(null);
    setError(null);
  }, []);

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <AnimateInView
        initialOnly
        delay={80}
        className="page-section landing-reveal-page"
        as="section"
        aria-label="Scanner header"
      >
        <div className="page-container">
          <div className="page-header text-center">
            <h1 className="page-title">{t("scanner.title")}</h1>
            <p className="page-subtitle mt-4">{t("scanner.subtitle")}</p>
          </div>
        </div>
      </AnimateInView>

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="section"
        aria-label="Scanner content"
      >
        <div className="scanner-content">
          {(state === "idle" || state === "error") && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="scan-url"
                  className="mb-2 block text-sm font-medium text-[var(--text)]"
                >
                  {t("scanner.urlLabel")}
                </label>
                <input
                  id="scan-url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder={t("scanner.urlPlaceholder")}
                  required
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] px-4 py-3 text-[var(--text)] placeholder:text-[var(--muted)] focus:border-[rgb(var(--primary))] focus:outline-none focus:ring-1 focus:ring-[rgb(var(--primary))]"
                />
              </div>
              <p className="text-xs text-[var(--muted)]">
                {t("scanner.disclaimer")}
              </p>
              <GenericButton
                type="submit"
                label={t("scanner.cta")}
                variant="primary"
                disabled={!url.trim()}
              />
            </form>
          )}

          {state === "loading" && steps.length > 0 && (
            <ScanLoader steps={steps} />
          )}

          {state === "success" && result && (
            <ScanResults result={result} onNewScan={handleNewScan} />
          )}

          {state === "error" && error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <h3 className="mb-2 font-semibold text-red-600 dark:text-red-400">
                {t("scanner.errorTitle")}
              </h3>
              <p className="text-sm text-[var(--text)]">{error.message}</p>
            </div>
          )}
        </div>
      </AnimateInView>
    </div>
  );
}
